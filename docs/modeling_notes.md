# Modeling Notes

This document will track modeling decisions, experiments, and results.

## First Modeling Goal

The first goal is to predict whether the home team wins each game.

## First Model Choice

The first model will likely be logistic regression.

Reasons:

- It is simple and explainable.
- It can output win probabilities.
- It is a good baseline before testing more advanced models.

## Important Rule: Avoid Data Leakage

When predicting a game, the model should only use information that would have been available before that game was played.

For example, a Week 6 prediction should only use data from Weeks 1 through 5.

## Baseline Logistic Regression Model

The first baseline model used logistic regression to predict whether the home team wins.

Features used:

- Average points scored difference
- Average points allowed difference
- Average point differential difference
- Win percentage difference

Initial model accuracy: 59.35%

This is a useful starting point because the model performs better than random guessing. However, the model is still basic and should be improved with stronger features and a more realistic testing setup.

Possible improvements:

- Train on earlier seasons and test on a later season
- Add recent-performance features
- Add EPA/play features
- Add Elo ratings
- Add rest and schedule features
- Try stronger models after improving the features

<<<<<<< HEAD
## Recent Form Feature Test

This test added last-3-game features to the model.

New features included:

- Last 3 games average points scored difference
- Last 3 games average points allowed difference
- Last 3 games average point differential difference
- Last 3 games win percentage difference

Previous season-based baseline accuracy: 61.40%

Recent-form model accuracy: 61.40%

Result:
- To be updated after reviewing the model output.
=======
## Season-Based Model Test

The next model test used a more realistic evaluation setup. Instead of randomly splitting games, the model trained on the 2023 and 2024 seasons and tested on the 2025 season.

Season-based model accuracy: 61.40%

This result is encouraging because the model performed slightly better than the original random train-test split accuracy of 59.35%. Since this setup better represents real forecasting, it suggests that the basic pre-game features are providing useful predictive signal.

Next improvement:
- Add recent form features using each team's last 3 games before the matchup.

## Expanded Training Data Test

This test expanded the dataset from 2023–2025 to 2018–2025.

Training seasons:
- 2018–2024

Testing season:
- 2025

Features used:
- Season-long pre-game scoring differences
- Season-long pre-game points allowed differences
- Season-long pre-game point differential differences
- Season-long pre-game win percentage differences
- Last-3-game scoring differences
- Last-3-game points allowed differences
- Last-3-game point differential differences
- Last-3-game win percentage differences

Previous best accuracy: 61.40%

Expanded training data accuracy: 62.46%

Result:
- To be updated after reviewing the model output.

## EPA Feature Test

This test added play-by-play EPA features to the model.

New features included:

- Offensive EPA/play difference
- Defensive EPA allowed/play difference
- Last-3-game offensive EPA/play difference
- Last-3-game defensive EPA allowed/play difference

Training seasons:
- 2018–2024

Testing season:
- 2025

Previous best accuracy: 62.46%

EPA feature model accuracy: 61.40%

Result:
- To be updated after reviewing the model output.

## Model Comparison Test

This test compared multiple model types using the expanded 2018–2025 dataset.

Training seasons:
- 2018–2024

Testing season:
- 2025

Models tested:
- Logistic Regression
- Random Forest
- Gradient Boosting

Previous best accuracy: 62.46%

Results:
- Logistic Regression: 62.46%
- Random Forest: 60.70%
- Gradient Boosting: 56.49%

Best model:
- Logistic Regression

Result:
- To be updated after reviewing model comparison results.

## Model Training Script

After comparing model types, the project moved the best model into a reusable Python script.

Script created:
- `src/train_model.py`

Purpose:
- Load the expanded modeling dataset
- Train Logistic Regression on 2018–2024
- Test on 2025
- Print model accuracy
- Save prediction results

Current best model:
- Logistic Regression

Current best accuracy:
- 62.46%

This script is an important step toward making the forecasting process repeatable for the dashboard.

## Elo Feature Test

This test added Elo rating features to the model.

New features included:

- Home team pre-game Elo rating
- Away team pre-game Elo rating
- Elo difference
- Elo difference with home-field advantage
- Elo-based home win probability

Elo settings:
- Base Elo: 1500
- K-factor: 20
- Home-field advantage: 55 Elo points

Training seasons:
- 2018–2024

Testing season:
- 2025

Previous best accuracy: 62.46%

Elo feature model accuracy: 63.51%

Result:
- To be updated after reviewing the model output.

## Updated Training Script with Elo

After the Elo feature test improved accuracy to 63.51%, the reusable training script was updated.

Updated script:
- `src/train_model.py`

Changes:
- Uses `modeling_dataset_elo_2018_2025.csv`
- Includes Elo difference features
- Trains Logistic Regression on 2018–2024
- Tests on 2025
- Saves updated predictions to `data/predictions/best_logistic_regression_predictions.csv`

Current best model:
- Logistic Regression with Elo features

Current best accuracy:
- 63.51%

## Reusable Elo Script

The Elo feature logic was moved into a reusable Python script.

Script created:
- `src/elo.py`

Functions included:
- `expected_home_win_prob()`
- `create_elo_features()`
- `get_latest_elos()`

Purpose:
- Make Elo calculations reusable outside of notebooks
- Improve project organization
- Prepare the project for a cleaner data and modeling pipeline

## Training Script Refactor

The model training script was refactored to use the reusable Elo script.

Updated script:
- `src/train_model.py`

Change made:
- The script now imports `create_elo_features()` from `src/elo.py`
- Elo features are rebuilt during model training
- The script no longer depends only on a notebook-created Elo modeling dataset

Purpose:
- Make the pipeline more reproducible
- Keep Elo logic in one reusable file
- Make future data updates easier
