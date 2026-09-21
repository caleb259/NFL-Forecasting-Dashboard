import json
from pathlib import Path

import pandas as pd
import streamlit as st

from forecast_archive import attach_archived_forecasts


ROOT = Path(__file__).resolve().parents[1]


def load_current_season():
    with open(
        ROOT / "data/predictions/forecast_metadata.json",
        encoding="utf-8",
    ) as handle:
        metadata = json.load(handle)

    season = int(metadata["forecast_season"])
    games = pd.read_csv(
        ROOT / f"data/processed/schedules_{season}.csv"
    )
    forecasts = pd.read_csv(
        ROOT / f"data/predictions/upcoming_{season}_predictions.csv"
    )

    games = games.loc[
        games["season"].eq(season)
        & games["game_type"].isin(["REG", "WC", "DIV", "CON", "SB"])
    ].copy()

    if games.empty:
        raise ValueError("The current-season schedule is empty.")

    games["gameday"] = pd.to_datetime(games["gameday"])
    for column in ["home_score", "away_score"]:
        games[column] = pd.to_numeric(games[column], errors="raise")

    games = games.merge(
        forecasts[
            ["game_id", "predicted_winner", "home_win_probability"]
        ],
        on="game_id",
        how="left",
        validate="one_to_one",
    )

    games["completed"] = games[
        ["home_score", "away_score"]
    ].notna().all(axis=1)

    # Remaining-game forecasts are not an archive of pregame predictions.
    games.loc[
        games["completed"],
        ["predicted_winner", "home_win_probability"],
    ] = [None, float("nan")]

    games = attach_archived_forecasts(games, season)
    return season, metadata, games


def show_schedule(games):
    table = games[
        [
            "week", "gameday", "away_team", "away_score",
            "home_team", "home_score", "completed",
            "predicted_winner", "home_win_probability", "pick_result",
        ]
    ].sort_values(["gameday", "away_team"]).copy()

    table["gameday"] = table["gameday"].dt.strftime("%Y-%m-%d")
    table["completed"] = table["completed"].map({
        True: "Completed",
        False: "Awaiting result",
    })
    table["home_win_probability"] = table[
        "home_win_probability"
    ].map(lambda value: f"{value:.1%}" if pd.notna(value) else "—")

    table = table.rename(columns={
        "week": "Week",
        "gameday": "Date",
        "away_team": "Away",
        "away_score": "Away score",
        "home_team": "Home",
        "home_score": "Home score",
        "completed": "Result status",
        "predicted_winner": "Model pick",
        "pick_result": "Pick result",
        "home_win_probability": "Home win probability",
    })
    st.dataframe(table, use_container_width=True, hide_index=True)

def show_prediction_performance(games):
    finished = games.loc[games["completed"]]
    evaluated = finished.loc[
        finished["pick_result"].isin(["Correct", "Incorrect"])
    ]

    completed_col, evaluated_col, accuracy_col = st.columns(3)
    completed_col.metric("Completed games", len(finished))
    evaluated_col.metric("Games evaluated", len(evaluated))

    accuracy_col.metric(
        "Archived pick accuracy",
        (
            f"{evaluated['pick_result'].eq('Correct').mean():.2%}"
            if not evaluated.empty else "Unavailable"
        ),
    )

    missing = int((~finished["has_archived_forecast"]).sum())
    ties = int(finished["actual_winner"].eq("Tie").sum())

    st.caption(
        "Latest archived forecast before each kickoff; forecast lead times vary. "
        f"Completed games without an archive: {missing}. "
        f"Ties excluded from accuracy: {ties}."
    )

def render_current_season(view):
    try:
        season, metadata, games = load_current_season()
    except (FileNotFoundError, ValueError, KeyError) as error:
        st.error(f"Unable to load current-season data: {error}")
        return

    st.subheader(f"{season} Season")
    st.caption(
        f"Saved data update: {metadata.get('last_updated', 'Unknown')}. "
        "Results refresh with the data update, not live during games."
    )

    completed = games.loc[games["completed"]]

    if view == "game":
        weeks = sorted(games["week"].unique())

        default_week = (
            completed["week"].max()
            if not completed.empty else min(weeks)
        )
        week = st.selectbox(
            "Week", weeks, index=weeks.index(default_week),
            key="current_breakdown_week",
        )

        choices = games.loc[games["week"].eq(week)].sort_values(
            ["gameday", "away_team"]
        ).set_index("game_id")

        game_id = st.selectbox(
            "Game",
            choices.index.tolist(),
            format_func=lambda key: (
                f"{choices.loc[key, 'away_team']} at "
                f"{choices.loc[key, 'home_team']}"
            ),
            key="current_breakdown_game",
        )
        game = choices.loc[game_id]

        st.header(f"{game['away_team']} at {game['home_team']}")
        st.caption(game["gameday"].strftime("%B %d, %Y"))

        if game["completed"]:
            away, home = st.columns(2)
            away.metric(game["away_team"], int(game["away_score"]))
            home.metric(game["home_team"], int(game["home_score"]))

            winner = (
                "Tie" if game["home_score"] == game["away_score"]
                else game["home_team"]
                if game["home_score"] > game["away_score"]
                else game["away_team"]
            )
            st.write(f"**Result:** {winner}")
            if game["has_archived_forecast"]:
                st.write(
                    f"**Archived pick:** {game['predicted_winner']} "
                    f"— {game['pick_result']}"
                )

                probability = float(game["home_win_probability"])
                away, home = st.columns(2)
                away.metric(
                    f"{game['away_team']} pregame probability",
                    f"{1 - probability:.1%}",
                )
                home.metric(
                    f"{game['home_team']} pregame probability",
                    f"{probability:.1%}",
                )

                st.caption(
                    "Latest archived forecast before kickoff. "
                    f"Saved: {game['archive_saved_at_utc']} "
                    f"• Source: {game['archive_source']}"
                )
                st.caption(
                    "Recovered Git timestamps and the current schedule "
                    "establish eligibility for these historical records. "
                    "A full archived feature breakdown is not loaded."
                )
            else:
                st.info("No eligible pregame forecast is archived for this game.")
        elif pd.notna(game["home_win_probability"]):
            st.write(f"**Predicted winner:** {game['predicted_winner']}")
            away, home = st.columns(2)
            home_probability = float(game["home_win_probability"])
            away.metric(game["away_team"], f"{1 - home_probability:.1%}")
            home.metric(game["home_team"], f"{home_probability:.1%}")
            st.caption("Latest saved forecast; no completed result available.")
        else:
            st.info("No completed result or saved forecast is available.")

    elif view == "team":
        teams = sorted(set(games["home_team"]) | set(games["away_team"]))
        team = st.selectbox("Team", teams, key="current_team")

        team_games = games.loc[
            games["home_team"].eq(team) | games["away_team"].eq(team)
        ].copy()

        played = team_games.loc[
            team_games["completed"] & team_games["game_type"].eq("REG")
        ].copy()

        points_for = played["home_score"].where(
            played["home_team"].eq(team), played["away_score"]
        )
        points_against = played["away_score"].where(
            played["home_team"].eq(team), played["home_score"]
        )

        wins = int((points_for > points_against).sum())
        losses = int((points_for < points_against).sum())
        ties = int((points_for == points_against).sum())

        st.header(f"{team} — {season}")
        record, scored, allowed = st.columns(3)
        record.metric("Regular-season record", f"{wins}-{losses}-{ties}")
        scored.metric("Points scored", int(points_for.sum()))
        allowed.metric("Points allowed", int(points_against.sum()))

        st.subheader("Predictions for this team's games")
        show_prediction_performance(team_games)

        st.subheader("Completed games")
        show_schedule(team_games.loc[team_games["completed"]])

        st.subheader("Remaining schedule and saved forecasts")
        show_schedule(team_games.loc[~team_games["completed"]])

    elif view == "performance":
        show_prediction_performance(games)
        st.subheader("Current-season prediction results")
        show_schedule(completed)

    else:
        raise ValueError(f"Unknown view: {view}")