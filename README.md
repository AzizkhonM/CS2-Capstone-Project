# CS2 Match Outcome Predictor & Seeding Engine

**Student:** Azizkhon Muzaffarov
**Project track:** Individual Project Track (Tabular)
**Status:** Done

🔴 **[Live demo](https://cs2-seeding.vercel.app/)** — try it now, no installation needed.

## Problem statement

CS2 tournament organizers (including my own tournament management website) currently seed teams into brackets manually and subjectively, with no objective way to justify placements. This project builds a supervised ML model that predicts the win probability between two CS2 teams, used both for direct match-outcome prediction and to generate explainable, data-driven tournament seeding for N teams (4, 8, 16, or arbitrary size).

## ML task type

Supervised binary classification — predict P(team1 beats team2).

## Dataset source

`cs2_newestcombinedmatches.csv` — professional CS2 match data, originally scraped from HLTV.org and published on [Kaggle](https://www.kaggle.com/datasets/griffindesroches/cs2-hltv-professional-match-statistics-dataset).
7,033 matches, 140 columns, 2024-05-15 to 2025-10-16. See `data/README.md` for full details, known issues, and download instructions.

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

**Metrics:** Accuracy and ROC-AUC on a temporal (time-based) train/test split — not random split, to avoid look-ahead bias. Additionally, calibration (Brier score) and prediction symmetry are checked as robustness measures (see `docs/Project_Brief.md`, Section 12).

| Model               | Accuracy         | AUC              | Brier score      |
| ------------------- | ---------------- | ---------------- | ---------------- |
| Elo-only baseline   | 0.6033           | 0.6277           | 0.2368           |
| Logistic Regression | **0.7591** | **0.8409** | **0.1612** |
| XGBoost             | 0.7520           | 0.8387           | 0.1622           |

**Additional robustness checks (Phase 9 — completed, see `notebooks/05_evaluation.ipynb`):**

- **Calibration:** Brier score 0.1612 (consistent with training). Confidence-bucket accuracy increases monotonically from 57.8% (0–20% confidence) to 96.6% (80–100% confidence) — a strong sign the model's probabilities are meaningfully calibrated.
- **Symmetry:** mean |P(A,B) + P(B,A) − 1| = 0.040, max = 0.126 across a 30-pair sample. Small but non-zero — a symmetry correction (`p_final = (p_ab + (1 - p_ba)) / 2`) is applied at inference time (see `06_demo.ipynb`).
- **Sparse/new-history teams:** counter to the original hypothesis, sparse-history matches (<10 games, n=223) showed *higher* accuracy (93.3%) than established matchups (≥10 games, n=1176, 72.6%) — likely because sparse-history teams often face clear skill mismatches (predictable outcomes), while established-vs-established matches are closer contests. See Known Limitations for the revised interpretation.

Full results: `results/evaluation_summary.csv`, `results/calibration_curve.png`.

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

Download the dataset from the Kaggle link in `data/README.md` and place it at `data/cs2_newestcombinedmatches.csv`.

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

**Live demo:** [https://cs2-seeding.vercel.app/](https://cs2-seeding.vercel.app/) — enter 4/8/16 teams and get back a seeded, explainable bracket in the browser. No setup required.

> **Note:** the backend is hosted on Render's free tier and may take 30–60 seconds to respond on the first request after a period of inactivity ("cold start"). Subsequent requests are fast.

The frontend (`frontend/`) is deployed on **Vercel** and calls a **FastAPI** backend (`api/`) deployed on **Render**: [https://cs2-capstone-project.onrender.com/](https://cs2-capstone-project.onrender.com/)

**Colab (offline / reproducibility):** alternatively, open `notebooks/06_demo.ipynb` in Google Colab, run all cells. It loads `models/logreg_model.pkl` and `models/elo_ratings.csv`, then accepts N team names and returns a seeded bracket — useful for verifying results without depending on the hosted API.

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

## Post-training fixes (found after initial evaluation)

- **Seeding algorithm bug:** the initial bracket-pairing logic grouped seeds incorrectly (e.g. seed 1 and seed 2 could meet in the semifinal instead of only in the final). Fixed with a standard recursive tournament-seeding algorithm (`generate_seed_order`), verified for 4/8/16-team fields.
- **Cross-environment reproducibility:** all notebooks were updated to auto-detect the repo root and work identically in Google Colab and local Jupyter/VS Code, without manual path edits. Verified via a fresh clone on a separate machine.

## Known limitations

- ~76 of 140 dataset columns (player/team average stats) are static career averages and are excluded from modeling — see `data/README.md`.
- Team-name resolution relies on fuzzy matching; ambiguous/unmatched names fall back to a default Elo (1500). A visible confidence flag for sparse-history/unmatched teams is planned but not yet implemented in the web app.
- **(Revised after testing)** Sparse match history does not reduce prediction *accuracy* — empirically, sparse-history matches were *easier* to predict (93.3% vs 72.6% for established matchups), likely due to clearer skill gaps. However, the underlying Elo/feature *estimates* for such teams remain less statistically grounded (fewer observations), so a confidence flag is still recommended for transparency, even though it did not translate into lower observed accuracy.
- Roster changes are not explicitly tracked (static player stats are excluded), so Elo may not reflect a team's current lineup if a major roster change occurred shortly before the tournament.
- Predicted probabilities are reasonably calibrated (Brier 0.1612; confidence-bucket accuracy rises monotonically 57.8%→96.6%), though not perfectly — see evaluation results above.
- Prediction symmetry showed a small but measurable violation (mean error 4%, max 12.6%); a symmetry-averaging correction is applied at inference time rather than relying on raw model output.
- Scope is limited to a static, publicly available historical dataset — no real-time HLTV integration.

## Responsible AI considerations

Data consists of public professional esports match results (HLTV.org, via Kaggle) with no personal or private information beyond public player aliases. No special privacy or licensing restrictions apply beyond standard attribution.

**Fairness:** empirical testing did not find lower accuracy for sparse-history teams (see Evaluation results) — the originally hypothesized bias was not observed in outcome accuracy. However, sparse-history *feature estimates* (Elo, form) remain statistically less grounded due to fewer observations, so a confidence flag is still surfaced for transparency. The model does not capture recent roster changes. These limitations are disclosed, and the tool is intended as decision support for organizers, not a sole or final authority for seeding disputes.

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
├── results/                — evaluation metrics, plots, error analysis
├── src/                    — shared feature-building logic (src/features.py)
├── api/                    — FastAPI backend (main.py), deployed on Render
└── frontend/               — static web demo (index.html, result.html, style.css, team logos)
```

## Documentation

- Project Brief: `docs/Project_Brief.docx`
- Full column analysis: `docs/Column_Analysis.md`
- ML formulation notes: `docs/ML_Formulation_Notes.md`
- Data source & dictionary: `data/README.md`
- Progress log: `PROJECT_STATUS.md`

## Trained model

The trained model (`models/logreg_model.pkl`) and computed Elo ratings (`models/elo_ratings.csv`) are not committed to this repository — see `.gitignore`. Regenerate them by running the notebooks in order (01 → 05), or download pre-trained artifacts from [link, if hosted].
