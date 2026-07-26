# Data

## Source

`cs2_newestcombinedmatches.csv` — professional CS2 match data, originally
scraped from [HLTV.org](https://www.hltv.org/) and published on Kaggle:

[CS2 (HLTV) Professional Match Statistics Dataset](https://www.kaggle.com/datasets/griffindesroches/cs2-hltv-professional-match-statistics-dataset)

- 7,033 matches
- 140 columns
- Date range: 2024-05-15 to 2025-10-16
- 331 unique teams, 648 tournaments
- Public professional esports results; no personal/private data

The raw CSV is **not committed to this repository** (see `.gitignore`).
Download it directly from the Kaggle link above and place it at
`data/cs2_newestcombinedmatches.csv` before running the notebooks.

## What one record represents

One completed match between two teams (predominantly best-of-3; a
subset are best-of-1 matches mislabeled as bo3 — see Known Issues).

## Target

`winner` — team1 or team2 (binary classification target).

## Column groups (140 total)

| Group | Count | Notes |
|---|---|---|
| Match metadata | 16 | date, tournament, score, match_type, event_type, etc. |
| Head-to-head & form | 6 | winner/loser_past3, head2head freq/percentage — dynamic |
| Per-map win rate | 18 | 9 maps × winner/loser — dynamic |
| Team-level averages | 12 | avg_RATING/DPR/KAST/ADR/KPR — **static, not used** |
| Player-level stats | 60 | per-player averages — **static, not used** |
| Differential features | 5 | rating_diff etc. — semi-dynamic, used cautiously |
| Win/loss history | 8 | wins/losses/totalwinrate — dynamic |
| Consistency/balance | 9 | rating_std, top/weakest player — **mostly static, not used** |
| Context win rate | 6 | online/lan/overall winrate — dynamic |

Full column-by-column breakdown: see `docs/Column_Analysis.md`.

## Known issues

1. **bo1/bo3 mislabeling** — 1,010 rows have empty `winner_map` and
   `match_type='bo3'`, but score values in the round-count range
   (4–34), indicating true bo1 matches. Fix rule:
   `winner_map is null AND (score_team1>3 OR score_team2>3) → match_type='bo1'`
   (965 rows corrected; ~44 rows are genuine bo1 with missing map name;
   1 anomalous row flagged for manual review).
2. **event_type casing** — inconsistent `LAN`/`lan`/`Online`/`online`;
   normalized to lowercase.
3. **match_number** — 100% empty; dropped.
4. **Static columns** — ~76 columns (team/player average stats,
   rating_std, top/weakest player) are constant per team/player across
   all matches (verified: e.g. `donk`'s stats identical across 104
   matches). These do not reflect per-match/point-in-time state and are
   **excluded from modeling** to avoid leakage and stale signal.

## License / usage

Public HLTV match results, redistributed via Kaggle. Used for
educational purposes. Source acknowledged; no redistribution of
restricted or private content beyond what is already public on Kaggle.