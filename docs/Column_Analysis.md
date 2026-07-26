# CS2 Tournament "Fair Seeding" Model — Full Technical Document

**Project:** Automated seeding system to be integrated into the CS2 Tournament Manager website
**Dataset file:** `cs2_newestcombinedmatches.csv`
**Document status:** Dataset analysis complete, model-building phase expected to begin

---

## 1. Project goal

### 1.1 The problem

Tournament organizers currently place teams into the bracket (seeding) based on:
- Subjective judgment ("by eye")
- Team popularity
- Old, outdated rankings

This leads to two problems:

1. **Unfair bracket** — two strong teams may meet in the first round, while a weak team can coast all the way to the final.
2. **Complaints/disputes** — when a team objects "why did I get a low seed?", the organizer has no numbers-based answer.

### 1.2 The solution — the model's exact task

**Input:** N team names (4, 8, 16, or any number) + tournament type (LAN/Online)

**Output:** A complete bracket — who plays whom, in which round, and why they were placed that way (with explanation)

**Workflow:**
```
1. The organizer enters N team names
2. The model matches each team name to historical records in the dataset (fuzzy matching)
3. A "current strength score" (Elo) is calculated for each team
4. Teams are sorted by rating (1-seed = strongest)
5. Teams are paired according to standard sports bracket rules
   (1 vs 8, 4 vs 5, 3 vs 6, 2 vs 7 — for 8 teams)
6. An explanation of "why this position" is generated for each seed
```

### 1.3 Why this isn't "trivial"

- Ordinary Elo/ranking systems only say "who is stronger," they don't explain **why**
- Our system will be explainable — if a team objects, we can respond with numbers
- It adapts to tournament context (LAN/Online) — not a single universal score

---

## 2. Dataset — overview

| Metric | Value |
|---|---|
| File name | `cs2_newestcombinedmatches.csv` |
| Number of rows | 7,033 (each one — a single match) |
| Number of columns | 140 |
| Date range | 2024-05-15 — 2025-10-16 |
| Number of unique teams | 331 |
| Number of unique tournaments | 648 |
| Match type | Mostly `bo3` (but partly mislabeled — see section 5.1) |
| Data source | HLTV.org (scraped, `scraped_date`: 2025-10-31) |

---

## 3. All 140 columns — full description

The columns are divided into 11 logical groups. For each: name, description, and **STATIC/DYNAMIC** status (see section 4).

### 3.1 Group: Match metadata (16 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 1 | `match_id` | Internal unique match ID | Meta |
| 2 | `hltv_match_id` | Official match ID on HLTV.org | Meta |
| 3 | `date` | Match date and time (ISO format, UTC) | **DYNAMIC — primary** |
| 4 | `tournament` | Tournament name | Meta |
| 5 | `winner` | Winning team (`team1`/`team2`) | **DYNAMIC — primary (target)** |
| 6 | `season` | Season number (1–8) | Meta |
| 7 | `score_team1` | Team1 score (map count or sometimes round count — see 5.1) | **DYNAMIC — primary** |
| 8 | `score_team2` | Team2 score | **DYNAMIC — primary** |
| 9 | `winner_map` | Name of the map the winner won on | Dynamic, but empty in 1010 rows |
| 10 | `loser_map` | Name of the map the loser lost on | Dynamic, but empty in 1010 rows |
| 11 | `decider_map` | Name of the deciding (3rd) map | Dynamic, empty in 63 rows |
| 36 | `match_type` | Declared format (`bo3`) — **mislabeled in 1010 rows** | ⚠️ Requires fixing |
| 37 | `event_type` | `LAN`/`Online`/`lan`/`online` — case mismatch | ⚠️ Needs normalization |
| 38 | `scraped_date` | When the data was collected | Meta |
| 39 | `hltv_url` | Link to the match page | Meta |
| 40 | `match_number` | **100% empty** — completely useless | ❌ To be removed |

### 3.2 Group: Head-to-head and form (6 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 12 | `winner_head2head_freq` | Number of prior wins by the winning team against this opponent (before this match) | ✅ **DYNAMIC** (confirmed) |
| 13 | `loser_head2head_freq` | Number of prior wins by the losing team against this opponent | ✅ **DYNAMIC** |
| 14 | `winner_head2head_percentage` | The winner's win percentage in the historical head-to-head between the two teams | ✅ **DYNAMIC** |
| 15 | `loser_head2head_percentage` | Same, for the losing side | ✅ **DYNAMIC** |
| 16 | `winner_past3` | Winning team's result percentage over the last 3 matches (form) | ✅ **DYNAMIC** |
| 17 | `loser_past3` | Losing team's result percentage over the last 3 matches | ✅ **DYNAMIC** |

> **Important note:** This group is considered the most reliable "time-sensitive" set of columns in the dataset — verification showed that for the same team (e.g. Spirit), these values differ from match to match (39, 31, 18 distinct unique values respectively).

### 3.3 Group: Historical per-map win rate (18 columns)

| # | Column pair | Map | Status |
|---|---|---|---|
| 18–19 | `winner_mirage` / `loser_mirage` | Mirage | Dynamic (history up to the match) |
| 20–21 | `winner_inferno` / `loser_inferno` | Inferno | Dynamic |
| 22–23 | `winner_nuke` / `loser_nuke` | Nuke | Dynamic |
| 24–25 | `winner_dust2` / `loser_dust2` | Dust2 | Dynamic |
| 26–27 | `winner_overpass` / `loser_overpass` | Overpass | Dynamic |
| 28–29 | `winner_train` / `loser_train` | Train | Dynamic |
| 30–31 | `winner_ancient` / `loser_ancient` | Ancient | Dynamic |
| 32–33 | `winner_vertigo` / `loser_vertigo` | Vertigo | Dynamic |
| 34–35 | `winner_anubis` / `loser_anubis` | Anubis | Dynamic |

### 3.4 Group: Team1 team-level average stats (6 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 41 | `team1_name` | Team name | Meta (key) |
| 42 | `team1_avg_DPR` | Average Deaths Per Round | ❌ **STATIC** |
| 43 | `team1_avg_KAST` | Average KAST percentage (Kill/Assist/Survive/Trade) | ❌ **STATIC** |
| 44 | `team1_avg_ADR` | Average Damage per Round | ❌ **STATIC** |
| 45 | `team1_avg_KPR` | Average Kills Per Round | ❌ **STATIC** |
| 46 | `team1_avg_RATING` | Average HLTV Rating | ❌ **STATIC** |

> **Confirmed example:** Team Spirit appears in 104 matches, yet in all 104 rows `team1_avg_RATING = 1.14` — the same value. This is a single fixed average over the whole career (or the period the dataset was collected), mechanically copied into every match row.

### 3.5 Group: Team1 players 1–5 (30 columns)

For each player, 6 columns repeat: `name`, `DPR`, `KAST`, `ADR`, `KPR`, `RATING`.

| # | Column pattern | Description | Status |
|---|---|---|---|
| 47–52 | `team1_player_1_*` | Player 1's name and stats | ❌ **STATIC** |
| 53–58 | `team1_player_2_*` | Player 2 | ❌ **STATIC** |
| 59–64 | `team1_player_3_*` | Player 3 | ❌ **STATIC** |
| 65–70 | `team1_player_4_*` | Player 4 | ❌ **STATIC** |
| 71–76 | `team1_player_5_*` | Player 5 | ❌ **STATIC** |

> **Confirmed example:** Player `donk` appears in 104 matches (May 2024 – October 2025); in all 104 rows DPR=0.67, KAST=74.9, ADR=90.6, RATING=1.31 — identical. Roster changes and form improvements/declines are **not reflected at all** in these columns.

### 3.6 Group: Team2 team-level stats (6 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 77 | `team2_name` | Team name | Meta (key) |
| 78–82 | `team2_avg_DPR/KAST/ADR/KPR/RATING` | Same logic as Team1 | ❌ **STATIC** |

### 3.7 Group: Team2 players 1–5 (30 columns)

| # | Column pattern | Status |
|---|---|---|
| 83–112 | `team2_player_1_*` ... `team2_player_5_*` | ❌ **STATIC** (same pattern as team1) |

### 3.8 Group: Differential columns (5 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 113 | `rating_diff` | Rating difference: Team1 − Team2 | ⚠️ **SEMI-DYNAMIC** (see note below) |
| 114 | `adr_diff` | ADR difference | ⚠️ SEMI-DYNAMIC |
| 115 | `kast_diff` | KAST difference | ⚠️ SEMI-DYNAMIC |
| 116 | `kpr_diff` | KPR difference | ⚠️ SEMI-DYNAMIC |
| 117 | `dpr_diff` | DPR difference | ⚠️ SEMI-DYNAMIC |

> **Important nuance:** These columns do change value from match to match (e.g. 19 distinct unique values were found for `rating_diff`), but this is **not because they change over time** — it's because the **opposing team changes** each time. Neither of the two static values (`team1_avg_RATING` and `team2_avg_RATING`) changes on its own; only which two static values are being compared changes. So these columns reflect **"the difference between static profiles," not "current form"** — they cannot be trusted as a primary source for seeding.

### 3.9 Group: Overall result history (8 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 118 | `team1_wins` | Total number of wins (up to this match) | ✅ **DYNAMIC** (46 distinct values, confirmed) |
| 119 | `team2_wins` | Same, for team2 | ✅ DYNAMIC |
| 120 | `team1_losses` | Total number of losses | ✅ DYNAMIC (16 distinct values) |
| 121 | `team2_losses` | Same, for team2 | ✅ DYNAMIC |
| 122 | `team1_totalwinrate` | Overall win percentage | ✅ DYNAMIC (72 distinct values) |
| 123 | `team2_totalwinrate` | Same, for team2 | ✅ DYNAMIC |
| 124 | `team1_totallossrate` | Overall loss percentage | ✅ DYNAMIC |
| 125 | `team2_totallossrate` | Same, for team2 | ✅ DYNAMIC |

### 3.10 Group: Consistency and player balance (9 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 126 | `team1_rating_std` | Rating standard deviation | ❌ **STATIC** (1 unique value — 0.1467) |
| 127 | `team2_rating_std` | Same, for team2 | ❌ STATIC |
| 128 | `consistency_advantage` | Consistency difference (team1 − team2) | ⚠️ SEMI-DYNAMIC (56 distinct values due to opponent changing, but both sides are static) |
| 129 | `team1_top_player` | Top player's rating | ❌ **STATIC** (1 unique value — 1.31) |
| 130 | `team2_top_player` | Same, for team2 | ❌ STATIC |
| 131 | `star_player_advantage` | Star-player difference | ⚠️ SEMI-DYNAMIC |
| 132 | `team1_weakest_player` | Weakest player's rating | ❌ **STATIC** (1 unique value — 0.94) |
| 133 | `team2_weakest_player` | Same, for team2 | ❌ STATIC |
| 134 | `weakest_link_advantage` | Weak-link difference | ⚠️ SEMI-DYNAMIC |

### 3.11 Group: Context-dependent win rate (6 columns)

| # | Column | Description | Status |
|---|---|---|---|
| 135 | `team1_online_winrate` | Win rate in online matches | ✅ **DYNAMIC** (but few unique values — 3, likely due to few online matches) |
| 136 | `team2_online_winrate` | Same, for team2 | ✅ DYNAMIC |
| 137 | `team1_lan_winrate` | Win rate in LAN matches | ✅ **DYNAMIC** (86 distinct values) |
| 138 | `team2_lan_winrate` | Same, for team2 | ✅ DYNAMIC |
| 139 | `team1_overall_winrate` | Overall win rate (another version) | ✅ DYNAMIC (87 distinct values) |
| 140 | `team2_overall_winrate` | Same, for team2 | ✅ DYNAMIC |

**Total check:** 16+6+18+6+30+6+30+5+8+9+6 = **140** ✅

---

## 4. STATIC vs DYNAMIC — final classification and why it matters

### 4.1 Why this distinction is critical

For the seeding model, we need an answer to the question: **"before the tournament starts, how strong is the team today?"** Only metrics that **genuinely change over time** can answer this question.

**A STATIC column** is a team's single frozen average over its entire history. It cannot distinguish May 2024 from October 2025, and cannot reflect roster changes or rises/drops in form.

**A DYNAMIC column** is calculated for each match based on the actual history up to that match. This is what we need.

### 4.2 Final table

| Status | Number of columns | Column list |
|---|---|---|
| ✅ **DYNAMIC — used with confidence** | ~45 | `date`, `winner`, `score_team1/2`, `event_type`, head2head group (6), past3 (2), per-map win-rate group (18), wins/losses/totalwinrate/totallossrate (8), online/lan/overall winrate (6) |
| ❌ **STATIC — NOT used in seeding calculation** | ~76 | avg_DPR/KAST/ADR/KPR/RATING (team-level, 10), all player stats (60), rating_std (2), top_player/weakest_player (4) |
| ⚠️ **SEMI-DYNAMIC — use cautiously, only as a supplementary signal** | ~9 | rating_diff, adr_diff, kast_diff, kpr_diff, dpr_diff, consistency_advantage, star_player_advantage, weakest_link_advantage |
| Meta / identification | ~10 | match_id, hltv_match_id, tournament, season, scraped_date, hltv_url, etc. |

### 4.3 Practical conclusion

For the Elo and seeding calculation, the **STATIC group is completely excluded**. Instead, the model will be built **only on the DYNAMIC group** (primarily `date`, `team1_name`, `team2_name`, `winner`, `score_team1/2`, plus supporting head2head/past3/map-winrate/online-lan-winrate columns).

---

## 5. Data quality issues and correction rules

### 5.1 Issue: bo1 matches incorrectly labeled as "bo3"

**Observation:** In 1010 rows, `winner_map` is empty, and in most of these rows `score_team1`/`score_team2` fall in the range 0–34 (e.g. 13-7, 16-14) — this is **not a map count, but the round count within a single map**. Despite this, the `match_type` column labels all of these as `bo3`.

**For comparison:** In rows where `winner_map` is filled in, `score_team1`/`score_team2` take only the values 0, 1, 2, 3 (the actual number of maps, e.g. 2-0 or 2-1).

**Three distinct cases identified:**

| Case | Condition | Row count | Fix |
|---|---|---|---|
| **A** | `winner_map` is empty **and** (`score_team1>3` or `score_team2>3`) | 965 | `match_type` changed to `bo1` |
| **B** | `winner_map` is empty **and** score is within ≤3 (e.g. 1-0, 0-1) | 44 | `match_type` is already correct (actually bo1), only the **map name is missing** — flagged, not changed |
| **C** | Odd value: `score_team1=1, score_team2=2` ("Showmatch CS" tournament) | 1 | Flagged as an anomaly, not auto-corrected, needs manual review |

**Fix code (for Case A):**
```python
condition = df['winner_map'].isna() & (
    (df['score_team1'] > 3) | (df['score_team2'] > 3)
)
df.loc[condition, 'match_type'] = 'bo1'
```

**Why this matters:** If not fixed, the model might misinterpret a row like `score_team1=13, score_team2=7` as "team1 won 13 times," or the "margin of victory" in Elo calculations could end up on a completely wrong scale.

### 5.2 Issue: `event_type` case inconsistency

**Observation:** The column takes 4 different values: `LAN`, `lan`, `Online`, `online` — semantically only 2 groups.

**Fix:**
```python
df['event_type'] = df['event_type'].str.lower()
# result: only 'lan' and 'online'
```

### 5.3 Issue: `match_number` — completely empty column

**Observation:** `NaN` in all 7,033 rows.

**Fix:** The column is dropped entirely.
```python
df = df.drop(columns=['match_number'])
```

### 5.4 Other NULL values (general list)

| Column | Number of empty rows | Recommendation |
|---|---|---|
| `winner_map`, `loser_map` | 1010 | Resolved by the rule in section 5.1 |
| `decider_map` | 63 | Natural for bo1 matches (no 3rd map) |
| `team1_player_X_*` columns | ~1–8 | Small count, can be ignored or filled with an average |
| `consistency_advantage`, `star_player_advantage`, etc. | 1–2 | Small count, not a real issue |

---

## 6. Elo system — methodology

### 6.1 Why Elo (instead of the static columns)

Every major rating system in the world (chess — Elo, League of Legends — TrueSkill/Glicko, football — various Elo variants) is built from just one thing: **who beat whom, and when**. They don't need player statistics (ADR, KAST, etc.), because a win/loss is already the final outcome that has already absorbed all factors (skill, strategy, form on the day).

### 6.2 Columns needed for Elo

**Required (for the core Elo):**

| Column | Purpose |
|---|---|
| `date` | To process matches in chronological order |
| `team1_name`, `team2_name` | Who played whom |
| `winner` | The primary signal for the Elo update |

**Enhancing (recommended):**

| Column | Purpose |
|---|---|
| `score_team1`, `score_team2` | Margin of victory — to account for the difference between 2-0 and 2-1 |
| `event_type` | To maintain separate Elo ratings for LAN and Online |
| `winner_past3`, `loser_past3` | As an additional "form" signal |
| `winner_head2head_percentage/freq` | Added as an adjustment for the historical head-to-head ratio between two teams |

**Optional (for per-map Elo):**

| Column | Purpose |
|---|---|
| `winner_map`, `loser_map`, `decider_map` | Separate Elo per map (e.g. "Team X is strong on Mirage but weak on Anubis") |

**Columns to be entirely excluded:** All STATIC-group columns from section 4.2.

### 6.3 Algorithm — step by step

```
1. Each team starts with an initial Elo rating (default: 1500)

2. All matches are sorted by date (oldest to newest)

3. For each match, in sequence:
   a. Both teams' CURRENT Elo scores are retrieved
   b. The expected win probability is calculated:
      E_A = 1 / (1 + 10^((Elo_B - Elo_A) / 400))
   c. Compared against the actual result (S_A = 1 if won, 0 if lost)
   d. The new Elo is calculated:
      Elo_A_new = Elo_A + K × (S_A - E_A)
   e. (Optional) The K coefficient is adjusted based on margin of victory
   f. Both teams' Elo scores are updated, move to the next match

4. On tournament day: the LATEST Elo score of the N entered teams is retrieved
   → the seed order is determined based on this score
```

### 6.4 Why this approach is right for your project

| Advantage | Description |
|---|---|
| No data leakage | Each Elo score is calculated only from results up to that day — it does not "know" the future |
| Time-sensitive | Spirit in May 2024 and Spirit in October 2025 will have completely different Elo scores |
| Works for new teams | Even with few matches, calculation still starts from 1500 |
| Updates automatically | The system updates itself as new results are entered into the site |
| Adapts to context | Separate Elo ratings can be maintained for LAN/Online |

---

## 7. Model architecture — full pipeline

```
┌─────────────────────────────────────────────────────────┐
│ STAGE 1: Data cleaning                                    │
│  - Drop the match_number column                           │
│  - Normalize event_type (lower case)                      │
│  - Fix the bo1/bo3 mislabeling (section 5.1)               │
│  - Exclude STATIC columns from the main calculation        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 2: Elo calculation                                   │
│  - Sort all matches by date                                │
│  - Maintain an overall Elo for each team                   │
│  - (Optional) Maintain separate LAN Elo and Online Elo       │
│  - (Optional) Maintain per-map Elo                          │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 3: Team name matching (fuzzy matching)                │
│  - Match the name entered by the organizer with the          │
│    name in the dataset (e.g. "NAVI" = "Natus Vincere")       │
│  - If a team isn't found — a fallback mechanism (default Elo)│
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 4: Determining seed order                             │
│  - The latest Elo scores of the N teams are retrieved        │
│  - Sorted in descending order by score                      │
│  - 1-seed = highest Elo                                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 5: Bracket construction (standard sports math)         │
│  - For 8 teams: 1v8, 4v5, 3v6, 2v7                           │
│  - If N ≠ 2^n: a "bye" (automatic advance) system            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ STAGE 6: Explainability                                     │
│  - Shows which factors (head2head, form, LAN/Online          │
│    difference) contributed to each team's Elo score          │
└─────────────────────────────────────────────────────────┘
```

---

## 8. Open questions / next steps

- [ ] Which library to use for fuzzy matching (e.g. `rapidfuzz`) and what matching threshold to set
- [ ] How the initial Elo value (1500) and the K-coefficient should be tuned (these differ across sports)
- [ ] How margin of victory (e.g. the difference between 2-0 and 2-1) should be integrated into the Elo formula
- [ ] What exact rules the "bye" system should follow for N ≠ 2^n cases
- [ ] When LAN/Online Elo are maintained separately, how they should be combined (if a tournament is mixed)
- [ ] Whether a confidence interval should be added for new/lesser-known teams

---

*This document was prepared as part of the CS2 tournament manager project, based on dataset analysis. All static/dynamic claims were verified directly on the dataset using Python/pandas.*
