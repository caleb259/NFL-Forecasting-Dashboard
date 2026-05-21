import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Team Dashboard",
    page_icon="🏟️",
    layout="wide"
)


@st.cache_data
def load_predictions():
    """Load saved model predictions."""
    filepath = "data/predictions/best_logistic_regression_predictions.csv"
    return pd.read_csv(filepath)


st.title("🏟️ Team Dashboard")
st.write(
    "Select a team to view its 2025 games, model predictions, and team-level prediction performance."
)

try:
    predictions = load_predictions()

    teams = sorted(
        set(predictions["home_team"].unique()).union(
            set(predictions["away_team"].unique())
        )
    )

    selected_team = st.selectbox(
        "Select a team",
        teams
    )

    team_games = predictions[
        (predictions["home_team"] == selected_team) |
        (predictions["away_team"] == selected_team)
    ].copy()

    team_games = team_games.sort_values("week").reset_index(drop=True)

    # Add team-specific columns
    team_games["team_score"] = team_games.apply(
        lambda row: row["home_score"]
        if row["home_team"] == selected_team
        else row["away_score"],
        axis=1
    )

    team_games["opponent_score"] = team_games.apply(
        lambda row: row["away_score"]
        if row["home_team"] == selected_team
        else row["home_score"],
        axis=1
    )

    team_games["opponent"] = team_games.apply(
        lambda row: row["away_team"]
        if row["home_team"] == selected_team
        else row["home_team"],
        axis=1
    )

    team_games["location"] = team_games.apply(
        lambda row: "Home"
        if row["home_team"] == selected_team
        else "Away",
        axis=1
    )

    team_games["team_won"] = team_games["actual_winner"] == selected_team

    team_games["model_picked_team"] = (
        team_games["predicted_winner"] == selected_team
    )

    team_games["team_prediction_correct"] = (
        team_games["predicted_winner"] == team_games["actual_winner"]
    )

    team_games["team_win_probability"] = team_games.apply(
        lambda row: row["home_win_probability"]
        if row["home_team"] == selected_team
        else 1 - row["home_win_probability"],
        axis=1
    )

    team_games["team_win_probability_percent"] = (
        team_games["team_win_probability"] * 100
    ).round(1)

    wins = team_games["team_won"].sum()
    losses = len(team_games) - wins

    model_accuracy_for_team_games = team_games[
        "team_prediction_correct"
    ].mean()

    model_picked_team_count = team_games["model_picked_team"].sum()

    avg_team_win_probability = team_games[
        "team_win_probability"
    ].mean()

    st.divider()

    st.header(f"{selected_team} Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Record", f"{int(wins)}-{int(losses)}")
    col2.metric(
        "Model Accuracy in Team Games",
        f"{model_accuracy_for_team_games:.2%}"
    )
    col3.metric(
        "Times Model Picked Team",
        int(model_picked_team_count)
    )
    col4.metric(
        "Avg Team Win Probability",
        f"{avg_team_win_probability:.2%}"
    )

    st.divider()

    st.header("Game-by-Game Results")

    team_games["game_result"] = team_games["team_won"].apply(
        lambda x: "Win" if x else "Loss"
    )

    team_games["prediction_result"] = team_games[
        "team_prediction_correct"
    ].apply(lambda x: "Correct" if x else "Incorrect")

    display_columns = [
        "week",
        "location",
        "opponent",
        "team_score",
        "opponent_score",
        "game_result",
        "predicted_winner",
        "actual_winner",
        "team_win_probability_percent",
        "prediction_result"
    ]

    st.dataframe(
        team_games[display_columns],
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Team win probability is adjusted based on whether the selected team was home or away."
    )

    st.divider()

    st.header("Team Game Cards")

    for _, row in team_games.iterrows():
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                if row["location"] == "Home":
                    matchup = f"{row['opponent']} at {selected_team}"
                else:
                    matchup = f"{selected_team} at {row['opponent']}"

                st.subheader(f"Week {int(row['week'])}: {matchup}")
                st.write(
                    f"Final Score: **{selected_team} {int(row['team_score'])} - "
                    f"{row['opponent']} {int(row['opponent_score'])}**"
                )

            with col2:
                st.write(f"Predicted Winner: **{row['predicted_winner']}**")
                st.write(f"Actual Winner: **{row['actual_winner']}**")
                st.write(
                    f"{selected_team} Win Probability: "
                    f"**{row['team_win_probability_percent']}%**"
                )

            with col3:
                if row["game_result"] == "Win":
                    st.success("Win")
                else:
                    st.error("Loss")

                if row["prediction_result"] == "Correct":
                    st.success("Prediction Correct")
                else:
                    st.error("Prediction Incorrect")

    st.divider()

    st.header("Team Win Probability by Week")

    chart_data = team_games[
        [
            "week",
            "team_win_probability_percent"
        ]
    ].copy()

    st.line_chart(
        chart_data,
        x="week",
        y="team_win_probability_percent"
    )

except FileNotFoundError:
    st.error(
        "Prediction file not found. Run `python src/train_model.py` first to create the predictions file."
    )