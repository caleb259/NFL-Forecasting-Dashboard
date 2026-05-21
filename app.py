import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Fourth & Forecast",
    page_icon="🏈",
    layout="wide"
)


@st.cache_data
def load_predictions():
    """Load saved model predictions."""
    filepath = "data/predictions/best_logistic_regression_predictions.csv"
    return pd.read_csv(filepath)


st.title("🏈 Fourth & Forecast")
st.subheader("An Explainable NFL Game Prediction Dashboard")

st.write(
    "This dashboard uses NFL team data and machine learning to predict game outcomes. "
    "The current version uses a Logistic Regression model trained on the 2018–2024 seasons "
    "and tested on the 2025 season."
)

st.divider()

# Load predictions
try:
    predictions = load_predictions()

    # Summary metrics
    accuracy = predictions["correct_prediction"].mean()
    total_games = len(predictions)
    correct_predictions = predictions["correct_prediction"].sum()
    incorrect_predictions = total_games - correct_predictions

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Model Accuracy", f"{accuracy:.2%}")
    col2.metric("Games Tested", total_games)
    col3.metric("Correct Picks", int(correct_predictions))
    col4.metric("Incorrect Picks", int(incorrect_predictions))

    st.divider()

    st.header("2025 Game Predictions")

    # Week selector
    weeks = sorted(predictions["week"].unique())

    selected_week = st.selectbox(
        "Select a week",
        weeks
    )

    week_predictions = predictions[predictions["week"] == selected_week].copy()

    # Format probability
    week_predictions["home_win_probability_percent"] = (
        week_predictions["home_win_probability"] * 100
    ).round(1)

    week_predictions["result"] = week_predictions["correct_prediction"].apply(
        lambda x: "Correct" if x else "Incorrect"
    )

    display_columns = [
        "week",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "predicted_winner",
        "actual_winner",
        "home_win_probability_percent",
        "result"
    ]

    st.dataframe(
        week_predictions[display_columns],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Home win probability represents the model's estimated chance that the home team wins."
    )

    st.divider()

    st.header("Model Details")

    st.write(
        "Current best model: **Logistic Regression**"
    )

    st.write(
        "Training seasons: **2018–2024**"
    )

    st.write(
        "Testing season: **2025**"
    )

    st.write(
        "Current features include season-long and recent-form differences between the home and away teams."
    )

    feature_list = [
        "Average points scored difference",
        "Average points allowed difference",
        "Average point differential difference",
        "Win percentage difference",
        "Last 3 games average points scored difference",
        "Last 3 games average points allowed difference",
        "Last 3 games average point differential difference",
        "Last 3 games win percentage difference"
    ]

    st.markdown("### Features Used")

    for feature in feature_list:
        st.markdown(f"- {feature}")

except FileNotFoundError:
    st.error(
        "Prediction file not found. Run `python src/train_model.py` first to create the predictions file."
    )