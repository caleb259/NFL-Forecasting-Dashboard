# Scoring carryover experiment

## Change

Blend previous-season scoring averages with current-season results.
Previous-season information receives the weight of four games.

Apply the same scoring calculation in historical training and upcoming
forecasts. Align upcoming recent-form, win-percentage, and
strength-of-schedule inputs with historical definitions.

Tied games remain in feature history but are excluded from winner
classifier training and evaluation.

## Development evaluation

Expanding training windows tested on 2021–2024, covering 1,136 non-tied
games. Compared carryover weights 0, 2, 4, and 8.

| Approach | Accuracy | Brier score | Log loss |
|---|---:|---:|---:|
| Original features | 63.29% | 0.2279 | 0.6493 |
| Carryover weight 4 | 63.91% | 0.2247 | 0.6415 |

Weight 4 was selected provisionally. Weight 2 performed similarly.

## Follow-up evaluation

2025 had already been inspected before this experiment and is not an
untouched holdout. Weight 4 was fixed before this follow-up comparison.

| Approach | Accuracy | Brier score | Log loss |
|---|---:|---:|---:|
| Original features | 64.08% | 0.2286 | 0.6494 |
| Carryover weight 4 | 64.79% | 0.2254 | 0.6410 |

Evaluated 284 non-tied games. Carryover produced two additional correct
picks. These results support a modest improvement, not a proven optimum.

## Verification

- Seven targeted carryover checks passed.
- Six synthetic training/upcoming feature comparisons passed.
- Eight real-game comparisons passed across all 13 model inputs.
- A dry run generated 272 forecasts without saving forecast outputs.

## Limitations

- No injury, quarterback, roster, or coaching inputs.
- Previous-season averages include playoff games.
- No prior-season history is available for the initial 2018 data.
- Margin-model performance has not been reevaluated.
- Historical evaluation freezes model coefficients for each test season;
  the live script retrains on all available completed games.