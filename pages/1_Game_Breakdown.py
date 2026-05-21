import pandas as pd
import streamlit as st
import sys

sys.path.append("src")

from team_info import get_team_logo, get_team_name, get_team_primary_color


st.set_page_config(
    page_title="Game Breakdown",
    page_icon="🏈",
    layout="wide"
)


@st.cache_data
def load_predictions():
    """Load saved model predictions."""
    filepath = "data/predictions/best_logistic_regression_predictions.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_modeling_data():
    """Load modeling dataset with feature values."""
    filepath = "data/processed/modeling_dataset_expanded_2018_2025.csv"
    return pd.read_csv(filepath)


st.title("🏈 Game Breakdown")
st.write(
    "Select a specific game to view the model prediction, final result, and feature values used by the model."
)

try:
    predictions = load_predictions()
    modeling_data = load_modeling_data()

    # Merge prediction results with model feature values
    game_data = predictions.merge(
        modeling_data,
        on=[
            "season",
            "week",
            "game_id",
            "gameday",
            "home_team",
            "away_team",
            "home_score",
            "away_score",
            "home_team_won"
        ],
        how="left",
        suffixes=("", "_model")
    )

    st.divider()

    # Week selector
    weeks = sorted(game_data["week"].unique())

    selected_week = st.selectbox(
        "Select a week",
        weeks
    )

    week_games = game_data[game_data["week"] == selected_week].copy()

    week_games["matchup"] = (
        week_games["away_team"] + " at " + week_games["home_team"]
    )

    selected_matchup = st.selectbox(
        "Select a game",
        week_games["matchup"].tolist()
    )

    selected_game = week_games[
        week_games["matchup"] == selected_matchup
    ].iloc[0]

    st.divider()

    st.header(selected_matchup)

    home_team = selected_game["home_team"]
    away_team = selected_game["away_team"]

    home_logo = get_team_logo(home_team)
    away_logo = get_team_logo(away_team)

    home_name = get_team_name(home_team)
    away_name = get_team_name(away_team)

    home_color = get_team_primary_color(home_team)

    prediction_result = (
        "Correct" if selected_game["correct_prediction"] else "Incorrect"
    )

    home_win_probability_percent = (
        selected_game["home_win_probability"] * 100
    )

    away_win_probability_percent = 100 - home_win_probability_percent

    st.markdown(
        f"""
        <div style="
            border-left: 10px solid {home_color};
            padding-left: 16px;
            margin-bottom: 20px;
        ">
            <h2 style="margin-bottom: 0;">{away_team} at {home_team}</h2>
            <p style="margin-top: 4px; color: #666;">
                {away_name} at {home_name}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    logo_col1, logo_col2, logo_col3 = st.columns([2, 1, 2])

    with logo_col1:
        if away_logo:
            st.image(away_logo, width=110)
        st.subheader(away_team)
        st.write(away_name)

    with logo_col2:
        st.markdown(
            "<h2 style='text-align: center; margin-top: 40px;'>VS</h2>",
            unsafe_allow_html=True
        )

    with logo_col3:
        if home_logo:
            st.image(home_logo, width=110)
        st.subheader(home_team)
        st.write(home_name)

    st.divider()

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Predicted Winner",
        selected_game["predicted_winner"]
    )

    col2.metric(
        "Actual Winner",
        selected_game["actual_winner"]
    )

    col3.metric(
        "Home Win Probability",
        f"{home_win_probability_percent:.1f}%"
    )

    col4.metric(
        "Prediction Result",
        prediction_result
    )

    st.divider()

    st.header("Final Score")

    score_col1, score_col2 = st.columns(2)

    with score_col1:
        st.metric(
            f"{away_team} Score",
            int(selected_game["away_score"])
        )
        st.caption(away_name)

    with score_col2:
        st.metric(
            f"{home_team} Score",
            int(selected_game["home_score"])
        )
        st.caption(home_name)

    st.divider()

    st.header("Win Probability")

    probability_table = pd.DataFrame(
        {
            "Team": [
                selected_game["away_team"],
                selected_game["home_team"]
            ],
            "Win Probability": [
                away_win_probability_percent,
                home_win_probability_percent
            ]
        }
    )

    st.dataframe(
        probability_table,
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(
        probability_table,
        x="Team",
        y="Win Probability"
    )

    st.divider()

    st.header("Model Feature Breakdown")

    st.write(
        "These values compare the home team to the away team before the game was played. "
        "Positive values favor the home team, while negative values favor the away team."
    )

    feature_rows = [
        {
            "Feature": "Average points scored difference",
            "Value": selected_game["avg_points_scored_diff"],
            "Explanation": "Home team's pregame average points scored minus away team's pregame average points scored."
        },
        {
            "Feature": "Average points allowed difference",
            "Value": selected_game["avg_points_allowed_diff"],
            "Explanation": "Home team's pregame average points allowed minus away team's pregame average points allowed."
        },
        {
            "Feature": "Average point differential difference",
            "Value": selected_game["avg_point_diff_diff"],
            "Explanation": "Home team's pregame average point differential minus away team's pregame average point differential."
        },
        {
            "Feature": "Win percentage difference",
            "Value": selected_game["win_pct_diff"],
            "Explanation": "Home team's pregame win percentage minus away team's pregame win percentage."
        },
        {
            "Feature": "Last 3 games points scored difference",
            "Value": selected_game["last3_avg_points_scored_diff"],
            "Explanation": "Home team's recent scoring average minus away team's recent scoring average."
        },
        {
            "Feature": "Last 3 games points allowed difference",
            "Value": selected_game["last3_avg_points_allowed_diff"],
            "Explanation": "Home team's recent points allowed average minus away team's recent points allowed average."
        },
        {
            "Feature": "Last 3 games point differential difference",
            "Value": selected_game["last3_avg_point_diff_diff"],
            "Explanation": "Home team's recent point differential minus away team's recent point differential."
        },
        {
            "Feature": "Last 3 games win percentage difference",
            "Value": selected_game["last3_win_pct_diff"],
            "Explanation": "Home team's recent win percentage minus away team's recent win percentage."
        },
        {
            "Feature": "Elo rating difference",
            "Value": selected_game["elo_diff"],
            "Explanation": "Home team's pregame Elo rating minus away team's pregame Elo rating."
        },
        {
            "Feature": "Elo difference with home-field advantage",
            "Value": selected_game["home_elo_with_hfa_diff"],
            "Explanation": "Home team's Elo rating plus home-field advantage minus away team's Elo rating."
        },
        {
            "Feature": "Elo-based home win probability",
            "Value": selected_game["elo_home_win_prob"],
            "Explanation": "The home team's expected win probability based only on Elo ratings."
        },
        {
            "Feature": "Strength of schedule difference",
            "Value": selected_game["strength_of_schedule_diff"],
            "Explanation": "Home team's average previous opponent win percentage minus away team's average previous opponent win percentage."
        },
        {
            "Feature": "Current opponent win percentage difference",
            "Value": selected_game["current_opponent_win_pct_diff"],
            "Explanation": "Home team's current opponent pregame win percentage minus away team's current opponent pregame win percentage."
        }
    ]

    feature_breakdown = pd.DataFrame(feature_rows)

    feature_breakdown["Value"] = feature_breakdown["Value"].round(3)

    st.dataframe(
        feature_breakdown,
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(
        feature_breakdown,
        x="Feature",
        y="Value"
    )

    st.divider()

    st.header("Elo Rating Summary")

    elo_col1, elo_col2, elo_col3 = st.columns(3)

    with elo_col1:
        st.metric(
            f"{selected_game['home_team']} Pregame Elo",
            f"{selected_game['home_elo_before']:.1f}"
        )

    with elo_col2:
        st.metric(
            f"{selected_game['away_team']} Pregame Elo",
            f"{selected_game['away_elo_before']:.1f}"
        )

    with elo_col3:
        st.metric(
            "Elo Home Win Probability",
            f"{selected_game['elo_home_win_prob']:.1%}"
        )

    st.write(
        "Elo ratings estimate team strength over time. A higher Elo rating means the team has performed better based on previous results. "
        "The Elo home win probability is calculated before the game using both teams' ratings and a home-field advantage adjustment."
    )

    st.divider()

    st.header("Strength of Schedule Summary")

    sos_col1, sos_col2, sos_col3 = st.columns(3)

    with sos_col1:
        st.metric(
            f"{selected_game['home_team']} Strength of Schedule",
            f"{selected_game['home_strength_of_schedule_before']:.3f}"
        )

    with sos_col2:
        st.metric(
            f"{selected_game['away_team']} Strength of Schedule",
            f"{selected_game['away_strength_of_schedule_before']:.3f}"
        )

    with sos_col3:
        st.metric(
            "Strength of Schedule Difference",
            f"{selected_game['strength_of_schedule_diff']:.3f}"
        )

    st.write(
        "Strength of schedule estimates how strong a team's previous opponents were before the game. "
        "A higher value means the team had faced opponents with stronger pregame win percentages."
    )

    st.divider()

    st.header("How to Read This Page")

    st.write(
        "The model predicts the probability that the home team wins. "
        "If the home win probability is above 50%, the model picks the home team. "
        "If it is below 50%, the model picks the away team."
    )

    st.write(
        "The feature breakdown helps explain what information the model used. "
        "For example, a positive point differential difference means the home team had a better average point differential before the game. "
        "A positive Elo difference means the home team had a higher team-strength rating before the matchup."
    )

except FileNotFoundError:
    st.error(
        "Required data file not found. Run `python src/train_model.py` and make sure the processed modeling dataset exists."
    )