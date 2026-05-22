import pandas as pd


def get_team_rating(team, projected_records):
    """
    Get a simple team rating from projected records.

    This rating is used only for deterministic playoff matchup picks.
    Higher expected wins means a stronger projected team.
    """
    team_row = projected_records[projected_records["team"] == team]

    if len(team_row) == 0:
        return 0

    return float(team_row.iloc[0]["expected_wins"])


def predict_playoff_game(home_team, away_team, projected_records):
    """
    Predict a playoff game winner using projected team strength.

    The first version uses expected wins as the main team strength signal.
    The higher-rated team wins. If tied, the home team wins.
    """
    home_rating = get_team_rating(home_team, projected_records)
    away_rating = get_team_rating(away_team, projected_records)

    if home_rating >= away_rating:
        winner = home_team
        loser = away_team
    else:
        winner = away_team
        loser = home_team

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_rating": home_rating,
        "away_rating": away_rating,
        "winner": winner,
        "loser": loser,
    }


def create_playoff_seeds(projected_records):
    """
    Create AFC and NFC playoff seeds.

    Seeds 1-4:
        Division winners, sorted by projected wins and expected wins.

    Seeds 5-7:
        Wild card teams, sorted by projected wins and expected wins.
    """
    records = projected_records.copy()

    required_cols = [
        "team",
        "conference",
        "division",
        "projected_wins",
        "projected_losses",
        "expected_wins",
        "expected_losses",
    ]

    missing_cols = [col for col in required_cols if col not in records.columns]

    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    all_seed_rows = []

    for conference in ["AFC", "NFC"]:
        conference_records = records[
            records["conference"] == conference
        ].copy()

        # Find division winners
        division_winners = (
            conference_records.sort_values(
                ["division", "projected_wins", "expected_wins"],
                ascending=[True, False, False],
            )
            .groupby("division")
            .head(1)
            .copy()
        )

        division_winners = division_winners.sort_values(
            ["projected_wins", "expected_wins"],
            ascending=False,
        ).reset_index(drop=True)

        division_winners["seed"] = range(1, len(division_winners) + 1)
        division_winners["seed_type"] = "Division Winner"

        # Find wild cards
        division_winner_teams = set(division_winners["team"])

        wild_cards = conference_records[
            ~conference_records["team"].isin(division_winner_teams)
        ].copy()

        wild_cards = wild_cards.sort_values(
            ["projected_wins", "expected_wins"],
            ascending=False,
        ).head(3).reset_index(drop=True)

        wild_cards["seed"] = range(5, 5 + len(wild_cards))
        wild_cards["seed_type"] = "Wild Card"

        conference_seeds = pd.concat(
            [division_winners, wild_cards],
            ignore_index=True,
        )

        conference_seeds = conference_seeds.sort_values("seed").reset_index(
            drop=True
        )

        all_seed_rows.append(conference_seeds)

    playoff_seeds = pd.concat(all_seed_rows, ignore_index=True)

    return playoff_seeds


def get_first_teams_out(projected_records, playoff_seeds, teams_out_count=3):
    """
    Find the first teams out of the playoff picture for each conference.
    """
    records = projected_records.copy()
    playoff_teams = set(playoff_seeds["team"])

    first_out_rows = []

    for conference in ["AFC", "NFC"]:
        conference_non_playoff = records[
            (records["conference"] == conference)
            & (~records["team"].isin(playoff_teams))
        ].copy()

        conference_non_playoff = conference_non_playoff.sort_values(
            ["projected_wins", "expected_wins"],
            ascending=False,
        ).head(teams_out_count)

        conference_non_playoff["rank_out"] = range(
            8, 8 + len(conference_non_playoff)
        )

        first_out_rows.append(conference_non_playoff)

    first_out = pd.concat(first_out_rows, ignore_index=True)

    return first_out


def simulate_conference_playoffs(conference, playoff_seeds, projected_records):
    """
    Simulate one conference playoff bracket.

    Wild Card:
        2 hosts 7
        3 hosts 6
        4 hosts 5
        1 gets a bye

    Divisional:
        1 hosts lowest remaining seed
        other two remaining teams play each other

    Conference Championship:
        Highest remaining seed hosts lowest remaining seed
    """
    seeds = playoff_seeds[
        playoff_seeds["conference"] == conference
    ].copy()

    seeds = seeds.sort_values("seed").reset_index(drop=True)

    seed_to_team = dict(zip(seeds["seed"], seeds["team"]))
    team_to_seed = dict(zip(seeds["team"], seeds["seed"]))

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

        result = predict_playoff_game(
            home_team,
            away_team,
            projected_records,
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

    result_1 = predict_playoff_game(
        divisional_game_1_home,
        divisional_game_1_away,
        projected_records,
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

    result_2 = predict_playoff_game(
        divisional_game_2_home,
        divisional_game_2_away,
        projected_records,
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

    championship_result = predict_playoff_game(
        championship_home,
        championship_away,
        projected_records,
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


def simulate_full_playoffs(projected_records):
    """
    Create playoff seeds, simulate AFC and NFC playoffs, and project Super Bowl champion.
    """
    playoff_seeds = create_playoff_seeds(projected_records)
    first_teams_out = get_first_teams_out(projected_records, playoff_seeds)

    afc_games, afc_champion = simulate_conference_playoffs(
        "AFC",
        playoff_seeds,
        projected_records,
    )

    nfc_games, nfc_champion = simulate_conference_playoffs(
        "NFC",
        playoff_seeds,
        projected_records,
    )

    playoff_games = afc_games + nfc_games

    super_bowl_result = predict_playoff_game(
        afc_champion,
        nfc_champion,
        projected_records,
    )

    playoff_games.append(
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

    playoff_games_df = pd.DataFrame(playoff_games)

    super_bowl_summary = {
        "afc_champion": afc_champion,
        "nfc_champion": nfc_champion,
        "super_bowl_matchup": f"{afc_champion} vs {nfc_champion}",
        "super_bowl_champion": super_bowl_result["winner"],
        "super_bowl_runner_up": super_bowl_result["loser"],
    }

    return playoff_seeds, first_teams_out, playoff_games_df, super_bowl_summary