# Project Plan

## Project Title

**Fourth & Forecast: NFL Game Prediction Dashboard**

## Project Overview

Fourth & Forecast is an NFL forecasting dashboard that predicts game outcomes using team-level statistics, Elo ratings, and machine learning.

The project is designed to be both predictive and explainable. The goal is not only to show which team is predicted to win, but also to show what information the model used to make that prediction.

The dashboard is built with Streamlit and currently includes pages for weekly predictions, game breakdowns, team-level analysis, model performance, model comparison, and a plain-English explanation of how the model works.

## Main Objective

The main objective is to build an end-to-end sports analytics project that can:

- Load and process NFL game data
- Create pre-game features without data leakage
- Train machine learning models to predict game outcomes
- Evaluate model performance honestly
- Display predictions in an interactive dashboard
- Explain the model in a way that non-technical users can understand

## Current Best Model

| Model | Training Data | Testing Data | Accuracy |
|---|---|---|---:|
| Logistic Regression with Elo features | 2018–2024 NFL seasons | 2025 NFL season | 63.51% |

## Project Motivation

This project was created to combine several important data science skills into one portfolio project:

- Data collection
- Data cleaning
- Feature engineering
- Machine learning
- Model evaluation
- Dashboard development
- GitHub documentation
- Communicating technical results clearly

NFL prediction is a useful project topic because it is interesting, challenging, and easy for many people to understand.

## Target Audience

The main audience for this project includes:

- NFL fans
- Sports analytics students
- Data science recruiters
- Professors or classmates
- People viewing the project on GitHub or a portfolio website

The dashboard should be understandable to people who do not have a technical background.

## Data Sources

The project uses NFL data from the nflverse ecosystem through the `nfl_data_py` Python package.

Current data includes:

- NFL schedules
- Game results
- Home and away teams
- Final scores
- Season and week information
- Team-level pre-game statistics
- Elo ratings created within the project

## Current Dataset

The current project uses games from the 2018 through 2025 NFL seasons.

Training seasons:

- 2018
- 2019
- 2020
- 2021
- 2022
- 2023
- 2024

Testing season:

- 2025

## Prediction Target

The current model predicts whether the home team wins.

Target variable:

```text
home_team_won
```

Where:

```text
1 = home team won
0 = home team lost
```

## Feature Groups

The current best model uses three main groups of features.

### Season-Long Pregame Features

- Average points scored difference
- Average points allowed difference
- Average point differential difference
- Win percentage difference

### Recent-Form Features

- Last 3 games average points scored difference
- Last 3 games average points allowed difference
- Last 3 games average point differential difference
- Last 3 games win percentage difference

### Elo Features

- Elo rating difference
- Elo rating difference with home-field advantage
- Elo-based home win probability

## Avoiding Data Leakage

Avoiding data leakage is one of the most important parts of the project.

When predicting a game, the model should only use information that would have been available before that game was played.

For example, when predicting a Week 6 game, the model should only use data from Weeks 1–5. It should not use full-season averages because those would include future games.

The project handles this by creating pre-game features using only previous games.

## Modeling Process

The modeling process followed these steps:

1. Load NFL schedule and results data.
2. Create a clean game-level dataset.
3. Build basic pre-game team features.
4. Train a baseline Logistic Regression model.
5. Switch from random train-test split to season-based testing.
6. Add recent-form features.
7. Expand the dataset to more seasons.
8. Test EPA features.
9. Compare multiple model types.
10. Add Elo rating features.
11. Update the training pipeline to use the best model.

## Model Accuracy History

| Model Version | Accuracy |
|---|---:|
| Baseline random split | 59.35% |
| Season-based split | 61.40% |
| Recent-form features | 61.40% |
| Expanded training data | 62.46% |
| EPA features | 61.40% |
| Model comparison best | 62.46% |
| Elo features | 63.51% |
| SOS features | 63.86% |

## Current Dashboard Pages

### Home

Shows weekly predictions, summary metrics, prediction cards, and model details.

### Game Breakdown

Allows the user to select one game and view prediction details, final result, feature values, and Elo information.

### Team Dashboard

Allows the user to select a team and view team-level prediction performance and game-by-game results.

### Model Performance

Shows overall accuracy, accuracy by week, accuracy by confidence level, and full prediction results.

### How the Model Works

Explains the data, features, model, Elo ratings, limitations, and future improvements in plain English.

### Model Comparison

Compares different modeling experiments and explains why the current best model was selected.

## Current Project Structure

```text
NFL-Forecasting-Dashboard/
│
├── Home.py
├── README.md
├── requirements.txt
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── predictions/
│
├── docs/
│   ├── project_plan.md
│   ├── data_dictionary.md
│   ├── modeling_notes.md
│   ├── update_log.md
│   └── images/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model_testing.ipynb
│   ├── 04_model_improvement.ipynb
│   ├── 05_recent_form_features.ipynb
│   ├── 06_expand_training_data.ipynb
│   ├── 07_epa_features.ipynb
│   ├── 08_compare_models.ipynb
│   └── 09_elo_features.ipynb
│
├── pages/
│   ├── 1_Game_Breakdown.py
│   ├── 2_Team_Dashboard.py
│   ├── 3_Model_Performance.py
│   ├── 4_How_The_Model_Works.py
│   └── 5_Model_Comparison.py
│
└── src/
    ├── data_loader.py
    ├── elo.py
    └── train_model.py
```

## Completed Milestones

- Created GitHub repository
- Created project folder structure
- Set up Python virtual environment
- Installed required packages
- Loaded NFL data using `nfl_data_py`
- Created data exploration notebook
- Created feature engineering notebook
- Created baseline model notebook
- Created season-based testing notebook
- Created recent-form feature notebook
- Expanded training data to 2018–2025
- Tested EPA features
- Compared multiple model types
- Added Elo features
- Improved model accuracy to 63.51%
- Created reusable training script
- Created reusable Elo script
- Created reusable data loader script
- Built Streamlit dashboard
- Added screenshots to README
- Updated README with current project information
- Created reusable feature engineering script
- Refactored model training pipeline to rebuild modeling features automatically

## Current Limitations

The project is working, but there are still several limitations:

- The model does not include player injuries.
- The model does not include weather.
- The model does not include betting market information.
- The model does not predict final score.
- The model does not predict point spread.
- The model uses team-level data instead of player-level data.
- The current dashboard evaluates completed 2025 games instead of live future games.
- Elo settings have not been tuned yet.

## Future Improvements

Planned future improvements include:

- Predict upcoming games for the next NFL season
- Add automated weekly data updates
- Add strength of schedule features
- Tune Elo settings
- Add injury data
- Add weather data
- Add betting spread comparison
- Predict point margin
- Predict final score
- Add stronger EPA and success-rate features
- Add team logos and team colors
- Improve dashboard styling
- Deploy the dashboard publicly

## Next Planned Step

The next major project improvement will likely be one of the following:

1. Create a reusable feature engineering script.
2. Add strength of schedule features.
3. Tune Elo settings.
4. Improve dashboard styling.
5. Deploy the Streamlit app publicly.
