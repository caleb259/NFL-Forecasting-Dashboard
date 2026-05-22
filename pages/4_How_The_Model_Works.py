import streamlit as st
import sys
sys.path.append("src")

from style import apply_global_styles, page_header, section_header


st.set_page_config(
    page_title="How the Model Works",
    page_icon="🧠",
    layout="wide"
)


page_header(
    title="How the Model Works",
    icon="🧠",
    subtitle="This page explains how the NFL forecasting model works, what data it uses, how predictions are created, and what the current limitations are."
)

st.divider()

st.header("Project Goal")

st.write(
    "The goal of Fourth & Forecast is to predict NFL game outcomes using team-level data "
    "and machine learning. The dashboard is designed to show not only who the model predicts "
    "to win, but also what information the forecast is based on."
)

st.info(
    "Current best model: Logistic Regression with Elo and strength of schedule features | Accuracy: 63.86%"
)

st.divider()

st.header("Data Used")

st.write(
    "The project uses NFL schedule, score, and game-level data from the nflverse ecosystem "
    "through the `nfl_data_py` Python package."
)

st.write(
    "The current model uses games from the 2018 through 2025 seasons."
)

st.markdown(
    """
    **Training data:** 2018–2024 games  
    **Testing data:** 2025 games  
    **Prediction target:** whether the home team wins
    """
)

st.divider()

st.header("Avoiding Data Leakage")

st.write(
    "One of the most important parts of this project is avoiding data leakage. "
    "Data leakage happens when a model accidentally uses information that would not have been known "
    "at the time of prediction."
)

st.write(
    "For example, when predicting a Week 6 game, the model should only use information from Weeks 1–5. "
    "It should not use full-season averages because those would include future games."
)

st.success(
    "To avoid this, the project creates pre-game features using only games that happened before each matchup."
)

st.divider()

st.header("Features Used by the Model")

st.write(
    "The model uses difference features. This means most features compare the home team to the away team."
)

st.markdown(
    """
    For example:

    `avg_points_scored_diff = home team average points scored before the game - away team average points scored before the game`

    Positive values usually favor the home team. Negative values usually favor the away team.
    """
)

st.subheader("Season-Long Pregame Features")

st.markdown(
    """
    - Average points scored difference
    - Average points allowed difference
    - Average point differential difference
    - Win percentage difference
    """
)

st.subheader("Recent-Form Features")

st.markdown(
    """
    - Last 3 games average points scored difference
    - Last 3 games average points allowed difference
    - Last 3 games average point differential difference
    - Last 3 games win percentage difference
    """
)

st.subheader("Elo Features")

st.markdown(
    """
    - Elo rating difference
    - Elo difference with home-field advantage
    - Elo-based home win probability
    """
)

st.subheader("Strength of Schedule Features")

st.markdown(
    """
    - Strength of schedule difference
    - Current opponent win percentage difference
    """
)

st.divider()

st.header("What Elo Means")

st.write(
    "Elo is a team-strength rating system. Every team starts with a rating, and that rating changes after each game. "
    "Teams gain Elo points when they win and lose Elo points when they lose."
)

st.write(
    "The size of the Elo change depends on how expected or surprising the result was. "
    "If a strong team beats a weak team, the rating change is small. If a weak team upsets a strong team, "
    "the rating change is larger."
)

st.markdown(
    """
    **Current Elo settings:**

    - Base Elo: 1500
    - K-factor: 20
    - Home-field advantage: 55 Elo points
    """
)

st.write(
    "Elo improved the model because it gives the forecast a running measure of team strength over time."
)

st.divider()

st.header("What Strength of Schedule Means")

st.write(
    "Strength of schedule estimates how difficult a team's previous opponents were. "
    "A team with strong results against difficult opponents may be more impressive than a team with similar results against weaker opponents."
)

st.write(
    "In this project, strength of schedule is based on the average pregame win percentage of a team's previous opponents."
)

st.divider()

st.header("Model Type")

st.write(
    "The current best model is Logistic Regression."
)

st.write(
    "Logistic Regression is a good first model for this project because it is simple, explainable, "
    "and produces win probabilities."
)

st.markdown(
    """
    The model outputs a probability that the home team wins.

    - If the probability is above 50%, the model predicts the home team.
    - If the probability is below 50%, the model predicts the away team.
    """
)

st.divider()

st.header("How Upcoming Forecasts Work")

st.write(
    "The dashboard now includes forecasts for the upcoming 2026 NFL season. "
    "These forecasts are created using the released 2026 schedule and the model trained on completed historical games."
)

st.write(
    "For upcoming games, the model does not know the final score yet. Instead, it uses pregame information such as "
    "team strength, recent performance, Elo ratings, and strength of schedule to estimate the most likely winner."
)

st.markdown(
    """
    The upcoming forecast process works like this:

    1. Load completed historical NFL games.
    2. Load the upcoming 2026 schedule.
    3. Train the current best model using completed games.
    4. Create pregame features for each upcoming matchup.
    5. Predict the winner and win probability for each game.
    6. Save the predictions for the dashboard.
    """
)

st.info(
    "Before the 2026 season begins, the forecasts are preseason-style predictions. "
    "They rely mostly on carried-forward team strength from previous seasons."
)

st.divider()

st.header("How Predicted Margin Works")

st.write(
    "In addition to predicting the winner, the project now estimates a predicted margin of victory for each upcoming game."
)

st.write(
    "The win/loss model predicts which team is more likely to win. A separate regression model estimates the expected home team point differential."
)

st.markdown(
    """
    The margin model predicts:

    ```text
    home_point_diff = home_score - away_score
    ```

    Examples:

    - A predicted margin of `+4.5` means the home team is projected to win by about 4.5 points.
    - A predicted margin of `-3.0` means the away team is projected to win by about 3 points.
    """
)

st.write(
    "This margin is not meant to be a guaranteed score prediction. It is an estimate based on the same team-level features used by the forecasting model."
)

st.divider()

st.header("How Projected Records Work")

st.write(
    "The Upcoming Forecasts page also creates projected team records for the 2026 season."
)

st.write(
    "There are two ways to summarize projected records: hard projected records and expected records."
)

st.subheader("Projected Record")

st.write(
    "Projected record uses the model's predicted winner for each game. "
    "If the model predicts a team to win, that team receives one projected win."
)

st.subheader("Expected Record")

st.write(
    "Expected record uses win probabilities instead of hard picks. "
    "For example, if a team has a 60% chance to win a game, it receives 0.60 expected wins and 0.40 expected losses."
)

st.markdown(
    """
    Example:

    ```text
    Team A win probability = 60%
    Team B win probability = 40%

    Team A gets 0.60 expected wins
    Team B gets 0.40 expected wins
    ```
    """
)

st.write(
    "Expected records are useful because they account for uncertainty. "
    "A team with several close 51% predictions may have a similar projected record to a team with several strong 70% predictions, "
    "but their expected records will show the difference in confidence."
)

st.divider()

st.header("Model Accuracy")

st.write(
    "The current best model reached 63.86% accuracy when trained on the 2018–2024 seasons "
    "and tested on the 2025 season."
)

st.markdown(
    """
    **Model accuracy history:**

    | Model Version | Accuracy |
    |---|---:|
    | Baseline random split | 59.35% |
    | Season-based split | 61.40% |
    | Recent-form features | 61.40% |
    | Expanded training data | 62.46% |
    | EPA features | 61.40% |
    | Model comparison best | 62.46% |
    | Elo features | 63.86% |
    | Strength of schedule features | 63.86% |
    """
)

st.success(
    "The strength of schedule feature model is currently the best-performing version."
)

st.divider()

st.header("How to Interpret Win Probability")

st.write(
    "A win probability is not a guarantee. It is the model's estimate of how likely a team is to win "
    "based on the features it has been given."
)

st.markdown(
    """
    Example:

    - Home win probability = 65%
    - This means the model thinks the home team is more likely to win.
    - It does not mean the home team will always win.
    """
)

st.write(
    "NFL games are difficult to predict because injuries, turnovers, weather, coaching decisions, "
    "and random game events can strongly affect outcomes."
)

st.divider()

st.header("Current Limitations")

st.write(
    "The model is useful, but it is still an early version. Some important limitations remain."
)

st.markdown(
    """
    - The model does not currently include player injuries.
    - The model does not currently include weather.
    - The model does not currently include betting market information.
    - The model does not currently predict final score.
    - The model does not currently predict point spread.
    - The model uses team-level data instead of player-level data.
    - The upcoming forecast page currently uses preseason-style 2026 predictions until games are completed.
    - Predicted margin is estimated with a basic regression model and should not be treated as a betting line.
    - During the season, forecasts need to be refreshed by rerunning the update script after new games are completed.
    """
)

st.divider()

st.header("Future Improvements")

st.write(
    "This project is designed to keep improving over time."
)

st.markdown(
    """
    Planned improvements include:

    - Predicting upcoming games for the next NFL season
    - Adding automated weekly data updates
    - Adding stronger EPA and success-rate features
    - Adding injury data
    - Adding weather data
    - Adding betting spread comparison
    - Predicting point margin
    - Adding team logos and better visual design
    - Deploying the dashboard publicly
    - Automate weekly forecast updates during the season
    - Improve the predicted margin model
    - Add projected standings by division and conference
    """
)

st.divider()

st.header("Summary")

st.write(
    "Fourth & Forecast currently uses Logistic Regression with scoring, recent-form, and Elo features "
    "to predict NFL game outcomes. The model is trained on past seasons and tested on a later season "
    "to make the evaluation more realistic."
)

st.write(
    "The project will continue improving by adding better data, stronger features, and a more polished dashboard experience."
)