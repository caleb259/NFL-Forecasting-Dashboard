import streamlit as st


def apply_global_styles():
    """
    Apply custom CSS styling across the Streamlit dashboard.
    """
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 3rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 0.2rem;
            color: #F8FAFC;
        }

        .page-title {
            font-size: 2.6rem !important;
            line-height: 1.1 !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
            margin-bottom: 0.3rem !important;
            color: #F8FAFC !important;
        }

        .subtitle {
            font-size: 1.1rem !important;
            line-height: 1.5 !important;
            color: #CBD5E1 !important;
            margin-bottom: 1.5rem !important;
        }

        .section-header {
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: #F8FAFC;
        }

        .small-section-header {
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            color: #F8FAFC;
        }

        .muted-text {
            color: #CBD5E1;
        }

        .accent-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 1rem;
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

        div[data-testid="stDataFrame"] {
            border-radius: 12px;
        }

        .stAlert {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def page_header(title, subtitle=None, icon=None):
    """
    Display a consistent page header.
    """
    display_title = f"{icon} {title}" if icon else title

    st.markdown(
        f"""
        <h1 class="page-title">{display_title}</h1>
        """,
        unsafe_allow_html=True
    )

    if subtitle:
        st.markdown(
            f"""
            <p class="subtitle">{subtitle}</p>
            """,
            unsafe_allow_html=True
        )


def main_header(title, subtitle=None, icon=None):
    """
    Display a larger homepage-style header.
    """
    display_title = f"{icon} {title}" if icon else title

    st.markdown(
        f"""
        <div class="main-title">{display_title}</div>
        """,
        unsafe_allow_html=True
    )

    if subtitle:
        st.markdown(
            f"""
            <div class="subtitle">{subtitle}</div>
            """,
            unsafe_allow_html=True
        )


def section_header(title):
    """
    Display a consistent section header.
    """
    st.markdown(
        f"""
        <div class="section-header">{title}</div>
        """,
        unsafe_allow_html=True
    )


def small_section_header(title):
    """
    Display a smaller section header.
    """
    st.markdown(
        f"""
        <div class="small-section-header">{title}</div>
        """,
        unsafe_allow_html=True
    )

def clean_column_names(df):
    """
    Return a copy of a DataFrame with cleaner column names for display.
    """
    rename_map = {
        "season": "Season",
        "week": "Week",
        "game_id": "Game ID",
        "gameday": "Game Date",
        "weekday": "Weekday",
        "home_team": "Home Team",
        "away_team": "Away Team",
        "home_score": "Home Score",
        "away_score": "Away Score",
        "home_team_won": "Home Team Won",
        "predicted_home_win": "Predicted Home Win",
        "home_win_probability": "Home Win Probability",
        "away_win_probability": "Away Win Probability",
        "home_win_probability_percent": "Home Win Probability",
        "away_win_probability_percent": "Away Win Probability",
        "predicted_winner": "Predicted Winner",
        "actual_winner": "Actual Winner",
        "correct_prediction": "Correct Prediction",
        "result": "Result",
        "confidence": "Confidence",
        "status": "Status",
        "predicted_home_margin": "Predicted Home Margin",
        "predicted_margin_text": "Projected Margin",
        "predicted_margin_abs": "Projected Margin",
        "team": "Team",
        "team_name": "Team Name",
        "conference": "Conference",
        "division": "Division",
        "actual_wins": "Actual Wins",
        "actual_losses": "Actual Losses",
        "projected_wins": "Projected Wins",
        "projected_losses": "Projected Losses",
        "expected_wins": "Expected Wins",
        "expected_losses": "Expected Losses",
        "number_of_games": "Number of Games",
        "accuracy_percent": "Accuracy",
        "accuracy": "Accuracy",
        "prediction_result": "Prediction Result",
        "game_result": "Game Result",
        "location": "Location",
        "opponent": "Opponent",
        "team_score": "Team Score",
        "opponent_score": "Opponent Score",
        "team_win_probability_percent": "Team Win Probability",
        "model": "Model",
        "Model Version": "Model Version",
        "Accuracy": "Accuracy",
        "Notes": "Notes",
        "Feature": "Feature",
        "Value": "Value",
        "Explanation": "Explanation",
        "home_strength_of_schedule_before": "Home Strength of Schedule",
        "away_strength_of_schedule_before": "Away Strength of Schedule",
        "strength_of_schedule_diff": "Strength of Schedule Difference",
        "current_opponent_win_pct_diff": "Current Opponent Win % Difference",
        "home_elo_before": "Home Elo",
        "away_elo_before": "Away Elo",
        "elo_diff": "Elo Difference",
        "home_elo_with_hfa_diff": "Elo Difference with Home Field",
        "elo_home_win_prob": "Elo Home Win Probability",
        "seed": "Seed",
        "seed_type": "Seed Type",
        "rank_out": "Rank",
        "winner": "Winner",
        "loser": "Loser",
        "matchup": "Matchup",
        "round": "Round",
        "home_seed": "Home Seed",
        "away_seed": "Away Seed",
        "winner_win_probability": "Winner Win Probability",
        "confidence_level": "Confidence Level",
        "upset_alert": "Upset Alert",
        "upset_alert_label": "Upset Alert",
        "adjusted_wins": "Adjusted Wins",
        "adjusted_losses": "Adjusted Losses",
        "win_change": "Win Change",
        "loss_change": "Loss Change",
        "original_record": "Original Record",
        "adjusted_record": "Adjusted Record",
        "adjusted_conference_rank": "Adjusted Conference Rank",
        "original_result": "Original Result",
        "adjusted_result": "Adjusted Result",
        "adjusted_seed": "Adjusted Seed",
        "adjusted_rank_out": "Adjusted Rank",
        "seed_type": "Seed Type",
        "winner": "Winner",
        "loser": "Loser",
        "round": "Round",
        "home_seed": "Home Seed",
        "away_seed": "Away Seed",
    }

    display_df = df.copy()
    display_df = display_df.rename(columns=rename_map)

    return display_df