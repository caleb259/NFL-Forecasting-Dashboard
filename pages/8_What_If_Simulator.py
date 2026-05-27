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

def create_adjusted_playoff_seeds(adjusted_standings):
    """
    Create adjusted AFC and NFC playoff seeds from adjusted standings.

    Seeds 1-4:
        Division winners sorted by adjusted wins and expected wins.

    Seeds 5-7:
        Wild card teams sorted by adjusted wins and expected wins.
    """
    standings = adjusted_standings.copy()

    all_seed_rows = []

    for conference in ["AFC", "NFC"]:
        conference_standings = standings[
            standings["conference"] == conference
        ].copy()

        division_winners = (
            conference_standings.sort_values(
                ["division", "adjusted_wins", "expected_wins"],
                ascending=[True, False, False],
            )
            .groupby("division")
            .head(1)
            .copy()
        )

        division_winners = division_winners.sort_values(
            ["adjusted_wins", "expected_wins"],
            ascending=False,
        ).reset_index(drop=True)

        division_winners["adjusted_seed"] = range(1, len(division_winners) + 1)
        division_winners["seed_type"] = "Division Winner"

        division_winner_teams = set(division_winners["team"])

        wild_cards = conference_standings[
            ~conference_standings["team"].isin(division_winner_teams)
        ].copy()

        wild_cards = wild_cards.sort_values(
            ["adjusted_wins", "expected_wins"],
            ascending=False,
        ).head(3).reset_index(drop=True)

        wild_cards["adjusted_seed"] = range(5, 5 + len(wild_cards))
        wild_cards["seed_type"] = "Wild Card"

        conference_seeds = pd.concat(
            [division_winners, wild_cards],
            ignore_index=True,
        )

        conference_seeds = conference_seeds.sort_values(
            "adjusted_seed"
        ).reset_index(drop=True)

        all_seed_rows.append(conference_seeds)

    adjusted_playoff_seeds = pd.concat(all_seed_rows, ignore_index=True)

    return adjusted_playoff_seeds


def create_adjusted_first_teams_out(adjusted_standings, adjusted_playoff_seeds):
    """
    Create adjusted first teams out for AFC and NFC.
    """
    playoff_teams = set(adjusted_playoff_seeds["team"])

    first_out_rows = []

    for conference in ["AFC", "NFC"]:
        conference_non_playoff = adjusted_standings[
            (adjusted_standings["conference"] == conference)
            & (~adjusted_standings["team"].isin(playoff_teams))
        ].copy()

        conference_non_playoff = conference_non_playoff.sort_values(
            ["adjusted_wins", "expected_wins"],
            ascending=False,
        ).head(3).reset_index(drop=True)

        conference_non_playoff["adjusted_rank_out"] = range(
            8,
            8 + len(conference_non_playoff)
        )

        first_out_rows.append(conference_non_playoff)

    adjusted_first_out = pd.concat(first_out_rows, ignore_index=True)

    return adjusted_first_out


def get_adjusted_playoff_status(selected_team, adjusted_playoff_seeds, adjusted_first_out):
    """
    Return adjusted playoff status for the selected team.
    """
    seed_row = adjusted_playoff_seeds[
        adjusted_playoff_seeds["team"] == selected_team
    ]

    if len(seed_row) > 0:
        seed = int(seed_row.iloc[0]["adjusted_seed"])
        seed_type = seed_row.iloc[0]["seed_type"]

        return {
            "status": "Projected Playoff Team",
            "detail": f"#{seed} seed, {seed_type}",
        }

    first_out_row = adjusted_first_out[
        adjusted_first_out["team"] == selected_team
    ]

    if len(first_out_row) > 0:
        rank_out = int(first_out_row.iloc[0]["adjusted_rank_out"])

        return {
            "status": "First Teams Out",
            "detail": f"Projected #{rank_out} in conference",
        }

    return {
        "status": "Outside Playoff Picture",
        "detail": "Not currently projected in playoff race",
    }

def get_adjusted_team_strength(team, adjusted_standings):
    """
    Get a simple adjusted team strength value.

    This uses adjusted wins first and expected wins second.
    """
    team_row = adjusted_standings[adjusted_standings["team"] == team]

    if len(team_row) == 0:
        return 0

    row = team_row.iloc[0]

    return float(row["adjusted_wins"]) + (float(row["expected_wins"]) / 100)


def predict_adjusted_playoff_game(home_team, away_team, adjusted_standings):
    """
    Predict an adjusted playoff game winner.

    The higher adjusted team strength wins.
    If tied, the home team wins.
    """
    home_strength = get_adjusted_team_strength(home_team, adjusted_standings)
    away_strength = get_adjusted_team_strength(away_team, adjusted_standings)

    if home_strength >= away_strength:
        winner = home_team
        loser = away_team
    else:
        winner = away_team
        loser = home_team

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_strength": home_strength,
        "away_strength": away_strength,
        "winner": winner,
        "loser": loser,
    }


def simulate_adjusted_conference_playoffs(
    conference,
    adjusted_playoff_seeds,
    adjusted_standings
):
    """
    Simulate an adjusted playoff bracket for one conference.

    Wild Card:
        2 hosts 7
        3 hosts 6
        4 hosts 5
        1 gets a bye

    Divisional:
        1 hosts lowest remaining seed
        Other two remaining teams play each other

    Conference Championship:
        Highest remaining seed hosts lowest remaining seed
    """
    seeds = adjusted_playoff_seeds[
        adjusted_playoff_seeds["conference"] == conference
    ].copy()

    seeds = seeds.sort_values("adjusted_seed").reset_index(drop=True)

    seed_to_team = dict(zip(seeds["adjusted_seed"], seeds["team"]))
    team_to_seed = dict(zip(seeds["team"], seeds["adjusted_seed"]))

    games = []

    # Wild Card Round
    wild_card_matchups = [
        (2, 7),
        (3, 6),
        (4, 5),
    ]

    wild_card_winners = [seed_to_team[1]]

    for home_seed, away_seed in wild_card_matchups:
        home_team = seed_to_team[home_seed]
        away_team = seed_to_team[away_seed]

        result = predict_adjusted_playoff_game(
            home_team,
            away_team,
            adjusted_standings,
        )

        games.append(
            {
                "conference": conference,
                "round": "Wild Card",
                "home_seed": home_seed,
                "away_seed": away_seed,
                "home_team": home_team,
                "away_team": away_team,
                "winner": result["winner"],
                "loser": result["loser"],
            }
        )

        wild_card_winners.append(result["winner"])

    # Divisional Round
    remaining_teams = wild_card_winners.copy()

    remaining_teams_sorted = sorted(
        remaining_teams,
        key=lambda team: team_to_seed[team],
    )

    one_seed_team = seed_to_team[1]

    other_remaining = [
        team for team in remaining_teams_sorted if team != one_seed_team
    ]

    lowest_remaining = sorted(
        other_remaining,
        key=lambda team: team_to_seed[team],
        reverse=True,
    )[0]

    divisional_game_1_home = one_seed_team
    divisional_game_1_away = lowest_remaining

    result_1 = predict_adjusted_playoff_game(
        divisional_game_1_home,
        divisional_game_1_away,
        adjusted_standings,
    )

    games.append(
        {
            "conference": conference,
            "round": "Divisional",
            "home_seed": team_to_seed[divisional_game_1_home],
            "away_seed": team_to_seed[divisional_game_1_away],
            "home_team": divisional_game_1_home,
            "away_team": divisional_game_1_away,
            "winner": result_1["winner"],
            "loser": result_1["loser"],
        }
    )

    remaining_for_second_game = [
        team
        for team in other_remaining
        if team != lowest_remaining
    ]

    remaining_for_second_game = sorted(
        remaining_for_second_game,
        key=lambda team: team_to_seed[team],
    )

    divisional_game_2_home = remaining_for_second_game[0]
    divisional_game_2_away = remaining_for_second_game[1]

    result_2 = predict_adjusted_playoff_game(
        divisional_game_2_home,
        divisional_game_2_away,
        adjusted_standings,
    )

    games.append(
        {
            "conference": conference,
            "round": "Divisional",
            "home_seed": team_to_seed[divisional_game_2_home],
            "away_seed": team_to_seed[divisional_game_2_away],
            "home_team": divisional_game_2_home,
            "away_team": divisional_game_2_away,
            "winner": result_2["winner"],
            "loser": result_2["loser"],
        }
    )

    # Conference Championship
    championship_teams = [result_1["winner"], result_2["winner"]]

    championship_teams = sorted(
        championship_teams,
        key=lambda team: team_to_seed[team],
    )

    championship_home = championship_teams[0]
    championship_away = championship_teams[1]

    championship_result = predict_adjusted_playoff_game(
        championship_home,
        championship_away,
        adjusted_standings,
    )

    games.append(
        {
            "conference": conference,
            "round": "Conference Championship",
            "home_seed": team_to_seed[championship_home],
            "away_seed": team_to_seed[championship_away],
            "home_team": championship_home,
            "away_team": championship_away,
            "winner": championship_result["winner"],
            "loser": championship_result["loser"],
        }
    )

    conference_champion = championship_result["winner"]

    return games, conference_champion


def simulate_adjusted_full_playoffs(adjusted_playoff_seeds, adjusted_standings):
    """
    Simulate the full adjusted playoffs and Super Bowl.
    """
    afc_games, afc_champion = simulate_adjusted_conference_playoffs(
        "AFC",
        adjusted_playoff_seeds,
        adjusted_standings,
    )

    nfc_games, nfc_champion = simulate_adjusted_conference_playoffs(
        "NFC",
        adjusted_playoff_seeds,
        adjusted_standings,
    )

    adjusted_playoff_games = afc_games + nfc_games

    super_bowl_result = predict_adjusted_playoff_game(
        afc_champion,
        nfc_champion,
        adjusted_standings,
    )

    adjusted_playoff_games.append(
        {
            "conference": "NFL",
            "round": "Super Bowl",
            "home_seed": None,
            "away_seed": None,
            "home_team": afc_champion,
            "away_team": nfc_champion,
            "winner": super_bowl_result["winner"],
            "loser": super_bowl_result["loser"],
        }
    )

    adjusted_playoff_games_df = pd.DataFrame(adjusted_playoff_games)

    adjusted_super_bowl_summary = {
        "afc_champion": afc_champion,
        "nfc_champion": nfc_champion,
        "super_bowl_matchup": f"{afc_champion} vs {nfc_champion}",
        "super_bowl_champion": super_bowl_result["winner"],
        "super_bowl_runner_up": super_bowl_result["loser"],
    }

    return adjusted_playoff_games_df, adjusted_super_bowl_summary

def get_adjusted_seed_label(team, adjusted_playoff_seeds):
    """
    Return adjusted seed label for a team.
    """
    team_seed = adjusted_playoff_seeds[
        adjusted_playoff_seeds["team"] == team
    ]

    if len(team_seed) == 0:
        return ""

    seed = int(team_seed.iloc[0]["adjusted_seed"])

    return f"#{seed}"


def render_adjusted_bracket_game(row, adjusted_playoff_seeds):
    """
    Render one adjusted playoff game card.
    """
    home_team = row["home_team"]
    away_team = row["away_team"]
    winner = row["winner"]

    home_seed = get_adjusted_seed_label(home_team, adjusted_playoff_seeds)
    away_seed = get_adjusted_seed_label(away_team, adjusted_playoff_seeds)

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

        st.success(f"Adjusted Winner: {winner}")


def render_adjusted_conference_bracket(
    conference,
    adjusted_playoff_games,
    adjusted_playoff_seeds
):
    """
    Render adjusted conference playoff bracket.
    """
    conference_games = adjusted_playoff_games[
        adjusted_playoff_games["conference"] == conference
    ].copy()

    st.markdown(f"### {conference} Adjusted Bracket")

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
                    render_adjusted_bracket_game(
                        row,
                        adjusted_playoff_seeds
                    )


def render_adjusted_super_bowl(
    adjusted_playoff_games,
    adjusted_playoff_seeds,
    adjusted_super_bowl_summary
):
    """
    Render adjusted Super Bowl projection.
    """
    super_bowl_game = adjusted_playoff_games[
        adjusted_playoff_games["round"] == "Super Bowl"
    ].copy()

    st.markdown("### Adjusted Super Bowl")

    if len(super_bowl_game) > 0:
        render_adjusted_bracket_game(
            super_bowl_game.iloc[0],
            adjusted_playoff_seeds
        )

    sb_col1, sb_col2, sb_col3 = st.columns(3)

    with sb_col1:
        st.metric(
            "Adjusted AFC Champion",
            adjusted_super_bowl_summary["afc_champion"]
        )

    with sb_col2:
        st.metric(
            "Adjusted NFC Champion",
            adjusted_super_bowl_summary["nfc_champion"]
        )

    with sb_col3:
        st.metric(
            "Adjusted Champion",
            adjusted_super_bowl_summary["super_bowl_champion"]
        )


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

    win_change = adjusted_wins - original_wins
    loss_change = adjusted_losses - original_losses

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

    adjusted_playoff_seeds = create_adjusted_playoff_seeds(adjusted_standings)

    adjusted_first_out = create_adjusted_first_teams_out(
        adjusted_standings,
        adjusted_playoff_seeds
    )

    adjusted_playoff_status = get_adjusted_playoff_status(
        selected_team,
        adjusted_playoff_seeds,
        adjusted_first_out
    )

    adjusted_playoff_games, adjusted_super_bowl_summary = (
        simulate_adjusted_full_playoffs(
            adjusted_playoff_seeds,
            adjusted_standings
        )
    )

    st.divider()

    section_header("Adjusted Projection")

    acol1, acol2, acol3, acol4 = st.columns(4)

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

    acol4.metric(
        "Adjusted Playoff Status",
        adjusted_playoff_status["status"]
    )

    st.info(adjusted_playoff_status["detail"])

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

    section_header("Adjusted Playoff Picture")

    st.write(
        "This section recalculates playoff seeds using the adjusted league standings from your scenario."
    )

    playoff_col1, playoff_col2 = st.columns(2)

    with playoff_col1:
        st.markdown("### AFC Adjusted Seeds")

        afc_adjusted_seeds = adjusted_playoff_seeds[
            adjusted_playoff_seeds["conference"] == "AFC"
        ].copy()

        afc_adjusted_display = afc_adjusted_seeds[
            [
                "adjusted_seed",
                "team",
                "division",
                "seed_type",
                "original_record",
                "adjusted_record",
                "win_change",
                "loss_change",
                "expected_wins",
                "expected_losses",
            ]
        ].copy()

        st.dataframe(
            clean_column_names(afc_adjusted_display),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### AFC Adjusted First Teams Out")

        afc_adjusted_out = adjusted_first_out[
            adjusted_first_out["conference"] == "AFC"
        ].copy()

        afc_adjusted_out_display = afc_adjusted_out[
            [
                "adjusted_rank_out",
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
            clean_column_names(afc_adjusted_out_display),
            use_container_width=True,
            hide_index=True
        )

    with playoff_col2:
        st.markdown("### NFC Adjusted Seeds")

        nfc_adjusted_seeds = adjusted_playoff_seeds[
            adjusted_playoff_seeds["conference"] == "NFC"
        ].copy()

        nfc_adjusted_display = nfc_adjusted_seeds[
            [
                "adjusted_seed",
                "team",
                "division",
                "seed_type",
                "original_record",
                "adjusted_record",
                "win_change",
                "loss_change",
                "expected_wins",
                "expected_losses",
            ]
        ].copy()

        st.dataframe(
            clean_column_names(nfc_adjusted_display),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### NFC Adjusted First Teams Out")

        nfc_adjusted_out = adjusted_first_out[
            adjusted_first_out["conference"] == "NFC"
        ].copy()

        nfc_adjusted_out_display = nfc_adjusted_out[
            [
                "adjusted_rank_out",
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
            clean_column_names(nfc_adjusted_out_display),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    section_header("Adjusted Playoff Bracket")

    st.write(
        "This bracket uses the adjusted playoff seeds from your scenario and projects winners through the Super Bowl."
    )

    render_adjusted_conference_bracket(
        "AFC",
        adjusted_playoff_games,
        adjusted_playoff_seeds
    )

    st.divider()

    render_adjusted_conference_bracket(
        "NFC",
        adjusted_playoff_games,
        adjusted_playoff_seeds
    )

    st.divider()

    render_adjusted_super_bowl(
        adjusted_playoff_games,
        adjusted_playoff_seeds,
        adjusted_super_bowl_summary
    )

    st.success(
        f"Adjusted Super Bowl Champion: {adjusted_super_bowl_summary['super_bowl_champion']}"
    )

    with st.expander("View adjusted playoff game table"):
        st.dataframe(
            clean_column_names(adjusted_playoff_games),
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
        "The simulator recalculates adjusted league records, division standings, conference standings, "
        "playoff seeds, first teams out, playoff bracket, conference champions, and projected Super Bowl champion."
    )

    st.write(
        "This is still a deterministic simulator. It does not run thousands of simulations or assign playoff odds yet. "
        "A future version could add Monte Carlo simulation to estimate playoff and Super Bowl probabilities."
    )

except FileNotFoundError:
    st.error(
        "Forecast files not found. Run `python src/predict_upcoming.py` first."
    )