import os
import nfl_data_py as nfl

# Load schedule data for recent NFL seasons
seasons = [2023, 2024, 2025]

schedules = nfl.import_schedules(seasons)

# Make sure the raw data folder exists
os.makedirs("data/raw", exist_ok=True)

# Save the schedule data
schedules.to_csv("data/raw/schedules_2023_2025.csv", index=False)

print("Schedule data loaded and saved successfully!")
print("Rows:", schedules.shape[0])
print("Columns:", schedules.shape[1])
print()
print("First 5 rows:")
print(schedules.head())
print()
print("Column names:")
print(schedules.columns.tolist())
