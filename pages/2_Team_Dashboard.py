import pandas as pd
import streamlit as st
import sys

sys.path.append("src")

from team_info import get_team_logo, get_team_name, get_team_primary_color
from style import apply_global_styles, page_header, section_header, clean_column_names


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


@st.cache_data
def load_upcoming_predictions():
    """Load 2026 upcoming forecast predictions."""
    filepath = "data/predictions/upcoming_2026_predictions.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_projected_records():
    """Load projected 2026 team records."""
    filepath = "data/predictions/projected_2026_records.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_playoff_seeds():
    """Load projected playoff seeds."""
    filepath = "data/predictions/projected_playoff_seeds.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_first_teams_out():
    """Load first teams out of the projected playoff picture."""
    filepath = "data/predictions/projected_first_teams_out.csv"
    return pd.read_csv(filepath)


def get_team_2026_games(upcoming_predictions, selected_team):
    """Return all 2026 forecasted games for the selected team."""
    team_games = upcoming_predictions[
        (upcoming_predictions["home_team"] == selected_team)
        | (upcoming_predictions["away_team"] == selected_team)
    ].copy()

    team_games["gameday"] = pd.to_datetime(team_games["gameday"])

    team_games = team_games.sort_values(["week", "gameday"]).reset_index(drop=True)

    team_games["opponent"] = team_games.apply(
        lambda row: row["away_team"]
        if row["home_team"] == selected_team
        else row["home_team"],
        axis=1,
    )

    team_games["location"] = team_games.apply(
        lambda row: "Home"
        if row["home_team"] == selected_team
        else "Away",
        axis=1,
    )

    team_games["team_win_probability"] = team_games.apply(
        lambda row: row["home_win_probability"]
        if row["home_team"] == selected_team
        else row["away_win_probability"],
        axis=1,
    )

    team_games["team_win_probability_percent"] = (
        team_games["team_win_probability"] * 100
    ).round(1)

    team_games["model_picks_team"] = (
        team_games["predicted_winner"] == selected_team
    )

    team_games["projected_result"] = team_games["model_picks_team"].apply(
        lambda x: "Projected Win" if x else "Projected Loss"
    )

    team_games["team_margin_text"] = team_games.apply(
        lambda row: row["predicted_margin_text"]
        if selected_team in row["predicted_margin_text"]
        else row["predicted_margin_text"],
        axis=1,
    )

    return team_games


def get_team_playoff_status(selected_team, playoff_seeds, first_teams_out):
    """Return projected playoff status for selected team."""
    seed_row = playoff_seeds[playoff_seeds["team"] == selected_team]

    if len(seed_row) > 0:
        seed = int(seed_row.iloc[0]["seed"])
        seed_type = seed_row.iloc[0]["seed_type"]

        return {
            "status": "Projected Playoff Team",
            "seed": seed,
            "seed_type": seed_type,
            "detail": f"#{seed} seed, {seed_type}",
        }

    first_out_row = first_teams_out[first_teams_out["team"] == selected_team]

    if len(first_out_row) > 0:
        rank_out = int(first_out_row.iloc[0]["rank_out"])

        return {
            "status": "First Teams Out",
            "seed": None,
            "seed_type": None,
            "detail": f"Projected #{rank_out} in conference",
        }

    return {
        "status": "Outside Playoff Picture",
        "seed": None,
        "seed_type": None,
        "detail": "Not currently projected in playoff race",
    }


def render_2026_team_game_card(row, selected_team, selected_team_logo, selected_team_name):
    """Render one 2026 team forecast game card."""
    opponent = row["opponent"]
    opponent_logo = get_team_logo(opponent)
    opponent_name = get_team_name(opponent)

    selected_team_color = get_team_primary_color(selected_team)

    if row["location"] == "Home":
        matchup = f"{opponent} at {selected_team}"
        matchup_full = f"{opponent_name} at {selected_team_name}"
    else:
        matchup = f"{selected_team} at {opponent}"
        matchup_full = f"{selected_team_name} at {opponent_name}"

    with st.container(border=True):
        st.markdown(
            f"""
            <div style="
                border-left: 8px solid {selected_team_color};
                padding-left: 12px;
                margin-bottom: 8px;
            ">
                <h3 style="margin-bottom: 0;">Week {int(row['week'])}: {matchup}</h3>
                <p style="margin-top: 4px; color: #CBD5E1;">
                    {matchup_full}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            logo_col1, logo_col2 = st.columns(2)

            with logo_col1:
                if selected_team_logo:
                    st.image(selected_team_logo, width=75)
                st.write(f"**{selected_team}**")
                st.write(f"Win Probability: **{row['team_win_probability_percent']}%**")

            with logo_col2:
                if opponent_logo:
                    st.image(opponent_logo, width=75)
                st.write(f"**{opponent}**")
                st.write(f"Location: **{row['location']}**")

        with col2:
            st.write(f"Predicted Winner: **{row['predicted_winner']}**")
            st.write(f"Projected Margin: **{row['predicted_margin_text']}**")
            st.write(f"Game Date: **{row['gameday'].date()}**")

        with col3:
            if row["projected_result"] == "Projected Win":
                st.success("Projected Win")
            else:
                st.error("Projected Loss")


page_header(
    title="Team Dashboard",
    icon="🏟️",
    subtitle="Select a team to view its 2025 games, model predictions, and team-level prediction performance."
)

try:
    predictions = load_predictions()
    upcoming_predictions = load_upcoming_predictions()
    projected_records = load_projected_records()
    playoff_seeds = load_playoff_seeds()
    first_teams_out = load_first_teams_out()

    teams = sorted(
        set(predictions["home_team"].unique()).union(
            set(predictions["away_team"].unique())
        )
    )

    selected_team = st.selectbox(
        "Select a team",
        teams
    )

    selected_team_logo = get_team_logo(selected_team)
    selected_team_name = get_team_name(selected_team)
    selected_team_color = get_team_primary_color(selected_team)

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

    section_header("2025 Historical Model Evaluation")

    st.write(
        "This section shows how the model performed on completed 2025 test games involving the selected team. "
        "The 2026 forecast outlook above is used for upcoming season projections."
    )

    st.divider()

    st.markdown(
        f"""
        <div style="
            border-left: 10px solid {selected_team_color};
            padding-left: 16px;
            margin-bottom: 20px;
        ">
            <h2 style="margin-bottom: 0;">{selected_team} Team Dashboard</h2>
            <p style="margin-top: 4px; color: #CBD5E1;">
                {selected_team_name}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    header_col1, header_col2 = st.columns([1, 4])

    with header_col1:
        if selected_team_logo:
            st.image(selected_team_logo, width=120)

    with header_col2:
        st.subheader(selected_team_name)
        st.write(
            "This page shows the selected team's 2026 forecast outlook, projected schedule results, "
            "and historical model performance from the 2025 testing season."
        )
    
    st.divider()

    section_header("2026 Forecast Outlook")

    team_record = projected_records[
        projected_records["team"] == selected_team
    ].copy()

    team_playoff_status = get_team_playoff_status(
        selected_team,
        playoff_seeds,
        first_teams_out
    )

    team_2026_games = get_team_2026_games(
        upcoming_predictions,
        selected_team
    )

    if len(team_record) > 0:
        record_row = team_record.iloc[0]

        projected_record = (
            f"{int(record_row['projected_wins'])}-"
            f"{int(record_row['projected_losses'])}"
        )

        expected_record = (
            f"{record_row['expected_wins']}-"
            f"{record_row['expected_losses']}"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Projected Record", projected_record)
        col2.metric("Expected Record", expected_record)
        col3.metric("Division", record_row["division"])
        col4.metric("Playoff Status", team_playoff_status["status"])

        st.info(team_playoff_status["detail"])

    else:
        st.warning("No projected record found for this team.")

    if len(team_2026_games) > 0:
        most_winnable = team_2026_games.sort_values(
            "team_win_probability",
            ascending=False
        ).iloc[0]

        toughest_game = team_2026_games.sort_values(
            "team_win_probability",
            ascending=True
        ).iloc[0]

        closest_game = team_2026_games.iloc[
            (team_2026_games["team_win_probability"] - 0.5).abs().argsort()
        ].iloc[0]

        projected_wins = int(team_2026_games["model_picks_team"].sum())
        projected_losses = int(len(team_2026_games) - projected_wins)

        st.markdown("### 2026 Forecast Highlights")

        hcol1, hcol2, hcol3, hcol4 = st.columns(4)

        with hcol1:
            st.metric("Forecasted Games", len(team_2026_games))

        with hcol2:
            st.metric("Projected Wins", projected_wins)

        with hcol3:
            st.metric(
                "Most Winnable Game",
                f"Week {int(most_winnable['week'])} vs {most_winnable['opponent']}"
            )
            st.caption(
                f"{most_winnable['team_win_probability_percent']}% win probability"
            )

        with hcol4:
            st.metric(
                "Toughest Game",
                f"Week {int(toughest_game['week'])} vs {toughest_game['opponent']}"
            )
            st.caption(
                f"{toughest_game['team_win_probability_percent']}% win probability"
            )

        st.caption(
            f"Closest projected game: Week {int(closest_game['week'])} vs "
            f"{closest_game['opponent']} "
            f"({closest_game['team_win_probability_percent']}% win probability)"
        )

    st.markdown("### 2026 Team Schedule Forecast")

    team_2026_display = team_2026_games[
        [
            "week",
            "gameday",
            "location",
            "opponent",
            "predicted_winner",
            "team_win_probability_percent",
            "predicted_margin_text",
            "projected_result",
            "status",
        ]
    ].copy()

    st.dataframe(
        clean_column_names(team_2026_display),
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("View 2026 team forecast game cards"):
        for _, row in team_2026_games.iterrows():
            render_2026_team_game_card(
                row,
                selected_team,
                selected_team_logo,
                selected_team_name,
            )




    st.divider()

    with st.expander("View 2025 evaluation game cards"):
        
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
        
        st.header("2025 Game-by-Game Evaluation Results")

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
            clean_column_names(team_games[display_columns]),
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "Team win probability is adjusted based on whether the selected team was home or away."
        )

        section_header("2025 Evaluation Game Cards")

        for _, row in team_games.iterrows():
            opponent = row["opponent"]
            opponent_logo = get_team_logo(opponent)
            opponent_name = get_team_name(opponent)
            opponent_color = get_team_primary_color(opponent)

            card_color = selected_team_color

            with st.container(border=True):
                if row["location"] == "Home":
                    matchup = f"{opponent} at {selected_team}"
                    matchup_full = f"{opponent_name} at {selected_team_name}"
                else:
                    matchup = f"{selected_team} at {opponent}"
                    matchup_full = f"{selected_team_name} at {opponent_name}"

                st.markdown(
                    f"""
                    <div style="
                        border-left: 8px solid {card_color};
                        padding-left: 12px;
                        margin-bottom: 8px;
                    ">
                        <h3 style="margin-bottom: 0;">Week {int(row['week'])}: {matchup}</h3>
                        <p style="margin-top: 4px; color: #CBD5E1;">
                            {matchup_full}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                col1, col2, col3 = st.columns([2, 2, 1])

                with col1:
                    logo_col1, logo_col2 = st.columns(2)

                    with logo_col1:
                        if selected_team_logo:
                            st.image(selected_team_logo, width=75)
                        st.write(f"**{selected_team}**")
                        st.write(f"{int(row['team_score'])} points")

                    with logo_col2:
                        if opponent_logo:
                            st.image(opponent_logo, width=75)
                        st.write(f"**{opponent}**")
                        st.write(f"{int(row['opponent_score'])} points")

                with col2:
                    st.write(f"Location: **{row['location']}**")
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