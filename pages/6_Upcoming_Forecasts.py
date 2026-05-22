import pandas as pd
import streamlit as st
import json
import sys

sys.path.append("src")

from style import apply_global_styles, page_header, section_header, clean_column_names
from team_info import (
    get_team_logo,
    get_team_name,
    get_team_primary_color,
    get_team_conference,
    get_team_division,
)


st.set_page_config(
    page_title="Upcoming Forecasts",
    page_icon="🔮",
    layout="wide"
)

apply_global_styles()


@st.cache_data
def load_upcoming_predictions():
    """Load upcoming 2026 forecast predictions."""
    filepath = "data/predictions/upcoming_2026_predictions.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_projected_records():
    """Load projected 2026 team records."""
    filepath = "data/predictions/projected_2026_records.csv"
    return pd.read_csv(filepath)

@st.cache_data
def load_forecast_metadata():
    """Load forecast metadata."""
    filepath = "data/predictions/forecast_metadata.json"

    with open(filepath, "r") as file:
        return json.load(file)
    
@st.cache_data
def load_playoff_seeds():
    """Load projected playoff seeds."""
    filepath = "data/predictions/projected_playoff_seeds.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_first_teams_out():
    """Load projected first teams out."""
    filepath = "data/predictions/projected_first_teams_out.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_playoff_games():
    """Load projected playoff games."""
    filepath = "data/predictions/projected_playoff_games.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_super_bowl_projection():
    """Load projected Super Bowl summary."""
    filepath = "data/predictions/projected_super_bowl.json"

    with open(filepath, "r") as file:
        return json.load(file)
    
def get_seed_label(team, playoff_seeds):
    """Return a team's playoff seed as a string."""
    team_seed = playoff_seeds[playoff_seeds["team"] == team]

    if len(team_seed) == 0:
        return ""

    seed = int(team_seed.iloc[0]["seed"])
    return f"#{seed}"


def render_bracket_game(row, playoff_seeds):
    """Render one playoff game as a bracket-style card using native Streamlit components."""
    home_team = row["home_team"]
    away_team = row["away_team"]
    winner = row["winner"]

    home_seed = get_seed_label(home_team, playoff_seeds)
    away_seed = get_seed_label(away_team, playoff_seeds)

    home_logo = get_team_logo(home_team)
    away_logo = get_team_logo(away_team)

    if row["round"] == "Super Bowl":
        matchup_label = f"{home_team} vs {away_team}"
    else:
        matchup_label = f"{away_team} at {home_team}"

    with st.container(border=True):
        st.caption(f"{row['conference']} • {row['round']}")
        st.subheader(matchup_label)

        team_col1, vs_col, team_col2 = st.columns([2, 1, 2])

        with team_col1:
            if away_logo:
                st.image(away_logo, width=60)
            st.write("Away Team")
            st.write(f"**{away_seed} {away_team}**")

        with vs_col:
            st.markdown(
                "<h3 style='text-align: center; margin-top: 35px;'>VS</h3>",
                unsafe_allow_html=True
            )

        with team_col2:
            if home_logo:
                st.image(home_logo, width=60)
            st.write("Home Team")
            st.write(f"**{home_seed} {home_team}**")

        st.success(f"Projected Winner: {winner}")

def render_team_record_card(row, rank=None):
    """Render one team record as a small visual card."""
    team = row["team"]
    team_name = get_team_name(team)
    team_logo = get_team_logo(team)
    team_color = get_team_primary_color(team)

    projected_record = f"{int(row['projected_wins'])}-{int(row['projected_losses'])}"
    expected_record = f"{row['expected_wins']}-{row['expected_losses']}"

    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 4, 2])

        with col1:
            if team_logo:
                st.image(team_logo, width=55)

        with col2:
            if rank is not None:
                st.markdown(f"**#{rank} {team}**")
            else:
                st.markdown(f"**{team}**")

            st.caption(team_name)

        with col3:
            st.markdown(f"**Projected:** {projected_record}")
            st.caption(f"Expected: {expected_record}")


def render_division_cards(projected_records_display):
    """Render projected division standings as card-style groups."""
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

    for division in division_order:
        division_table = projected_records_display[
            projected_records_display["division"] == division
        ].copy()

        division_table = division_table.sort_values(
            ["projected_wins", "expected_wins"],
            ascending=False
        ).reset_index(drop=True)

        st.markdown(f"### {division}")

        for index, row in division_table.iterrows():
            render_team_record_card(row, rank=index + 1)


def render_playoff_seed_cards(playoff_seeds, first_teams_out):
    """Render projected playoff seeds and first teams out as cards."""
    for conference in ["AFC", "NFC"]:
        st.markdown(f"### {conference} Projected Seeds")

        conference_seeds = playoff_seeds[
            playoff_seeds["conference"] == conference
        ].copy()

        conference_seeds = conference_seeds.sort_values("seed")

        for _, row in conference_seeds.iterrows():
            team = row["team"]
            team_name = get_team_name(team)
            team_logo = get_team_logo(team)

            projected_record = (
                f"{int(row['projected_wins'])}-{int(row['projected_losses'])}"
            )
            expected_record = f"{row['expected_wins']}-{row['expected_losses']}"

            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 4, 2])

                with col1:
                    if team_logo:
                        st.image(team_logo, width=55)

                with col2:
                    st.markdown(f"**#{int(row['seed'])} {team}**")
                    st.caption(f"{team_name} • {row['division']} • {row['seed_type']}")

                with col3:
                    st.markdown(f"**Projected:** {projected_record}")
                    st.caption(f"Expected: {expected_record}")

        st.markdown(f"#### {conference} First Teams Out")

        conference_out = first_teams_out[
            first_teams_out["conference"] == conference
        ].copy()

        conference_out = conference_out.sort_values("rank_out")

        for _, row in conference_out.iterrows():
            team = row["team"]
            team_name = get_team_name(team)
            team_logo = get_team_logo(team)

            projected_record = (
                f"{int(row['projected_wins'])}-{int(row['projected_losses'])}"
            )
            expected_record = f"{row['expected_wins']}-{row['expected_losses']}"

            with st.container(border=True):
                col1, col2, col3 = st.columns([1, 4, 2])

                with col1:
                    if team_logo:
                        st.image(team_logo, width=50)

                with col2:
                    st.markdown(f"**#{int(row['rank_out'])} {team}**")
                    st.caption(f"{team_name} • {row['division']}")

                with col3:
                    st.markdown(f"**Projected:** {projected_record}")
                    st.caption(f"Expected: {expected_record}")


def render_conference_bracket(conference, playoff_games, playoff_seeds):
    """Render one conference playoff bracket."""
    conference_games = playoff_games[
        playoff_games["conference"] == conference
    ].copy()

    st.markdown(f"### {conference} Bracket")

    round_order = [
        "Wild Card",
        "Divisional",
        "Conference Championship",
    ]

    cols = st.columns(3)

    for col, playoff_round in zip(cols, round_order):
        with col:
            st.markdown(f"#### {playoff_round}")

            round_games = conference_games[
                conference_games["round"] == playoff_round
            ].copy()

            if len(round_games) == 0:
                st.info("No games available.")
            else:
                for _, row in round_games.iterrows():
                    render_bracket_game(row, playoff_seeds)


def render_super_bowl_bracket(playoff_games, playoff_seeds, super_bowl_projection):
    """Render the projected Super Bowl game."""
    super_bowl_game = playoff_games[
        playoff_games["round"] == "Super Bowl"
    ].copy()

    st.markdown("### Projected Super Bowl")

    if len(super_bowl_game) > 0:
        render_bracket_game(super_bowl_game.iloc[0], playoff_seeds)

    sb_col1, sb_col2, sb_col3 = st.columns(3)

    with sb_col1:
        st.metric(
            "AFC Champion",
            super_bowl_projection["afc_champion"]
        )

    with sb_col2:
        st.metric(
            "NFC Champion",
            super_bowl_projection["nfc_champion"]
        )

    with sb_col3:
        st.metric(
            "Projected Champion",
            super_bowl_projection["super_bowl_champion"]
        )


page_header(
    title="Upcoming Forecasts",
    icon="🔮",
    subtitle=(
        "View predicted winners, win probabilities, projected margins, "
        "and projected team records for the upcoming 2026 NFL season."
    )
)

try:
    predictions = load_upcoming_predictions()
    projected_records = load_projected_records()
    metadata = load_forecast_metadata()
    playoff_seeds = load_playoff_seeds()
    first_teams_out = load_first_teams_out()
    playoff_games = load_playoff_games()
    super_bowl_projection = load_super_bowl_projection()

    predictions["gameday"] = pd.to_datetime(predictions["gameday"])

    st.markdown(
    f"""
    <div class="accent-card">
        <h4 style="margin-top: 0;">Forecast Metadata</h4>
        <p class="muted-text">
            <strong>Win model:</strong> {metadata.get("win_model", metadata["model"])}<br>
        <strong>Margin model:</strong> {metadata.get("margin_model", "Not available")}<br>
        <strong>Margin model MAE:</strong> {metadata.get("margin_model_mae", "Not available")} points<br>
        <strong>Forecast season:</strong> {metadata["forecast_season"]}<br>
        <strong>Upcoming games forecasted:</strong> {metadata["upcoming_games_forecasted"]}<br>
        <strong>Last updated:</strong> {metadata["last_updated"]}
        </p>
    </div>
    """,
    unsafe_allow_html=True
    )

    st.divider()

    section_header("2026 Forecast Summary")

    total_games = len(predictions)
    avg_home_win_prob = predictions["home_win_probability"].mean()
    avg_projected_margin = predictions["predicted_home_margin"].abs().mean()

    col1, col2, col3 = st.columns(3)

    col1.metric("Upcoming Games Forecasted", total_games)
    col2.metric("Avg Home Win Probability", f"{avg_home_win_prob:.2%}")
    col3.metric("Avg Projected Margin", f"{avg_projected_margin:.1f} pts")

    st.divider()

    section_header("Weekly Game Forecasts")

    weeks = sorted(predictions["week"].unique())

    selected_week = st.selectbox(
        "Select a week",
        weeks
    )

    week_predictions = predictions[
        predictions["week"] == selected_week
    ].copy()

    week_predictions["home_win_probability_percent"] = (
        week_predictions["home_win_probability"] * 100
    ).round(1)

    week_predictions["away_win_probability_percent"] = (
        week_predictions["away_win_probability"] * 100
    ).round(1)

    display_table = week_predictions[
        [
            "week",
            "gameday",
            "away_team",
            "home_team",
            "predicted_winner",
            "home_win_probability_percent",
            "away_win_probability_percent",
            "predicted_margin_text",
            "status",
        ]
    ].copy()

    st.dataframe(
        clean_column_names(display_table),
        use_container_width=True,
        hide_index=True
    )

    st.caption(
        "Predicted margin is based on a separate regression model that estimates home team point differential."
    )

    st.divider()

    section_header(f"Week {selected_week} Forecast Cards")

    for _, row in week_predictions.iterrows():
        home_team = row["home_team"]
        away_team = row["away_team"]

        home_logo = get_team_logo(home_team)
        away_logo = get_team_logo(away_team)

        home_name = get_team_name(home_team)
        away_name = get_team_name(away_team)

        home_color = get_team_primary_color(home_team)

        home_prob = row["home_win_probability"] * 100
        away_prob = row["away_win_probability"] * 100

        with st.container(border=True):
            st.markdown(
                f"""
                <div style="
                    border-left: 8px solid {home_color};
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
                    st.write(f"Win Probability: **{away_prob:.1f}%**")

                with logo_col2:
                    if home_logo:
                        st.image(home_logo, width=80)
                    st.write(f"**{home_team}**")
                    st.write(f"Win Probability: **{home_prob:.1f}%**")

            with col2:
                st.write(f"Predicted Winner: **{row['predicted_winner']}**")
                st.write(f"Projected Margin: **{row['predicted_margin_text']}**")
                st.write(f"Game Date: **{row['gameday'].date()}**")

            with col3:
                st.info(row["status"])

    st.divider()

    section_header("Projected 2026 Team Records")

    st.write(
        "Projected records use the model's predicted winners for each remaining game. "
        "Expected records use win probabilities, so they can include decimals."
    )

    projected_records_display = projected_records.copy()

    projected_records_display["team_name"] = projected_records_display["team"].apply(
        get_team_name
    )

    projected_records_display["conference"] = projected_records_display["team"].apply(
        get_team_conference
    )

    projected_records_display["division"] = projected_records_display["team"].apply(
        get_team_division
    )

    projected_records_display = projected_records_display[
        [
            "team",
            "team_name",
            "conference",
            "division",
            "actual_wins",
            "actual_losses",
            "projected_wins",
            "projected_losses",
            "expected_wins",
            "expected_losses",
        ]
    ]

    st.dataframe(
        clean_column_names(projected_records_display),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    section_header("Projected Division Standings")

    st.write(
        "Projected division standings are based on the model's predicted winners for the 2026 schedule. "
        "Expected wins use win probabilities and include decimals."
    )

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

    render_division_cards(projected_records_display)

    with st.expander("View division standings table"):
        st.dataframe(
            clean_column_names(projected_records_display),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    section_header("Projected Conference Standings")

    selected_conference = st.selectbox(
        "Select a conference",
        ["AFC", "NFC"]
    )

    conference_table = projected_records_display[
        projected_records_display["conference"] == selected_conference
    ].copy()

    conference_table = conference_table.sort_values(
        ["projected_wins", "expected_wins"],
        ascending=False
    ).reset_index(drop=True)

    st.dataframe(
        clean_column_names(conference_table[
            [
                "team",
                "team_name",
                "division",
                "projected_wins",
                "projected_losses",
                "expected_wins",
                "expected_losses",
            ]
        ]),
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    section_header("Projected Playoff Seeds")

    st.write(
        "The projected playoff seeds are based on the model's projected regular-season records. "
        "Division winners receive seeds 1–4, and the next three teams in each conference receive wild card spots."
    )

    render_playoff_seed_cards(playoff_seeds, first_teams_out)

    with st.expander("View playoff seed tables"):
        st.markdown("### Projected Playoff Seeds")
        st.dataframe(
            clean_column_names(playoff_seeds),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("### First Teams Out")
        st.dataframe(
            clean_column_names(first_teams_out),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    section_header("Visual Projected Playoff Bracket")

    st.write(
        "This bracket uses the projected playoff seeds and picks winners using projected team strength. "
        "The winner of each matchup is highlighted by the color accent on the left side of the card."
    )

    render_conference_bracket(
        "AFC",
        playoff_games,
        playoff_seeds
    )

    st.divider()

    render_conference_bracket(
        "NFC",
        playoff_games,
        playoff_seeds
    )

    st.divider()

    render_super_bowl_bracket(
        playoff_games,
        playoff_seeds,
        super_bowl_projection
    )

    st.divider()

    section_header("Top Projected Teams")

    top_records = projected_records_display.sort_values(
        ["projected_wins", "expected_wins"],
        ascending=False
    ).head(10)

    st.bar_chart(
        top_records,
        x="team",
        y="projected_wins"
    )

    st.divider()

    section_header("Forecast Notes")

    st.write(
        "These are preseason-style 2026 forecasts. Since no 2026 games have been played yet, "
        "the model relies mostly on carried-forward team strength, 2025 performance, Elo ratings, "
        "strength of schedule, and historical model patterns."
    )

    st.write(
        "Once 2026 games are completed, rerunning `python src/predict_upcoming.py` will refresh "
        "the forecasts using the latest completed results."
    )

except FileNotFoundError:
    st.error(
        "Upcoming forecast files not found. Run `python src/predict_upcoming.py` first."
    )