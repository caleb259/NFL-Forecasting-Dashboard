# Update Log

This document tracks major progress updates for the Fourth & Forecast NFL prediction dashboard.

## May 2026

### Project Setup

- Created the project idea for an NFL game prediction dashboard.
- Decided to focus on explainable NFL game forecasts.
- Created the GitHub repository.
- Set up the initial project folder structure.
- Created the initial README file.
- Created documentation files in the `docs/` folder.
- Set up a Python virtual environment.
- Installed required packages, including pandas, scikit-learn, Streamlit, Plotly, and `nfl_data_py`.

### Data Loading

- Created an initial data test script.
- Successfully loaded NFL schedule data using `nfl_data_py`.
- Saved the first raw schedule dataset.
- Created the first data exploration notebook.
- Built a clean game results dataset from schedule and score data.
- Created the first target variable, `home_team_won`.

### Feature Engineering

- Created `02_feature_engineering.ipynb`.
- Converted games into team-game rows.
- Created pre-game season-long averages.
- Created point differential features.
- Created win percentage features.
- Created home vs. away difference features.
- Saved the first modeling dataset.

### Baseline Modeling

- Created `03_model_testing.ipynb`.
- Trained the first Logistic Regression baseline model.
- Used a random train-test split.
- Baseline random split accuracy: 59.35%.
- Saved baseline prediction results.

### Improved Model Evaluation

- Created `04_model_improvement.ipynb`.
- Switched from random train-test split to season-based testing.
- Trained on 2023–2024 and tested on 2025.
- Season-based model accuracy: 61.40%.
- Documented the result in modeling notes.

### Recent-Form Features

- Created `05_recent_form_features.ipynb`.
- Added last-3-game rolling features.
- Tested recent scoring, points allowed, point differential, and win percentage.
- Recent-form model accuracy: 61.40%.
- Result did not improve accuracy but did not reduce it.

### Expanded Training Data

- Created `06_expand_training_data.ipynb`.
- Expanded dataset to use 2018–2025 games.
- Trained on 2018–2024 and tested on 2025.
- Expanded training data accuracy: 62.46%.
- This became the best model result at that point.

### EPA Feature Test

- Created `07_epa_features.ipynb`.
- Loaded play-by-play data.
- Created offensive and defensive EPA/play features.
- Tested EPA features with Logistic Regression.
- EPA feature model accuracy: 61.40%.
- EPA did not improve the model in its first version.

### Model Comparison

- Created `08_compare_models.ipynb`.
- Compared Logistic Regression, Random Forest, and Gradient Boosting.
- Results:
  - Logistic Regression: 62.46%
  - Random Forest: 60.70%
  - Gradient Boosting: 56.49%
- Logistic Regression remained the best-performing model at this stage.

### Elo Features

- Created `09_elo_features.ipynb`.
- Added Elo ratings as team-strength features.
- Elo settings:
  - Base Elo: 1500
  - K-factor: 20
  - Home-field advantage: 55 Elo points
- Added Elo difference, Elo with home-field advantage, and Elo-based home win probability.
- Elo feature model accuracy: 63.51%.
- Elo became the best-performing model feature upgrade.

### Upcoming Forecasts

- Created `src/predict_upcoming.py`.
- Added support for 2026 scheduled game forecasts.
- Added predicted margin of victory using a regression model.
- Created projected team records based on forecasted winners.
- Created expected team records based on win probabilities.
- Added the Upcoming Forecasts dashboard page.

### Projected Standings

- Added conference and division metadata to `src/team_info.py`.
- Added projected division standings to the Upcoming Forecasts page.
- Added projected conference standings to the Upcoming Forecasts page.

### Forecast Metadata

- Added `forecast_metadata.json` to track when upcoming forecasts were last generated.
- Updated the Home page to display forecast metadata.
- Updated the Upcoming Forecasts page to display forecast metadata.\

### Forecast Update Process

- Created `docs/update_process.md`.
- Documented the manual weekly process for refreshing 2026 forecasts.
- Added update instructions for regenerating predictions, projected records, and forecast metadata.

### Margin Model Testing

- Created `11_margin_model_testing.ipynb`.
- Tested multiple regression models for predicting home point differential.
- Random Forest Regressor performed best for margin prediction.
- Best margin model MAE: 10.28 points.
- Updated `src/predict_upcoming.py` to use Random Forest Regressor for projected margins.

### Reusable Scripts

- Created `src/train_model.py`.
- Updated the training script to use Logistic Regression with Elo features.
- Created `src/elo.py`.
- Moved Elo logic into reusable functions.
- Created `src/data_loader.py`.
- Added reusable functions for loading and saving project data.
- Refactored `train_model.py` to use `src/elo.py` and `src/data_loader.py`.
- Created `src/feature_engineering.py`.
- Moved feature engineering logic into reusable functions.
- Refactored `src/train_model.py` so it can rebuild modeling features from game results.

### Streamlit Dashboard

- Created a working Streamlit dashboard.
- Renamed `app.py` to `Home.py`.
- Added weekly prediction table.
- Added prediction cards to the homepage.
- Created the Game Breakdown page.
- Created the Team Dashboard page.
- Created the Model Performance page.
- Created the How the Model Works page.
- Created the Model Comparison page.
- Updated the dashboard to use the current best Elo model predictions.
- Created `src/team_info.py` for NFL team names, colors, and logo URLs.
- Added team logos and team-color accents to homepage prediction cards.
- Created `src/style.py` for reusable dashboard styling.
- Refactored dashboard pages to use shared styling helpers.

### GitHub and Documentation

- Updated the README to match the current project.
- Added dashboard screenshots to the README.
- Updated modeling notes with experiment results.
- Updated the project plan.
- Updated this update log.

## Current Best Model

| Model | Training Data | Testing Data | Accuracy |
|---|---|---|---:|
| Logistic Regression Elo and strength of schedule features | 2018–2024 NFL seasons | 2025 NFL season | 63.86% |

## Current Dashboard Pages

- Home
- Game Breakdown
- Team Dashboard
- Model Performance
- How the Model Works
- Model Comparison

## Next Planned Improvements

Possible next steps:

- Create a reusable feature engineering script.
- Add strength of schedule features.
- Tune Elo settings.
- Add team logos and colors.
- Improve dashboard styling.
- Add future game prediction support.
- Deploy the Streamlit app publicly.