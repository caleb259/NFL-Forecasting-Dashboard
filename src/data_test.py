import nfl_data_py as nfl

# Test loading schedule data
seasons = [2023, 2024, 2025]

schedules = nfl.import_schedules(seasons)

print("Schedule data loaded successfully!")
print("Rows:", schedules.shape[0])
print("Columns:", schedules.shape[1])
print(schedules.head())
print(schedules.columns)
