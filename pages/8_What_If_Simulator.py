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

def build_original_league_records(predictions):
    """
    Build original projected league records from upcoming predictions.
    Uses predicted winners from every forecasted game.
    """
    teams = sorted(
        set(predictions["home_team"].unique()).union(
            set(predictions["away_team"].unique())
        )
    )

    records = {
        team: {
            "team": team,
            "projected_wins": 0,
            "projected_losses": 0,
            "expected_wins": 0.0,
            "expected_losses": 0.0,
        }
        for team in teams
    }

    for _, row in predictions.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        predicted_winner = row["predicted_winner"]

        predicted_loser = away_team if predicted_winner == home_team else home_team

        records[predicted_winner]["projected_wins"] += 1
        records[predicted_loser]["projected_losses"] += 1

        records[home_team]["expected_wins"] += row["home_win_probability"]
        records[home_team]["expected_losses"] += row["away_win_probability"]

        records[away_team]["expected_wins"] += row["away_win_probability"]
        records[away_team]["expected_losses"] += row["home_win_probability"]

    records_df = pd.DataFrame(records.values())

    records_df["expected_wins"] = records_df["expected_wins"].round(1)
    records_df["expected_losses"] = records_df["expected_losses"].round(1)

    return records_df


def apply_what_if_changes_to_league(predictions, selected_team, selected_outcomes):
    """
    Recalculate league-wide projected records after user changes selected team's games.
    Each changed result affects both teams in that game.
    """
    adjusted_predictions = predictions.copy()

    for index, row in adjusted_predictions.iterrows():
        game_id = row["game_id"]

        if game_id not in selected_outcomes:
            continue

        selected_team_result = selected_outcomes[game_id]

        home_team = row["home_team"]
        away_team = row["away_team"]

        if selected_team_result == "Win":
            adjusted_winner = selected_team
        else:
            adjusted_winner = away_team if selected_team == home_team else home_team

        adjusted_predictions.loc[index, "adjusted_winner"] = adjusted_winner

    adjusted_predictions["adjusted_winner"] = adjusted_predictions[
        "adjusted_winner"
    ].fillna(adjusted_predictions["predicted_winner"])

    teams = sorted(
        set(adjusted_predictions["home_team"].unique()).union(
            set(adjusted_predictions["away_team"].unique())
        )
    )

    records = {
        team: {
            "team": team,
            "adjusted_wins": 0,
            "adjusted_losses": 0,
        }
        for team in teams
    }

    for _, row in adjusted_predictions.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]
        adjusted_winner = row["adjusted_winner"]

        adjusted_loser = away_team if adjusted_winner == home_team else home_team

        records[adjusted_winner]["adjusted_wins"] += 1
        records[adjusted_loser]["adjusted_losses"] += 1

    adjusted_records = pd.DataFrame(records.values())

    return adjusted_records, adjusted_predictions


def create_adjusted_standings(original_records, adjusted_records, projected_records):
    """
    Combine original projected records, adjusted records, and team metadata.
    """
    standings = original_records.merge(
        adjusted_records,
        on="team",
        how="left"
    )

    metadata_cols = [
        "team",
        "conference",
        "division",
        "expected_wins",
        "expected_losses",
    ]

    metadata = projected_records[metadata_cols].copy()

    standings = standings.drop(
        columns=["expected_wins", "expected_losses"],
        errors="ignore"
    )

    standings = standings.merge(
        metadata,
        on="team",
        how="left"
    )

    standings["win_change"] = (
        standings["adjusted_wins"] - standings["projected_wins"]
    )

    standings["loss_change"] = (
        standings["adjusted_losses"] - standings["projected_losses"]
    )

    standings["original_record"] = (
        standings["projected_wins"].astype(int).astype(str)
        + "-"
        + standings["projected_losses"].astype(int).astype(str)
    )

    standings["adjusted_record"] = (
        standings["adjusted_wins"].astype(int).astype(str)
        + "-"
        + standings["adjusted_losses"].astype(int).astype(str)
    )

    standings = standings.sort_values(
        ["adjusted_wins", "expected_wins"],
        ascending=False
    ).reset_index(drop=True)

    return standings


def get_most_affected_teams(adjusted_standings):
    """
    Return teams whose records changed from the what-if scenario.
    """
    affected = adjusted_standings[
        (adjusted_standings["win_change"] != 0)
        | (adjusted_standings["loss_change"] != 0)
    ].copy()

    affected = affected.sort_values(
        ["win_change", "loss_change"],
        ascending=[False, True]
    )

    return affected


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

    section_header("Adjusted League Impact")

    st.write(
        "This section recalculates league-wide projected records after your changes. "
        "Each changed game affects both the selected team and its opponent."
    )

    original_league_records = build_original_league_records(predictions)

    adjusted_league_records, adjusted_predictions = apply_what_if_changes_to_league(
        predictions,
        selected_team,
        selected_outcomes
    )

    adjusted_standings = create_adjusted_standings(
        original_league_records,
        adjusted_league_records,
        projected_records
    )

    affected_teams = get_most_affected_teams(adjusted_standings)

    if len(affected_teams) > 0:
        st.markdown("### Teams Affected by This Scenario")

        affected_display = affected_teams[
            [
                "team",
                "conference",
                "division",
                "original_record",
                "adjusted_record",
                "win_change",
                "loss_change",
            ]
        ].copy()

        st.dataframe(
            clean_column_names(affected_display),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No league-wide records changed because no game outcomes were changed.")

        st.divider()

        st.markdown("### Adjusted Division Standings")

    division_order = [
        "AFC East",
        "AFC North",
        "AFC South",
        "AFC West",
        "NFC East",
        "NFC North",
        "NFC South",
        "NFC West",
    ]

    selected_division = st.selectbox(
        "Select a division to view adjusted standings",
        division_order
    )

    division_standings = adjusted_standings[
        adjusted_standings["division"] == selected_division
    ].copy()

    division_standings = division_standings.sort_values(
        ["adjusted_wins", "expected_wins"],
        ascending=False
    )

    division_display = division_standings[
        [
            "team",
            "original_record",
            "adjusted_record",
            "win_change",
            "loss_change",
            "expected_wins",
            "expected_losses",
        ]
    ].copy()

    st.dataframe(
        clean_column_names(division_display),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.markdown("### Adjusted Conference Standings")

    selected_conference = st.selectbox(
        "Select a conference to view adjusted standings",
        ["AFC", "NFC"]
    )

    conference_standings = adjusted_standings[
        adjusted_standings["conference"] == selected_conference
    ].copy()

    conference_standings = conference_standings.sort_values(
        ["adjusted_wins", "expected_wins"],
        ascending=False
    ).reset_index(drop=True)

    conference_standings["adjusted_conference_rank"] = (
        conference_standings.index + 1
    )

    conference_display = conference_standings[
        [
            "adjusted_conference_rank",
            "team",
            "division",
            "original_record",
            "adjusted_record",
            "win_change",
            "loss_change",
            "expected_wins",
            "expected_losses",
        ]
    ].copy()

    st.dataframe(
        clean_column_names(conference_display),
        use_container_width=True,
        hide_index=True
    )

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
        "This simulator lets you test team-level scenarios by changing projected wins and losses. "
        "When a game result is changed, both teams in that matchup are updated in the adjusted league standings."
    )

    st.write(
        "The simulator now recalculates adjusted league records, division standings, and conference standings. "
        "A future version can also recalculate playoff seeds, playoff brackets, and the projected Super Bowl champion from the adjusted standings."
    )

except FileNotFoundError:
    st.error(
        "Forecast files not found. Run `python src/predict_upcoming.py` first."
    )