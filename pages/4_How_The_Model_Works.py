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
    - The current dashboard is based on completed 2025 test games, not live future games yet.
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