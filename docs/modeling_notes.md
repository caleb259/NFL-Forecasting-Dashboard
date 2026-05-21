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

