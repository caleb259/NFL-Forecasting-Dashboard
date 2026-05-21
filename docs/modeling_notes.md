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
