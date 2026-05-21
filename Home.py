import pandas as pd
import streamlit as st
import sys
sys.path.append("src")

from team_info import get_team_logo, get_team_name, get_team_primary_color


st.set_page_config(
    page_title="Fourth & Forecast",
    page_icon="🏈",
    layout="wide"
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        font-size: 1.15rem;
        color: #CBD5E1;
        margin-bottom: 1.5rem;
    }

    .section-header {
        font-size: 1.6rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-top: 1.5rem;
        margin-bottom: 0.75rem;
    }

    .muted-text {
        color: #CBD5E1;
    }

    div[data-testid="stMetric"] {
        background-color: #1E293B;
        border: 1px solid #334155;
        padding: 1rem;
        border-radius: 14px;
    }

    div[data-testid="stMetric"] label {
        color: #CBD5E1;
    }

    div[data-testid="stMetric"] div {
        color: #F8FAFC;
    }
    </style>
    """,
    unsafe_allow_html=True
)


@st.cache_data
def load_predictions():
    """Load saved model predictions."""
    filepath = "data/predictions/best_logistic_regression_predictions.csv"
    return pd.read_csv(filepath)


st.markdown(
    """
    <div class="main-title">🏈 Fourth & Forecast</div>
    <div class="subtitle">
        Explainable NFL game predictions powered by team stats, Elo ratings, strength of schedule, and machine learning.
    </div>
    """,
    unsafe_allow_html=True
)

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

    st.markdown('<div class="section-header">2025 Game Predictions</div>', unsafe_allow_html=True)

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

    st.markdown("### Prediction Cards")

    for _, row in week_predictions.iterrows():
        result_text = "Correct" if row["correct_prediction"] else "Incorrect"

        home_team = row["home_team"]
        away_team = row["away_team"]

        home_logo = get_team_logo(home_team)
        away_logo = get_team_logo(away_team)

        home_name = get_team_name(home_team)
        away_name = get_team_name(away_team)

        card_color = get_team_primary_color(home_team)

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="
                    border-left: 8px solid {card_color};
                    padding-left: 12px;
                    margin-bottom: 8px;
                ">
                    <h3 style="margin-bottom: 0;">{away_team} at {home_team}</h3>
                    <p style="margin-top: 4px; color: #CBD5E1;">
                        {away_name} at {home_name}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            col1, col2, col3 = st.columns([2, 2, 1])

            with col1:
                logo_col1, logo_col2 = st.columns(2)

                with logo_col1:
                    if away_logo:
                        st.image(away_logo, width=80)
                    st.write(f"**{away_team}**")
                    st.write(f"{int(row['away_score'])} points")

                with logo_col2:
                    if home_logo:
                        st.image(home_logo, width=80)
                    st.write(f"**{home_team}**")
                    st.write(f"{int(row['home_score'])} points")

            with col2:
                st.write(f"Predicted Winner: **{row['predicted_winner']}**")
                st.write(f"Actual Winner: **{row['actual_winner']}**")
                st.write(
                    f"Home Win Probability: "
                    f"**{row['home_win_probability_percent']}%**"
                )

            with col3:
                if row["correct_prediction"]:
                    st.success(result_text)
                else:
                    st.error(result_text)

    

    st.caption(
        "Home win probability represents the model's estimated chance that the home team wins."
    )

    st.divider()

    st.markdown('<div class="section-header">Model Details</div>', unsafe_allow_html=True)

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
        "Current features include season-long differences, recent-form differences, Elo rating differences, "
        "and strength of schedule differences between the home and away teams."
    )

    feature_list = [
        "Average points scored difference",
        "Average points allowed difference",
        "Average point differential difference",
        "Win percentage difference",
        "Last 3 games average points scored difference",
        "Last 3 games average points allowed difference",
        "Last 3 games average point differential difference",
        "Last 3 games win percentage difference",
        "Elo rating difference",
        "Elo rating difference with home-field advantage",
        "Elo-based home win probability",
        "Strength of schedule difference",
        "Current opponent win percentage difference"
    ]

    st.markdown("### Features Used")

    for feature in feature_list:
        st.markdown(f"- {feature}")

except FileNotFoundError:
    st.error(
        "Prediction file not found. Run `python src/train_model.py` first to create the predictions file."
    )