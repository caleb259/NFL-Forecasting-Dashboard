# Data Dictionary
## Temporary

This document will define the main data fields used in the NFL forecasting project.

## Game-Level Fields

| Column | Description |
|---|---|
| season | NFL season |
| week | NFL week number |
| home_team | Home team abbreviation |
| away_team | Away team abbreviation |
| home_score | Points scored by the home team |
| away_score | Points scored by the away team |
| home_team_won | Target variable: 1 if the home team won, 0 otherwise |

## Feature Fields

These fields will be added during feature engineering.

| Column | Description |
|---|---|
| home_offensive_rating | Pregame offensive rating for the home team |
| away_offensive_rating | Pregame offensive rating for the away team |
| home_defensive_rating | Pregame defensive rating for the home team |
| away_defensive_rating | Pregame defensive rating for the away team |
| home_recent_point_diff | Recent point differential for the home team |
| away_recent_point_diff | Recent point differential for the away team |
| home_turnover_diff | Pregame turnover differential for the home team |
| away_turnover_diff | Pregame turnover differential for the away team |
