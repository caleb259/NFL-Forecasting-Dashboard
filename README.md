# NFL-Forecasting-Dashboard

## Project Overview

Fourth & Forecast is a data science and sports analytics project focused on predicting NFL game outcomes. The goal of this project is to build an interactive web dashboard that forecasts upcoming NFL games and explains the main factors behind each prediction.

The dashboard will use historical and current NFL team data to predict game winners, estimate win probabilities, and show users how the forecast was calculated. As the NFL season progresses, the data will be updated so the model can continue making predictions based on the most recent team performance.

## Project Goals

The main goals of this project are to:

* Build a machine learning model that predicts NFL game outcomes
* Create an interactive dashboard for viewing weekly predictions
* Show win probabilities for upcoming games
* Explain which statistics influence each prediction
* Track model accuracy throughout the season
* Document the full project process from planning to deployment

## Why This Project Matters

This project is designed to combine data science, machine learning, dashboard design, and sports analytics into one complete portfolio project. Instead of only showing final predictions, the dashboard will also help users understand why a team is projected to win.

The project is also meant to be updated throughout the season, making it a living project rather than a one-time analysis.

## Planned Features

### Weekly Forecasts

Users will be able to select an NFL week and view predictions for each game.

Planned information includes:

* Matchup
* Predicted winner
* Win probability
* Confidence level
* Projected point margin, if added later

### Game Breakdown

Each matchup will include a more detailed explanation of the prediction.

Possible details include:

* Offensive comparison
* Defensive comparison
* Recent team performance
* Turnover difference
* Home-field advantage
* Key factors that influenced the forecast

### Team Dashboard

Users will be able to select a team and view team-level performance trends.

Possible details include:

* Team record
* Offensive rating
* Defensive rating
* Recent performance
* Upcoming schedule
* Forecasted win probabilities

### Model Performance

The dashboard will include a page that tracks how well the model is performing.

Possible metrics include:

* Overall prediction accuracy
* Accuracy by week
* Accuracy by confidence level
* Biggest correct predictions
* Biggest misses

## Data Sources

The project will likely use NFL data from the nflverse ecosystem through the `nfl_data_py` Python package.

Potential data sources include:

* Historical NFL schedules and scores
* Weekly team statistics
* Play-by-play data
* Team offensive and defensive statistics
* EPA/play statistics
* Current-season game results

Additional data sources may be added later, such as injury data, betting lines, or weather data.

## Modeling Approach

The first version of the model will focus on predicting whether the home team wins a game.

The first model will likely use logistic regression because it is simple, explainable, and provides win probabilities.

Possible features include:

* Difference in offensive performance between teams
* Difference in defensive performance between teams
* Recent point differential
* Turnover differential
* Home-field advantage
* Team strength ratings
* Rolling averages from previous games

A major focus of the project will be avoiding data leakage. This means the model should only use information that would have been available before each game was played.

## Technology Stack

Planned tools:

| Area             | Tool                                |
| ---------------- | ----------------------------------- |
| Programming      | Python                              |
| Data Cleaning    | pandas                              |
| NFL Data         | nfl_data_py                         |
| Machine Learning | scikit-learn                        |
| Dashboard        | Streamlit                           |
| Charts           | Plotly or Altair                    |
| Version Control  | Git and GitHub                      |
| Deployment       | Streamlit Community Cloud or Render |

## Planned Repository Structure

```text
nfl-forecast-dashboard/
│
├── README.md
├── requirements.txt
├── app.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── predictions/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_engineering.ipynb
│   └── 03_model_testing.ipynb
│
├── src/
│   ├── data_loader.py
│   ├── feature_engineering.py
│   ├── model.py
│   ├── predict.py
│   └── evaluation.py
│
├── pages/
│   ├── 1_Game_Breakdown.py
│   ├── 2_Team_Dashboard.py
│   └── 3_Model_Performance.py
│
└── docs/
    ├── project_plan.md
    ├── data_dictionary.md
    ├── modeling_notes.md
    └── update_log.md
```

## Project Phases

### Phase 1: Planning and Setup

* Create the GitHub repository
* Write the project README
* Create the project folder structure
* Document the project plan

### Phase 2: Data Collection

* Load NFL data using `nfl_data_py`
* Explore available data fields
* Save raw data files
* Begin documenting the data sources

### Phase 3: Feature Engineering

* Create one row per game
* Build pre-game team statistics
* Create rolling averages
* Add home/away features
* Create the model target variable

### Phase 4: Modeling

* Train a baseline model
* Predict game winners
* Generate win probabilities
* Evaluate model accuracy
* Save predictions

### Phase 5: Dashboard Development

* Build the Streamlit dashboard
* Add weekly prediction views
* Add game breakdown pages
* Add team dashboard pages
* Add model performance tracking

### Phase 6: Season Updates

* Update data during the season
* Re-run predictions weekly
* Track model performance
* Improve the model over time

## Current Status

This project is currently in the planning and setup stage.

## Future Improvements

Possible future improvements include:

* Adding Elo ratings
* Adding injury data
* Adding betting spread comparison
* Predicting final scores
* Predicting point spreads
* Adding automated weekly updates
* Deploying the dashboard publicly
* Improving the visual design of the dashboard

## Author

Created by Caleb Linsenbardt.
