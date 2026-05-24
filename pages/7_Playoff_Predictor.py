import json
import pandas as pd
import streamlit as st
import sys

sys.path.append("src")

from style import apply_global_styles, page_header, section_header, clean_column_names
from team_info import get_team_logo, get_team_name, get_team_primary_color


st.set_page_config(
    page_title="Playoff Predictor",
    page_icon="🏆",
    layout="wide"
)

apply_global_styles()


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


@st.cache_data
def load_forecast_metadata():
    """Load forecast metadata."""
    filepath = "data/predictions/forecast_metadata.json"

    with open(filepath, "r") as file:
        return json.load(file)


def get_seed_label(team, playoff_seeds):
    """Return a team's playoff seed as a string."""
    team_seed = playoff_seeds[playoff_seeds["team"] == team]

    if len(team_seed) == 0:
        return ""

    seed = int(team_seed.iloc[0]["seed"])
    return f"#{seed}"


def render_team_seed_card(row):
    """Render one projected playoff seed card."""
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


def render_first_out_card(row):
    """Render one first-team-out card."""
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


def render_playoff_seed_cards(playoff_seeds, first_teams_out):
    """Render AFC/NFC playoff seeds and first teams out."""
    for conference in ["AFC", "NFC"]:
        st.markdown(f"### {conference} Projected Seeds")

        conference_seeds = playoff_seeds[
            playoff_seeds["conference"] == conference
        ].copy()

        conference_seeds = conference_seeds.sort_values("seed")

        for _, row in conference_seeds.iterrows():
            render_team_seed_card(row)

        st.markdown(f"#### {conference} First Teams Out")

        conference_out = first_teams_out[
            first_teams_out["conference"] == conference
        ].copy()

        conference_out = conference_out.sort_values("rank_out")

        for _, row in conference_out.iterrows():
            render_first_out_card(row)


def render_bracket_game(row, playoff_seeds):
    """Render one playoff game as a bracket-style card using Streamlit components."""
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


def render_conference_bracket(conference, playoff_games, playoff_seeds):
    """Render a conference bracket by round."""
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
    """Render projected Super Bowl section."""
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
    title="Playoff Predictor",
    icon="🏆",
    subtitle=(
        "View projected playoff seeds, first teams out, a projected playoff bracket, "
        "and the model's projected Super Bowl champion."
    )
)


try:
    playoff_seeds = load_playoff_seeds()
    first_teams_out = load_first_teams_out()
    playoff_games = load_playoff_games()
    super_bowl_projection = load_super_bowl_projection()
    metadata = load_forecast_metadata()

    st.markdown(
        f"""
        <div class="accent-card">
            <h4 style="margin-top: 0;">Playoff Forecast Summary</h4>
            <p class="muted-text">
                <strong>Projected Super Bowl:</strong> {super_bowl_projection["super_bowl_matchup"]}<br>
                <strong>Projected Champion:</strong> {super_bowl_projection["super_bowl_champion"]}<br>
                <strong>Forecast season:</strong> {metadata["forecast_season"]}<br>
                <strong>Last updated:</strong> {metadata["last_updated"]}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    section_header("Projected Playoff Seeds")

    st.write(
        "Division winners receive seeds 1–4 in each conference. "
        "The next three teams by projected record receive wild card spots."
    )

    seed_col1, seed_col2 = st.columns(2)

    with seed_col1:
        afc_seeds = playoff_seeds[playoff_seeds["conference"] == "AFC"].copy()
        afc_first_out = first_teams_out[
            first_teams_out["conference"] == "AFC"
        ].copy()

        st.markdown("### AFC")
        for _, row in afc_seeds.sort_values("seed").iterrows():
            render_team_seed_card(row)

        st.markdown("#### AFC First Teams Out")
        for _, row in afc_first_out.sort_values("rank_out").iterrows():
            render_first_out_card(row)

    with seed_col2:
        nfc_seeds = playoff_seeds[playoff_seeds["conference"] == "NFC"].copy()
        nfc_first_out = first_teams_out[
            first_teams_out["conference"] == "NFC"
        ].copy()

        st.markdown("### NFC")
        for _, row in nfc_seeds.sort_values("seed").iterrows():
            render_team_seed_card(row)

        st.markdown("#### NFC First Teams Out")
        for _, row in nfc_first_out.sort_values("rank_out").iterrows():
            render_first_out_card(row)

    st.divider()

    section_header("Visual Projected Playoff Bracket")

    st.write(
        "This deterministic bracket uses projected playoff seeds and projected team strength "
        "to pick winners through the Super Bowl."
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

    section_header("Detailed Playoff Tables")

    with st.expander("View projected playoff seeds table"):
        st.dataframe(
            clean_column_names(playoff_seeds),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("View first teams out table"):
        st.dataframe(
            clean_column_names(first_teams_out),
            use_container_width=True,
            hide_index=True
        )

    with st.expander("View detailed playoff games table"):
        st.dataframe(
            clean_column_names(playoff_games),
            use_container_width=True,
            hide_index=True
        )

except FileNotFoundError:
    st.error(
        "Playoff projection files not found. Run `python src/predict_upcoming.py` first."
    )