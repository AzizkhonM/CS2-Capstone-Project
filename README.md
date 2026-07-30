# CS2 Match Outcome Predictor & Seeding Engine

**Student:** Azizkhon Muzaffarov
**Project track:** Individual Project Track (Tabular)
**Status:** In progress — see `PROJECT_STATUS.md`

## Problem statement

CS2 tournament organizers (including my own tournament management website)
currently seed teams into brackets manually and subjectively, with no
objective way to justify placements. This project builds a supervised ML
model that predicts the win probability between two CS2 teams, used both
for direct match-outcome prediction and to generate explainable,
data-driven tournament seeding for N teams (4, 8, 16, or arbitrary size).

## ML task type

Supervised binary classification — predict P(team1 beats team2).

## Dataset source

`cs2_newestcombinedmatches.csv` — professional CS2 match data, originally
scraped from HLTV.org and published on
[Kaggle](https://www.kaggle.com/datasets/griffindesroches/cs2-hltv-professional-match-statistics-dataset).
7,033 matches, 140 columns, 2024-05-15 to 2025-10-16. See `data/README.md`
for full details, known issues, and download instructions.

## Project pipeline / system architecture

```
Raw CSV (Kaggle)
   ↓
01_eda.ipynb            — exploratory analysis, static vs dynamic column audit
   ↓
02_preprocessing.ipynb  — data cleaning (bo1/bo3 fix, event_type normalization,
                           drop static/leaky columns), feature selection
   ↓
03_baseline_elo.ipynb   — self-computed, time-ordered Elo rating (baseline)
   ↓
04_model_training.ipynb — Logistic Regression + XGBoost, MLflow experiment tracking
   ↓
05_evaluation.ipynb     — held-out (temporal split) evaluation, error analysis
   ↓
06_demo.ipynb           — inference pipeline: team names → fuzzy match →
                           feature lookup → win probability → seeding/bracket
```

Full technical rationale: `docs/Column_Analysis.md` and `docs/Project_Brief.md`.

## Models / approaches tested

| Approach                                                              | Role                              |
| --------------------------------------------------------------------- | --------------------------------- |
| Elo rating (from`date`, `team1_name`, `team2_name`, `winner`) | Baseline                          |
| Logistic Regression                                                   | Interpretable baseline classifier |
| XGBoost                                                               | Main model                        |

## Final model and justification

Logistic Regression was selected as the final model. On a temporal (time-based) held-out test split, it achieved Accuracy 0.759, AUC 0.841, and Brier score 0.161 — marginally outperforming a hyperparameter-tuned XGBoost (best: Accuracy 0.752, AUC 0.840, Brier 0.162) across all metrics, while remaining simpler and more interpretable (see coefficient analysis in `notebooks/04_model_training.ipynb`). Both substantially outperformed the Elo-only baseline.

## Evaluation metrics and results

**Metrics:** Accuracy and ROC-AUC on a temporal (time-based) train/test
split — not random split, to avoid look-ahead bias. Additionally,
calibration (Brier score) and prediction symmetry are checked as
robustness measures (see `docs/Project_Brief.md`, Section 12).

| Model               | Accuracy         | AUC              | Brier score      |
| ------------------- | ---------------- | ---------------- | ---------------- |
| Elo-only baseline   | 0.6033           | 0.6277           | 0.2368           |
| Logistic Regression | **0.7591** | **0.8409** | **0.1612** |
| XGBoost             | 0.7520           | 0.8387           | 0.1622           |

**Additional robustness checks (Phase 9):**

- Calibration: reliability diagram comparing predicted probability vs
  observed win rate.
- Symmetry: P(A beats B) + P(B beats A) should ≈ 1 for a sample of
  team pairs, tested in both input orders.
- New/sparse-history teams: model output evaluated separately for teams
  with few or no historical matches.

_Results to be filled in after `05_evaluation.ipynb` is run. See `results/`
for plots and error analysis once available._

## Implementation notes (found during model training)

* `winner_*`/`loser_*` dataset columns are named relative to the actual match outcome and are leakage-prone if used directly as features; they were reframed to `team1_*`/`team2_*` before training (see `04_model_training.ipynb`).
* `totalwinrate` and `totallossrate` are perfectly collinear; `totallossrate_diff` was dropped from the final 20-feature set.
* Elo sanity check confirmed correct behavior: mean `elo_diff` was +32.4 when team1 won vs -8.97 when team1 lost.

## Installation instructions

```bash
git clone <repo-url>
cd cs2-seeding-capstone
pip install -r requirements.txt
```

Download the dataset from the Kaggle link in `data/README.md` and place
it at `data/cs2_newestcombinedmatches.csv`.

## Training / fine-tuning instructions

Run the notebooks in order (each saves its output for the next step):

```
notebooks/01_eda.ipynb
notebooks/02_preprocessing.ipynb   → data/cleaned_matches.csv
notebooks/03_baseline_elo.ipynb    → models/elo_ratings.csv
notebooks/04_model_training.ipynb  → models/logreg_model.pkl (MLflow-logged)
notebooks/05_evaluation.ipynb      → results/
```

## Demo and inference run instructions

**Colab-first:** open `notebooks/06_demo.ipynb` in Google Colab (badge/link
to be added), run all cells. It loads `models/logreg_model.pkl` and
`models/elo_ratings.csv`, then accepts N team names and returns a seeded
bracket.

_No separate application/API is used for this project — inference is
demonstrated entirely through the Colab notebook._

## Example input and output

**Input:**

```python
teams = ["Spirit", "NAVI", "G2", "Vitality", "FaZe", "MOUZ", "Liquid", "Astralis"]
tournament_type = "LAN"
```

**Output (example, illustrative):**

```
Seed 1: Vitality   (power score 0.74)
Seed 2: Spirit     (power score 0.69)
Seed 3: NAVI       (power score 0.58)
Seed 4: G2         (power score 0.55)
Seed 5: MOUZ       (power score 0.44)
Seed 6: FaZe       (power score 0.38)
Seed 7: Liquid     (power score 0.29)
Seed 8: Astralis   (power score 0.22)

Bracket:
  Vitality vs Astralis
  G2 vs MOUZ
  NAVI vs FaZe
  Spirit vs Liquid
```

## Known limitations

- ~76 of 140 dataset columns (player/team average stats) are static
  career averages and are excluded from modeling — see `data/README.md`.
- Team-name resolution relies on fuzzy matching; ambiguous/unmatched
  names fall back to a default Elo (1500).
- Teams with sparse match history produce less reliable estimates; this
  has not yet been empirically validated and will be explicitly tested
  (Phase 9) rather than only assumed.
- Roster changes are not explicitly tracked (static player stats are
  excluded), so Elo may not reflect a team's current lineup if a major
  roster change occurred shortly before the tournament.
- Predicted probabilities are not guaranteed to be well-calibrated
  out of the box; calibration will be checked (reliability diagram /
  Brier score) before probabilities are relied on for seeding.
- Prediction symmetry (P(A beats B) + P(B beats A) ≈ 1) is not
  guaranteed by model construction and will be explicitly tested and
  corrected if violated.
- Scope is limited to a static, publicly available historical dataset —
  no real-time HLTV integration.

## Responsible AI considerations

Data consists of public professional esports match results (HLTV.org,
via Kaggle) with no personal or private information beyond public player
aliases. No special privacy or licensing restrictions apply beyond
standard attribution.

**Fairness:** the model will be less reliable for teams with sparse match
history, introducing a bias against newer/under-represented teams; this
is surfaced via a confidence flag rather than hidden. The model does not
capture recent roster changes. These limitations are disclosed, and the
tool is intended as decision support for organizers, not a sole or final
authority for seeding disputes.

## Repository structure

```
├── README.md              — this file
├── .gitignore
├── PROJECT_STATUS.md       — running log of progress against course phases
├── requirements.txt
├── notebooks/              — EDA, preprocessing, baseline, training, evaluation, demo
├── docs/                   — Project Brief, column analysis, ML formulation notes
├── models/                 — trained model (.pkl) and Elo ratings (not committed, see .gitignore)
├── data/                   — data/README.md (source, license, column dictionary)
└── results/                — evaluation metrics, plots, error analysis
```

## Documentation

- Project Brief: `docs/Project_Brief.docx`
- Full column analysis: `docs/Column_Analysis.md`
- ML formulation notes: `docs/ML_Formulation_Notes.md`
- Data source & dictionary: `data/README.md`
- Progress log: `PROJECT_STATUS.md`

## Trained model

The trained model (`models/logreg_model.pkl`) and computed Elo ratings
(`models/elo_ratings.csv`) are not committed to this repository — see
`.gitignore`. Regenerate them by running the notebooks in order
(01 → 05), or download pre-trained artifacts from [link, if hosted].
