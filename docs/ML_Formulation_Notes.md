# CS2 Power Seeding — Model Purpose and Methodology (Draft)

> This is **not** a final document — it is a **draft** to be filled in later based on the official template.

---

## 1. Model type

**Supervised Learning — Binary Classification**

- Features (X) and a target (y) exist, just like in a churn-prediction model
- Target: `winner` (team1 / team2)

---

## 2. Core ML problem (single, central task)

> **Given two CS2 teams, predict which one is more likely to win**

```
INPUT:  Team A, Team B (features of both)
OUTPUT: Team A's win probability (e.g. 0.68)
```

This is the model's **only learned task**. Everything else is just a different application of this one function.

---

## 3. Two use cases for one model

| # | Use case | Description |
|---|---|---|
| 1 | **Match prediction** | Called directly for a single specific pairing: "A vs B — who wins?" |
| 2 | **Seeding** (main practical benefit) | The model is run for all possible pairs among N teams (C(N,2)) → results are aggregated (Bradley-Terry method) → an overall Power Score → seed order → paired according to the standard bracket rule (`seed_i vs seed(N+1-i)`) |

**Important:** Seeding itself is not ML — it's a **post-processing** stage (combinatorics + sorting) that processes the model's output.

---

## 4. Elo — part of the model, not a separate model

- Elo is a classic mathematical rating algorithm (not trained), not ML
- We calculate it ourselves, using only the following columns: `date`, `team1_name`, `team2_name`, `winner` (in chronological order, updated sequentially)
- The calculated Elo score (and `elo_diff`) is then **fed into the ML classifier as a feature** — Elo is not standalone, it's an input signal that strengthens the model

---

## 5. Preliminary feature list (X)

### We calculate ourselves:
- `elo_diff` — the Elo score difference between the two teams (overall)
- `elo_diff_lan` / `elo_diff_online` — context-dependent Elo difference (optional)

### Already available in the dataset, confirmed dynamic (used directly):
- `winner_past3` / `loser_past3` — form over the last 3 games
- `winner_head2head_percentage`, `winner_head2head_freq` — head-to-head history
- per-map win rate (`winner_mirage`, `winner_inferno`, ...)
- `team1/2_online_winrate`, `team1/2_lan_winrate`, `team1/2_overall_winrate`
- `team1/2_wins`, `losses`, `totalwinrate`, `totallossrate`
- `event_type` (LAN/Online, normalized)

### Not used (confirmed STATIC):
- `avg_RATING`, `avg_DPR`, `avg_KAST`, `avg_ADR`, `avg_KPR` (at both team and player level)
- `rating_std`, `top_player`, `weakest_player`

## Target (y):
- `winner` (team1 / team2 → encoded as 0/1)

---

## 6. Baseline vs Main model

| | Baseline | Main model |
|---|---|---|
| What | Elo only (or a 50/50 guess) | Supervised classifier (Logistic Regression / XGBoost) |
| Purpose | Reference point — "how accurate we'd be if we learned nothing" | A genuinely trained, evaluable model |
| Input | Only elo_diff | All features (section 5) |

---

## 7. Evaluation — why it matters

- The model is tested on **test/held-out data** (matches not seen during training)
- Metrics: **Accuracy, AUC, F1** (the exact choice to be justified later)
- This is the part that is **provable**, distinguishing the model from "just a calculation": "the model correctly predicted 720 out of 1000 test matches"
- Seeding itself cannot be verified this way (no ground truth) — so evaluation is carried out **at the level of the core model (match prediction)**

---

## 8. Data splitting — important note

- A **temporal split** is used, not a random one
- Reason: in real life we predict the future, not the past — a random split would create data leakage

---

## 9. Open questions (to be determined later)

- [ ] The exact evaluation metric and the reasoning for it
- [ ] The initial Elo value and the K-coefficient
- [ ] How to incorporate margin of victory into the Elo/model
- [ ] The fuzzy matching library and threshold
- [ ] The "bye" system for N ≠ 2^n cases
- [ ] The exact formula for Bradley-Terry aggregation
