# Fourth & Forecast
### NFL game predictions, explained.

Fourth & Forecast is a Streamlit dashboard for exploring NFL game predictions,
team performance, and the evidence behind each forecast.

Built by Caleb Linsenbardt as an ongoing data science project, its main goal
is to improve game-winner predictions through chronological evaluation,
careful feature engineering, and clear communication of uncertainty.

**[Open the live dashboard](https://nfl-forecasting-dashboard-bmigza2zszwnqz4rohkbzn.streamlit.app/)**

## What you can explore

- **Upcoming forecasts:** predicted winners, home and away win probabilities,
  and forecast update information.
- **Game breakdowns:** historical predictions, actual outcomes, and the
  features behind each prediction.
- **Team dashboards:** team-level results, schedules, and projections.
- **Model performance:** historical accuracy and game-by-game evaluation.
- **Model methodology:** how scoring history, Elo, and other features
  contribute to forecasts.
- **Season scenarios:** exploratory playoff projections and what-if tools.

The dashboard uses saved prediction files. Opening it does not automatically
retrain the models or incorporate new reports.

## Current winner model

The current model uses **logistic regression** to estimate home-win
probability from 13 team-level features:

| Feature group | Information used |
|---|---|
| Scoring history | Pregame scoring and points-allowed averages, with previous-season carryover |
| Recent form | Scoring and win percentage over the team's last three games in the current season |
| Team strength | Elo differences and Elo-based home-win probability |
| Record and schedule | Current-season win percentage and strength-of-schedule features |

Scoring carryover gives the previous season the weight of **four games**.
Its influence declines as current-season results accumulate. This blending
does not apply to win percentage or recent-form features.

Tied games remain in historical feature calculations but are excluded
from winner-classifier training and evaluation.

## Evaluated performance

| Evaluation | Games | Accuracy ↑ | Brier score ↓ | Log loss ↓ |
|---|---:|---:|---:|---:|
| 2021–2024 development backtests | 1,136 | 63.91% | 0.2247 | 0.6415 |
| 2025 follow-up evaluation | 284 | 64.79% | 0.2254 | 0.6410 |

Evaluations include regular-season and postseason games, excluding ties.

- Development backtests used expanding training windows: train on earlier
  seasons, then evaluate on the next season.
- The 2025 evaluation trained on 2018–2024.
- The 2025 season had already been inspected during development, so it is
  not an untouched final holdout.
- Accuracy measures winner picks. Brier score and log loss evaluate the
  predicted probabilities; lower values are better.
- These historical results are not a guarantee of future performance.

See the [scoring-carryover experiment](docs/scoring_carryover_experiment.md)
for the comparison and selection process.

## Research checkpoint: quarterback information

The current production winner model does **not** include quarterback
ratings or injury-report adjustments.

Recent research has focused on two questions:

1. Does historical quarterback passing efficiency add useful information
   beyond existing team features?
2. Can the expected starter be identified reliably using information
   available before a forecast?

### Initial QB feature experiment

A weekly expanding-window experiment compared the existing features with
the same features plus a home-versus-away QB passing-rating difference.

Both classifiers trained only on earlier 2025 games in this experiment.
Testing covered Week 9 onward, including postseason.

| Approach | Games | Accuracy ↑ | Brier score ↓ | Log loss ↓ |
|---|---:|---:|---:|---:|
| Existing features | 164 | 62.80% | 0.2223 | 0.6362 |
| Existing features + QB rating | 164 | 63.41% | 0.2228 | 0.6378 |

The added feature gained one correct winner pick but slightly worsened
both probability metrics. It was **not promoted to production**.

These results use a different training setup and test sample from the
main model evaluation above and should not be compared directly.

### Starter availability pilot

Depth-chart selections were compared with recorded starters, previous
starters, and the previous game's passing leader. The audits highlighted
cases where a depth-chart leader was not the player who started.

A separate four-game source pilot demonstrated how official team reports
can supply explicit exclusions or starting plans before a 24-hour cutoff.

The evidence loader keeps availability, starting plans, and source
timestamps separate. It leaves missing or conflicting evidence unresolved.

Publisher timestamps were inspected, but historical page contents were
not independently archive-verified. The selected pilot does not establish
league-wide coverage or an accuracy improvement.

Read more:

- [QB rating experiment](docs/qb_rating_experiment.md)
- [Availability source pilot](docs/qb_availability_source_pilot.md)

## Run locally

The project has been used with **Python 3.11 on Windows**.

### Clone the repository

```powershell
git clone https://github.com/caleb259/NFL-Forecasting-Dashboard.git
cd NFL-Forecasting-Dashboard
```

### Create an environment and install dependencies

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Start the dashboard

```powershell
.\.venv\Scripts\python.exe -m streamlit run Home.py
```

These commands use the environment's Python directly, so PowerShell
activation is not required.

Saved processed data and predictions are included in the repository.
Retraining is not required just to explore the dashboard.

## Run evaluations and refresh forecasts

From the project root:

```powershell
# Retrain the historical evaluation model and overwrite its prediction CSV
.\.venv\Scripts\python.exe src/train_model.py

# Evaluate the saved historical predictions
.\.venv\Scripts\python.exe src/evaluate_predictions.py

# Preview upcoming forecasts without saving output files
.\.venv\Scripts\python.exe src/predict_upcoming.py --dry-run

# Generate and save upcoming forecasts and related projections
.\.venv\Scripts\python.exe src/predict_upcoming.py
```

The forecast script is currently configured for the **2026 season**.
Forecast generation requires access to its data sources.

See the [update process](docs/update_process.md) for additional workflow notes.

### Research checks

```powershell
.\.venv\Scripts\python.exe src/check_qb_rating.py
.\.venv\Scripts\python.exe src/check_qb_availability_evidence.py
```

The broader QB audit uses downloaded historical data:

```powershell
.\.venv\Scripts\python.exe src/audit_qb_forecast_cutoffs.py
```

Research scripts are separate from production forecast generation.

## Project structure

```text
Home.py             Streamlit entry point
pages/              Dashboard pages
src/                Feature engineering, models, evaluations, and audits
data/processed/     Prepared historical datasets
data/predictions/   Saved evaluation results and forecasts
data/research/      Manually reviewed research evidence
docs/               Methodology, experiment records, and workflow notes
notebooks/          Earlier exploration and modeling experiments
```

## Data and tools

NFL data comes from the **nflverse ecosystem**, accessed through
`nfl_data_py` and direct nflverse data files. The availability pilot also
uses manually reviewed official team reports with source links.

The project uses:

- Python, pandas, and NumPy for data preparation
- scikit-learn for modeling and evaluation
- Streamlit and Plotly for the dashboard

## Current limitations

- The production winner model primarily reflects historical team results.
  It does not explicitly model injuries, roster turnover, coaching changes,
  weather, or betting markets.
- Historical date filtering does not independently verify when every
  source record was originally published or revised.
- QB availability research is exploratory and is not integrated into
  production forecasts.
- The separate margin model has not been reevaluated after the scoring
  feature changes.
- Season and playoff projections are exploratory scenarios, not validated
  championship probabilities.
- Older notebooks document development history; their results are not
  necessarily comparable with the current evaluation.

## Next priorities

- Expand the availability-source audit using a fixed sample across teams
  and consecutive weeks.
- Improve starter identification before testing further QB adjustments.
- Validate candidate features chronologically against matched baselines.
- Simplify dashboard navigation and presentation.
- Preserve forecast snapshots for future evaluation of predictions made
  at different times before kickoff.

Betting-market comparisons remain a possible future direction rather than
a current project commitment.

## Author

**Caleb Linsenbardt**

Fourth & Forecast combines hands-on data science learning with the goal
of building a useful, transparent NFL forecasting dashboard.