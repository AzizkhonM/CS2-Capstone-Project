from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import numpy as np
import pickle
from rapidfuzz import process, fuzz
from itertools import combinations
from sklearn.preprocessing import StandardScaler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Load model, features, Elo, and historical data snapshot base
# ============================================================
with open('models/logreg_model.pkl', 'rb') as f:
    logreg = pickle.load(f)
with open('models/feature_list.pkl', 'rb') as f:
    final_features = pickle.load(f)

elo_ratings = pd.read_csv('models/elo_ratings.csv').set_index('team_name')['elo_rating'].to_dict()
all_teams = sorted(elo_ratings.keys())

REFRAME_BASES = [
    'past3', 'head2head_percentage', 'head2head_freq',
    'mirage', 'inferno', 'nuke', 'dust2', 'overpass',
    'train', 'ancient', 'vertigo', 'anubis'
]
COUNT_BASES = [
    'wins', 'losses', 'totalwinrate', 'totallossrate',
    'online_winrate', 'lan_winrate', 'overall_winrate'
]

DEFAULT_ELO = 1500

# team_snapshots va scaler — server ishga tushganda BIR MARTA tayyorlanadi
# (matches_with_elo.csv models/ ichida yo'q bo'lsa, snapshotni oldindan
#  hisoblab, alohida fayl sifatida saqlash tavsiya etiladi — pastga qarang)
with open('models/team_snapshots.pkl', 'rb') as f:
    team_snapshots = pickle.load(f)
with open('models/scaler.pkl', 'rb') as f:
    scaler = pickle.load(f)


# ============================================================
# Core ML functions (from 06_demo.ipynb)
# ============================================================
def resolve_team_name(input_name, known_teams, threshold=80):
    match, score, _ = process.extractOne(input_name, known_teams, scorer=fuzz.WRatio)
    if score >= threshold:
        return match, score
    return None, score


def resolve_teams(team_names, known_teams):
    resolved = {}
    for name in team_names:
        match, score = resolve_team_name(name, known_teams)
        resolved[name] = match
    return resolved


def build_pair_features(team_a, team_b, event_type='lan'):
    snap_a = team_snapshots.get(team_a)
    snap_b = team_snapshots.get(team_b)

    row = {}
    elo_a = elo_ratings.get(team_a, DEFAULT_ELO)
    elo_b = elo_ratings.get(team_b, DEFAULT_ELO)
    row['elo_diff'] = elo_a - elo_b

    for base in REFRAME_BASES + COUNT_BASES:
        if base == 'totallossrate':
            continue
        if snap_a is None and snap_b is None:
            val_a, val_b = 0, 0
        elif snap_a is None:
            val_a = snap_b[base]
            val_b = snap_b[base]
        elif snap_b is None:
            val_a = snap_a[base]
            val_b = snap_a[base]
        else:
            val_a = snap_a[base]
            val_b = snap_b[base]
        row[f'{base}_diff'] = val_a - val_b

    row['event_type_lan'] = 1 if event_type == 'lan' else 0
    return pd.DataFrame([row])[final_features]


def predict_win_prob(team_a, team_b, event_type='lan'):
    X_ab = build_pair_features(team_a, team_b, event_type)
    X_ab_scaled = pd.DataFrame(scaler.transform(X_ab), columns=final_features)
    p_ab = logreg.predict_proba(X_ab_scaled)[0][1]

    X_ba = build_pair_features(team_b, team_a, event_type)
    X_ba_scaled = pd.DataFrame(scaler.transform(X_ba), columns=final_features)
    p_ba = logreg.predict_proba(X_ba_scaled)[0][1]

    return (p_ab + (1 - p_ba)) / 2


def compute_power_scores(team_names, resolved_names, event_type='lan'):
    scores = {t: [] for t in team_names}
    pairwise = {}

    for a, b in combinations(team_names, 2):
        ra = resolved_names[a] or a
        rb = resolved_names[b] or b
        p_ab = predict_win_prob(ra, rb, event_type)
        pairwise[(a, b)] = p_ab
        scores[a].append(p_ab)
        scores[b].append(1 - p_ab)

    power_scores = {t: float(np.mean(v)) for t, v in scores.items()}
    return power_scores, pairwise


def generate_seeding(team_names, event_type='lan'):
    resolved_names = resolve_teams(team_names, all_teams)
    power_scores, pairwise = compute_power_scores(team_names, resolved_names, event_type)
    ranked = sorted(power_scores.items(), key=lambda x: x[1], reverse=True)
    return ranked, pairwise, resolved_names


def generate_seed_order(n):
    """
    Returns the correct slot order for a single-elimination bracket
    of size n (must be a power of 2), such that seed 1 and seed 2
    can only meet in the final, seeds 1-4 only meet in semis, etc.
    """
    seeds = [1, 2]
    while len(seeds) < n:
        p = len(seeds) * 2
        new_seeds = []
        for s in seeds:
            new_seeds.append(s)
            new_seeds.append(p + 1 - s)
        seeds = new_seeds
    return seeds


# ============================================================
# Bracket builder — clear, self-describing bye handling
# ============================================================
def build_bracket(ranked_teams):
    n = len(ranked_teams)
    next_pow2 = 1
    while next_pow2 < n:
        next_pow2 *= 2

    seed_order = generate_seed_order(next_pow2)  # ← YANGI

    # Har bir "seed raqami" ga mos jamoa nomini beriladi (yo'q bo'lsa None = BYE)
    seeded_by_position = [None] * next_pow2
    for idx, seed_num in enumerate(seed_order):
        if seed_num <= n:
            seeded_by_position[idx] = ranked_teams[seed_num - 1][0]

    round1 = []
    for i in range(next_pow2 // 2):
        team_a = seeded_by_position[i * 2]
        team_b = seeded_by_position[i * 2 + 1]
        is_bye = team_a is None or team_b is None
        round1.append({
            "match_number": i + 1,
            "team_a": team_a,
            "team_b": team_b,
            "is_bye": is_bye,
            "winner": (team_a or team_b) if is_bye else None,
        })

    rounds = [{"round": 1, "round_name": get_round_name(next_pow2, 1), "matches": round1}]

    # Keyingi raundlar — skelet, g'oliblar hali noma'lum (BYE'dan tashqari)
    current_size = next_pow2 // 2
    round_num = 2
    prev_round = round1
    while current_size >= 1:
        matches = []
        for i in range(current_size // 2 if current_size > 1 else 1):
            m1 = prev_round[i * 2]
            m2 = prev_round[i * 2 + 1]
            # Agar oldingi matchda BYE bo'lsa, g'olib allaqachon ma'lum
            team_a = m1["winner"] if m1["winner"] else f"Winner of Match {m1['match_number']}"
            team_b = m2["winner"] if m2["winner"] else f"Winner of Match {m2['match_number']}"
            matches.append({
                "match_number": len(round1) + len(matches) + 1,  # global raqamlash (soddalashtirish uchun)
                "team_a": team_a,
                "team_b": team_b,
                "is_bye": False,
                "winner": None,
                "source_matches": [m1["match_number"], m2["match_number"]],
            })
        if not matches:
            break
        rounds.append({"round": round_num, "round_name": get_round_name(next_pow2, round_num), "matches": matches})
        prev_round = matches
        current_size //= 2
        round_num += 1
        if current_size <= 1:
            break

    return rounds


def get_round_name(bracket_size, round_num):
    total_rounds = bracket_size.bit_length() - 1
    remaining = total_rounds - round_num + 1
    names = {1: "Final", 2: "Semifinal", 3: "Quarterfinal"}
    return names.get(remaining, f"Round {round_num}")


# ============================================================
# API endpoints
# ============================================================
class SeedRequest(BaseModel):
    teams: list[str]
    tournament_type: str = "lan"


@app.get("/")
def health():
    return {"status": "running"}


@app.get("/teams")
def get_teams():
    return {"teams": all_teams}


@app.post("/predict")
def predict(req: SeedRequest):
    if len(set(req.teams)) != len(req.teams):
        return {"error": "Duplicate teams are not allowed."}
    if len(req.teams) < 2:
        return {"error": "At least 2 teams are required."}

    ranked, pairwise, resolved_names = generate_seeding(req.teams, req.tournament_type)
    bracket = build_bracket(ranked)

    return {
        "resolved_names": resolved_names,
        "seeding": [
            {"seed": i + 1, "team": team, "power_score": round(score, 3)}
            for i, (team, score) in enumerate(ranked)
        ],
        "bracket": bracket,
    }