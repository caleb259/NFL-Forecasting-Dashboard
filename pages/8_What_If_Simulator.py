import pandas as pd
import streamlit as st
import sys

sys.path.append("src")

from style import apply_global_styles, page_header, section_header, clean_column_names
from team_info import get_team_logo, get_team_name, get_team_primary_color


st.set_page_config(
    page_title="What If Simulator",
    page_icon="🧪",
    layout="wide"
)

apply_global_styles()


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


def get_team_games(predictions, selected_team):
    """Return 2026 forecasted games for one team."""
    team_games = predictions[
        (predictions["home_team"] == selected_team)
        | (predictions["away_team"] == selected_team)
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

    team_games["original_projected_result"] = team_games.apply(
        lambda row: "Win"
        if row["predicted_winner"] == selected_team
        else "Loss",
        axis=1,
    )

    team_games["game_label"] = team_games.apply(
        lambda row: (
            f"Week {int(row['week'])}: {selected_team} vs {row['opponent']}"
            if row["location"] == "Home"
            else f"Week {int(row['week'])}: {selected_team} at {row['opponent']}"
        ),
        axis=1,
    )

    return team_games


def get_original_record(team_games):
    """Calculate original projected record from forecasted winners."""
    wins = int((team_games["original_projected_result"] == "Win").sum())
    losses = int((team_games["original_projected_result"] == "Loss").sum())

    return wins, losses


def calculate_adjusted_record(team_games, selected_outcomes):
    """Calculate adjusted projected record from user-selected outcomes."""
    adjusted_wins = 0
    adjusted_losses = 0
    changed_games = []

    for _, row in team_games.iterrows():
        game_id = row["game_id"]
        original_result = row["original_projected_result"]
        adjusted_result = selected_outcomes.get(game_id, original_result)

        if adjusted_result == "Win":
            adjusted_wins += 1
        else:
            adjusted_losses += 1

        if adjusted_result != original_result:
            changed_games.append(
                {
                    "week": row["week"],
                    "opponent": row["opponent"],
                    "location": row["location"],
                    "original_result": original_result,
                    "adjusted_result": adjusted_result,
                }
            )

    return adjusted_wins, adjusted_losses, changed_games


def render_team_header(selected_team):
    """Render selected team header."""
    team_name = get_team_name(selected_team)
    team_logo = get_team_logo(selected_team)
    team_color = get_team_primary_color(selected_team)

    st.markdown(
        f"""
        <div style="
            border-left: 10px solid {team_color};
            padding-left: 16px;
            margin-bottom: 20px;
        ">
            <h2 style="margin-bottom: 0;">{selected_team} What If Simulator</h2>
            <p style="margin-top: 4px; color: #CBD5E1;">
                {team_name}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 4])

    with col1:
        if team_logo:
            st.image(team_logo, width=120)

    with col2:
        st.write(
            "Flip projected wins and losses to see how the selected team's projected record changes."
        )
        st.caption(
            "This first version updates the selected team's record only. League-wide standings and playoff seeds will be added in a later version."
        )


page_header(
    title="What If Simulator",
    icon="🧪",
    subtitle="Explore how changing projected game results affects a team's 2026 projected record."
)


try:
    predictions = load_upcoming_predictions()
    projected_records = load_projected_records()

    teams = sorted(
        set(predictions["home_team"].unique()).union(
            set(predictions["away_team"].unique())
        )
    )

    selected_team = st.selectbox(
        "Select a team",
        teams
    )

    render_team_header(selected_team)

    team_games = get_team_games(predictions, selected_team)

    original_wins, original_losses = get_original_record(team_games)

    st.divider()

    section_header("Original 2026 Projection")

    team_record = projected_records[
        projected_records["team"] == selected_team
    ].copy()

    projected_record_text = f"{original_wins}-{original_losses}"

    if len(team_record) > 0:
        record_row = team_record.iloc[0]
        expected_record_text = (
            f"{record_row['expected_wins']}-"
            f"{record_row['expected_losses']}"
        )
    else:
        expected_record_text = "Not available"

    col1, col2, col3 = st.columns(3)

    col1.metric("Original Projected Record", projected_record_text)
    col2.metric("Expected Record", expected_record_text)
    col3.metric("Forecasted Games", len(team_games))

    st.divider()

    section_header("Change Game Outcomes")

    st.write(
        "Use the dropdowns below to change individual projected game results. "
        "The adjusted record will update based on your selections."
    )

    selected_outcomes = {}

    for _, row in team_games.iterrows():
        game_id = row["game_id"]

        default_index = 0 if row["original_projected_result"] == "Win" else 1

        with st.container(border=True):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

            with col1:
                st.markdown(f"**{row['game_label']}**")
                st.caption(
                    f"{row['location']} game | Projected margin: {row['predicted_margin_text']}"
                )

            with col2:
                st.write(f"Opponent: **{row['opponent']}**")
                st.write(
                    f"Win Probability: **{row['team_win_probability_percent']}%**"
                )

            with col3:
                st.write(
                    f"Original Pick: **{row['original_projected_result']}**"
                )
                st.caption(f"Model picked: {row['predicted_winner']}")

            with col4:
                selected_result = st.selectbox(
                    "Adjusted Result",
                    ["Win", "Loss"],
                    index=default_index,
                    key=f"what_if_{game_id}_{selected_team}"
                )

                selected_outcomes[game_id] = selected_result

    adjusted_wins, adjusted_losses, changed_games = calculate_adjusted_record(
        team_games,
        selected_outcomes
    )

    st.divider()

    section_header("Adjusted Projection")

    win_change = adjusted_wins - original_wins
    loss_change = adjusted_losses - original_losses

    acol1, acol2, acol3 = st.columns(3)

    acol1.metric(
        "Adjusted Projected Record",
        f"{adjusted_wins}-{adjusted_losses}"
    )

    acol2.metric(
        "Win Change",
        f"{win_change:+d}"
    )

    acol3.metric(
        "Loss Change",
        f"{loss_change:+d}"
    )

    if len(changed_games) > 0:
        st.markdown("### Changed Games")

        changed_games_df = pd.DataFrame(changed_games)

        st.dataframe(
            clean_column_names(changed_games_df),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No games have been changed from the original projection.")

    st.divider()

    section_header("Adjusted Schedule View")

    adjusted_rows = []

    for _, row in team_games.iterrows():
        adjusted_result = selected_outcomes.get(
            row["game_id"],
            row["original_projected_result"]
        )

        adjusted_rows.append(
            {
                "week": row["week"],
                "gameday": row["gameday"],
                "location": row["location"],
                "opponent": row["opponent"],
                "original_projected_result": row["original_projected_result"],
                "adjusted_result": adjusted_result,
                "team_win_probability_percent": row["team_win_probability_percent"],
                "predicted_margin_text": row["predicted_margin_text"],
                "confidence_level": row.get("confidence_level", "Not available"),
                "upset_alert_label": row.get("upset_alert_label", "Not available"),
            }
        )

    adjusted_schedule_df = pd.DataFrame(adjusted_rows)

    st.dataframe(
        clean_column_names(adjusted_schedule_df),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    section_header("What This Simulator Does")

    st.write(
        "This simulator lets you test simple team-level scenarios by changing projected wins and losses. "
        "It does not currently recalculate every other team's record, division standings, conference standings, "
        "or playoff seeds."
    )

    st.write(
        "A future version can expand this into a full league-wide simulator where changing one game updates both teams, "
        "the division standings, playoff picture, and projected Super Bowl bracket."
    )

except FileNotFoundError:
    st.error(
        "Forecast files not found. Run `python src/predict_upcoming.py` first."
    )