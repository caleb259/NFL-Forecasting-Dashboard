# QB passing-rating experiment

## Question

Does adding the expected starting quarterbacks' historical passing-rating
difference improve the existing winner model?

## Feature

For each team, select the rank-one quarterback from the latest depth-chart
snapshot collected before the forecast cutoff.

Calculate historical adjusted net yards per attempt (ANY/A):

(passing yards + 20 × passing TDs − 45 × interceptions + signed sack yards)
÷ (attempts + sacks)

The source stores sack yards as negative values.

Use available 2023–2025 history, excluding games on or after the forecast
cutoff's Eastern calendar date. Shrink each player's rating toward the
league average using a fixed prior weight of 100 attempts plus sacks.
Calculate the league average using the same date restriction.

The model feature is home adjusted ANY/A minus away adjusted ANY/A.
A player without history receives the league-average fallback.

## Validation

- Four synthetic checks passed for sack losses, zero history,
  shrinkage, and exclusion of cutoff-day and future statistics.
- QB feature coverage: 285 games at each of two forecast cutoffs.
- All 13 existing team features matched cutoff-restricted
  reconstructions for all 285 games at the 24-hour horizon.

These checks validate the implemented calendar-date rule.
They do not verify historical publication or revision timestamps.

## Prediction experiment

- Forecast horizon: 24 hours before kickoff.
- Initial classifier training: 2025 Weeks 1–8.
- Test period: Week 9 onward, including postseason.
- Retrain each week using earlier 2025 weeks and results dated before
  that week's earliest forecast cutoff.
- Both approaches use identical training and evaluation games.
- Logistic regression with the existing settings.
- Baseline: existing 13 features, scoring carryover weight 4.
- Challenger: baseline features plus QB rating difference.
- Ties remain in historical features but are excluded from classifier
  training and evaluation.
- Earlier seasons supply feature history, not classifier training rows
  in this experiment.

## Results

| Approach | Games | Accuracy | Brier score | Log loss |
|---|---:|---:|---:|---:|
| Existing features | 164 | 62.80% | 0.2223 | 0.6362 |
| Existing features + QB | 164 | 63.41% | 0.2228 | 0.6378 |

Three winner picks changed:
- Two incorrect picks became correct.
- One correct pick became incorrect.

The QB coefficient was negative in Weeks 9–11, nearly zero in Week 12,
and positive afterward. This indicates an unstable early conditional
relationship; it does not establish that weaker QB play improves outcomes.

## Decision

No demonstrated improvement. Keep production forecasts unchanged.

The challenger gained one correct pick but slightly worsened both
probability metrics. This is a small exploratory comparison on a season
already examined during development, not an untouched final test.

## Next hypothesis

An expected quarterback's rating relative to the quarterback play
represented in the team's recent results may add more useful information
than an absolute home-versus-away QB rating difference.

Investigate coverage and behavior before fitting another model.
Do not choose settings based on which values improve these inspected games.