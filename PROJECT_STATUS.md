# Project Status Log

Tracks progress against the 13 implementation phases from the Capstone
Implementation Helper. Updated as work progresses.

| Phase | Description                              | Status         | Notes                                                                                                                                                       |
| ----- | ---------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Select track, control scope              | ✅ Done        | Individual Project Track — CS2 Match Outcome Predictor & Seeding Engine                                                                                    |
| 2     | Define ML problem & success criteria     | ✅ Done        | Binary classification, target=`winner`, see `docs/Project_Brief.md`                                                                                     |
| 3     | Create repository & environment          | 🔄 In progress | Repo skeleton created; Colab env + requirements.txt pending                                                                                                 |
| 4     | Find, validate, document data            | ✅ Done        | See`data/README.md`                                                                                                                                       |
| 5     | EDA & data quality audit                 | ✅ Done        | Static vs dynamic column analysis, bo1/bo3 mislabeling found & fix rule defined                                                                             |
| 6     | Preprocessing, features, splits          | ⏳ Not started | Temporal split planned; feature list drafted in`docs/`                                                                                                    |
| 7     | Build baseline                           | ⏳ Not started | Elo (from date/team1/team2/winner) planned as baseline                                                                                                      |
| 8     | Train models, track experiments (MLflow) | ⏳ Not started | Logistic Regression + XGBoost planned                                                                                                                       |
| 9     | Evaluate final model, error analysis     | ⏳ Not started |                                                                                                                                                             |
| 10    | Responsible AI, privacy, limitations     | 🔄 In progress | Fairness/bias (sparse-history teams) and roster-change limitations documented in Project Brief and README; not yet reflected in code (e.g. confidence flag) |
| 11    | Reusable inference pipeline + demo       | ⏳ Not started |                                                                                                                                                             |
| 12    | GitHub/Colab reproducibility             | ⏳ Not started |                                                                                                                                                             |
| 13    | Documentation, QA, submission, defense   | 🔄 In progress | Full README draft (16 sections) completed; results/metrics sections still TBD pending model training                                                        |

**Legend:** ✅ Done · 🔄 In progress · ⏳ Not started
