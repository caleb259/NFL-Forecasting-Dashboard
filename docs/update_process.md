# Forecast Update Process

This document explains how to refresh the Fourth & Forecast dashboard after new NFL games are completed.

The dashboard uses saved prediction files from the `data/predictions/` folder. To keep the deployed app current, the prediction files need to be regenerated and pushed to GitHub.

## Why Updates Are Needed

The Upcoming Forecasts page predicts games for the 2026 NFL season.

Before the season starts, these predictions are preseason-style forecasts based mostly on previous-season performance, Elo ratings, strength of schedule, and historical model patterns.

As the 2026 season is played, new completed games should be used to update:

- Team records
- Recent-form features
- Strength of schedule
- Elo ratings
- Predicted winners
- Win probabilities
- Predicted margins
- Projected team records

## When to Update

During the NFL season, the forecast should usually be updated after all games for a week are completed.

Recommended update time:

```text
Tuesday morning after each NFL week
```

This gives the data source time to include final scores from Monday Night Football.

Updates can also be run after major schedule or data changes.

## Main Update Command

From the main project folder, run:

```powershell
python src/predict_upcoming.py
```

This script refreshes the upcoming forecast files.

## Files Updated

Running the forecast script updates these files:

```text
data/predictions/upcoming_2026_predictions.csv
data/predictions/projected_2026_records.csv
data/predictions/forecast_metadata.json
data/processed/schedules_2026.csv
```

These files are used by the deployed Streamlit app.

## Step-by-Step Weekly Update Process

### 1. Open the project in VS Code

Open the local project folder:

```text
NFL-Forecasting-Dashboard
```

### 2. Activate the virtual environment

On Windows, run:

```powershell
.venv\Scripts\activate
```

### 3. Pull the latest GitHub changes

Before updating anything, make sure the local project is current.

```powershell
git pull
```

### 4. Run the upcoming forecast script

```powershell
python src/predict_upcoming.py
```

This will:

- Load updated NFL schedule and score data
- Separate completed games from upcoming games
- Rebuild model features
- Recalculate Elo ratings
- Train the win probability model
- Train the predicted margin model
- Generate upcoming game predictions
- Generate projected team records
- Update the forecast metadata file

### 5. Check the terminal output

The script should print messages showing that files were saved.

Look for output like:

```text
Saved upcoming predictions to data/predictions/upcoming_2026_predictions.csv
Saved projected records to data/predictions/projected_2026_records.csv
Saved forecast metadata to data/predictions/forecast_metadata.json
```

### 6. Run the app locally

Before pushing changes, test the dashboard locally.

```powershell
streamlit run Home.py
```

Check these pages:

- Home
- Upcoming Forecasts
- Model Performance
- Team Dashboard
- Game Breakdown

Make sure the app runs without file errors.

### 7. Confirm the forecast metadata updated

In the app, check:

```text
Forecast last updated
```

It should show the new update time.

You can also open:

```text
data/predictions/forecast_metadata.json
```

and confirm the `last_updated` value changed.

### 8. Check Git status

```powershell
git status
```

You should usually see changes to files like:

```text
data/predictions/upcoming_2026_predictions.csv
data/predictions/projected_2026_records.csv
data/predictions/forecast_metadata.json
data/processed/schedules_2026.csv
```

### 9. Add the updated files

```powershell
git add data/predictions/upcoming_2026_predictions.csv
git add data/predictions/projected_2026_records.csv
git add data/predictions/forecast_metadata.json
git add data/processed/schedules_2026.csv
```

Or, if other intended files changed too:

```powershell
git add .
```

### 10. Commit the update

Use a clear commit message.

Example:

```powershell
git commit -m "Update 2026 forecasts after Week 1"
```

For later weeks, change the week number:

```powershell
git commit -m "Update 2026 forecasts after Week 2"
```

### 11. Push to GitHub

```powershell
git push
```

### 12. Check the deployed Streamlit app

After pushing, Streamlit Community Cloud should automatically redeploy.

Open the live app and check:

- Forecast last updated changed
- Upcoming Forecasts page loads
- Projected records updated
- No missing file errors appear

If the deployed app does not update after a few minutes, open Streamlit Community Cloud and manually reboot or redeploy the app.

## Simple Weekly Command List

For quick reference:

```powershell
.venv\Scripts\activate
git pull
python src/predict_upcoming.py
streamlit run Home.py
git status
git add .
git commit -m "Update 2026 forecasts after Week X"
git push
```

Replace `Week X` with the correct NFL week.

## Important Notes

### The app does not update by itself

The deployed Streamlit app reads files from GitHub. It will not automatically learn from completed games unless the prediction files are regenerated and pushed.

### New scores depend on the data source

The script uses NFL schedule and score data from `nfl_data_py`. If a completed game is not updated in the data source yet, the app may still treat it as upcoming.

### Predictions should only use completed games

The forecast script should only use games with final scores as completed data. Future games should remain pending until scores are available.

### Forecasts become more current during the season

As more 2026 games are completed, the model can use current-season information such as:

- Updated Elo ratings
- Current-season records
- Recent scoring form
- Updated strength of schedule

This should make forecasts more current as the season continues.

## Future Automation Plan

Eventually, this manual update process can be automated with GitHub Actions.

A future GitHub Actions workflow could:

- Run every Tuesday morning during the NFL season
- Install project dependencies
- Run `src/predict_upcoming.py`
- Commit updated prediction files
- Push changes to GitHub
- Trigger a Streamlit redeploy

This would make the dashboard update automatically during the season.