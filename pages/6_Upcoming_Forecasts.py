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
    icon="🏈",
    subtitle="Browse predicted winners and win probabilities by week.",
)

try:
    predictions = load_upcoming_predictions()
    metadata = load_forecast_metadata()

    predictions["gameday"] = pd.to_datetime(predictions["gameday"])
    pending = predictions.loc[
        predictions["status"] == "Pending"
    ].copy()

    st.caption(
        f"Forecast last updated: "
        f"{metadata.get('last_updated', 'Not available')}"
    )

    st.write(
        "These estimates use completed game results and team-strength "
        "features. They do not yet incorporate injuries, starting "
        "quarterbacks, roster changes, or coaching changes directly."
    )

    if pending.empty:
        st.info("There are no pending games in the saved forecast.")
    else:
        weeks = sorted(pending["week"].unique())

        selected_week = st.selectbox(
            "Choose a week",
            weeks,
            format_func=lambda week: f"Week {int(week)}",
        )

        week_predictions = pending.loc[
            pending["week"] == selected_week
        ].sort_values(
            ["gameday", "away_team", "home_team"]
        )

        section_header(
            f"Week {int(selected_week)} · {len(week_predictions)} games"
        )

        table = week_predictions[
            [
                "gameday",
                "away_team",
                "home_team",
                "predicted_winner",
                "away_win_probability",
                "home_win_probability",
            ]
        ].copy()

        table["gameday"] = table["gameday"].dt.strftime("%b %d, %Y")

        for column in ["away_win_probability", "home_win_probability"]:
            table[column] = table[column].map(
                lambda probability: f"{probability:.1%}"
            )

        table = table.rename(columns={
            "gameday": "Date",
            "away_team": "Away",
            "home_team": "Home",
            "predicted_winner": "Predicted winner",
            "away_win_probability": "Away win probability",
            "home_win_probability": "Home win probability",
        })

        st.dataframe(
            table,
            hide_index=True,
            use_container_width=True,
        )

        st.caption(
            "Probabilities assume the game does not end in a tie. "
            "A predicted winner is the more likely team, not a guaranteed result."
        )

        with st.expander("View matchup details"):
            for _, row in week_predictions.iterrows():
                away_team = row["away_team"]
                home_team = row["home_team"]

                st.subheader(f"{away_team} at {home_team}")
                st.caption(row["gameday"].strftime("%A, %B %d, %Y"))

                away_column, home_column = st.columns(2)

                with away_column:
                    logo = get_team_logo(away_team)
                    if logo:
                        st.image(logo, width=60)
                    st.metric(
                        get_team_name(away_team),
                        f"{row['away_win_probability']:.1%}",
                    )

                with home_column:
                    logo = get_team_logo(home_team)
                    if logo:
                        st.image(logo, width=60)
                    st.metric(
                        get_team_name(home_team),
                        f"{row['home_win_probability']:.1%}",
                    )

                st.write(
                    f"Predicted winner: **"
                    f"{get_team_name(row['predicted_winner'])}**"
                )
                st.divider()

    with st.expander("About these forecasts"):
        st.write(
            "The winner model uses logistic regression with scoring "
            "carryover, recent form, Elo, and strength of schedule. "
            "All future matchups use information available when the "
            "saved forecast was generated."
        )
        st.write(
            "Later-week forecasts are not based on simulated results "
            "for intervening games. See How the Model Works and "
            "Model Comparison for methodology and evaluation results."
        )

except FileNotFoundError:
    st.info("Forecast data is not available yet.")