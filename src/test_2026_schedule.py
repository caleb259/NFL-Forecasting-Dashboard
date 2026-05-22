import nfl_data_py as nfl

schedules_2026 = nfl.import_schedules([2026])

print("Rows:", schedules_2026.shape[0])
print("Columns:", schedules_2026.shape[1])

print(
    schedules_2026[
        [
            "season",
            "week",
            "gameday",
            "weekday",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
        ]
    ].head(20)
)

schedules_2026.to_csv("data/raw/schedules_2026.csv", index=False)