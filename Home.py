import pandas as pd
import streamlit as st
import json
import sys
sys.path.append("src")

from team_info import get_team_logo, get_team_name, get_team_primary_color
from style import apply_global_styles, main_header, section_header, clean_column_names


st.set_page_config(
    page_title="Fourth & Forecast",
    page_icon="🏈",
    layout="wide"
)

apply_global_styles()



@st.cache_data
def load_predictions():
    """Load saved model predictions."""
    filepath = "data/predictions/best_logistic_regression_predictions.csv"
    return pd.read_csv(filepath)

@st.cache_data
def load_forecast_metadata():
    """Load forecast metadata."""
    filepath = "data/predictions/forecast_metadata.json"

    with open(filepath, "r") as file:
        return json.load(file)
    
@st.cache_data
def load_upcoming_predictions():
    """Load upcoming 2026 predictions."""
    filepath = "data/predictions/upcoming_2026_predictions.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_projected_records():
    """Load projected 2026 records."""
    filepath = "data/predictions/projected_2026_records.csv"
    return pd.read_csv(filepath)


@st.cache_data
def load_super_bowl_projection():
    """Load projected Super Bowl summary."""
    filepath = "data/predictions/projected_super_bowl.json"

    with open(filepath, "r") as file:
        return json.load(file)

def get_forecast_hub_stats():
    """Create homepage forecast hub stats."""
    upcoming_predictions = load_upcoming_predictions()
    projected_records = load_projected_records()
    super_bowl_projection = load_super_bowl_projection()
    metadata = load_forecast_metadata()

    upcoming_predictions["predicted_margin_abs"] = (
        upcoming_predictions["predicted_home_margin"].abs()
    )

    upcoming_predictions["game_label"] = (
        upcoming_predictions["away_team"] + " at " + upcoming_predictions["home_team"]
    )

    closest_game = upcoming_predictions.sort_values(
        "predicted_margin_abs",
        ascending=True
    ).iloc[0]

    largest_margin_game = upcoming_predictions.sort_values(
        "predicted_margin_abs",
        ascending=False
    ).iloc[0]

    top_projected_team = projected_records.sort_values(
        ["projected_wins", "expected_wins"],
        ascending=False
    ).iloc[0]

    return {
        "super_bowl_champion": super_bowl_projection["super_bowl_champion"],
        "afc_champion": super_bowl_projection["afc_champion"],
        "nfc_champion": super_bowl_projection["nfc_champion"],
        "top_projected_team": top_projected_team["team"],
        "top_projected_record": f"{int(top_projected_team['projected_wins'])}-{int(top_projected_team['projected_losses'])}",
        "closest_game": closest_game["game_label"],
        "closest_game_margin": closest_game["predicted_margin_text"],
        "largest_margin_game": largest_margin_game["game_label"],
        "largest_margin": largest_margin_game["predicted_margin_text"],
        "last_updated": metadata["last_updated"],
    }

def get_forecast_storylines():
    """Create plain-English forecast storylines from 2026 forecast data."""
    upcoming_predictions = load_upcoming_predictions()
    projected_records = load_projected_records()
    super_bowl_projection = load_super_bowl_projection()

    upcoming_predictions["predicted_margin_abs"] = (
        upcoming_predictions["predicted_home_margin"].abs()
    )

    upcoming_predictions["game_label"] = (
        upcoming_predictions["away_team"] + " at " + upcoming_predictions["home_team"]
    )

    projected_records["record_label"] = (
        projected_records["projected_wins"].astype(int).astype(str)
        + "-"
        + projected_records["projected_losses"].astype(int).astype(str)
    )

    top_team = projected_records.sort_values(
        ["projected_wins", "expected_wins"],
        ascending=False
    ).iloc[0]

    closest_game = upcoming_predictions.sort_values(
        "predicted_margin_abs",
        ascending=True
    ).iloc[0]

    largest_margin_game = upcoming_predictions.sort_values(
        "predicted_margin_abs",
        ascending=False
    ).iloc[0]

    most_confident_game = upcoming_predictions.sort_values(
        "winner_win_probability",
        ascending=False
    ).iloc[0]

    upset_games = upcoming_predictions[
        upcoming_predictions["upset_alert"] == True
    ].copy()

    if len(upset_games) > 0:
        top_upset = upset_games.sort_values(
            "winner_win_probability",
            ascending=False
        ).iloc[0]

        upset_story = (
            f"{top_upset['predicted_winner']} is flagged as an upset pick in "
            f"{top_upset['game_label']}."
        )
    else:
        upset_story = "No major upset alerts are currently flagged in the forecast."

    division_summary = (
        projected_records.groupby("division")
        .agg(
            top_projected_wins=("projected_wins", "max"),
            bottom_projected_wins=("projected_wins", "min"),
            avg_expected_wins=("expected_wins", "mean")
        )
        .reset_index()
    )

    division_summary["win_gap"] = (
        division_summary["top_projected_wins"]
        - division_summary["bottom_projected_wins"]
    )

    most_competitive_division = division_summary.sort_values(
        ["win_gap", "avg_expected_wins"],
        ascending=[True, False]
    ).iloc[0]

    storylines = [
        {
            "title": "Projected Super Bowl Champion",
            "text": (
                f"{super_bowl_projection['super_bowl_champion']} is currently projected "
                f"to win the Super Bowl over a projected matchup of "
                f"{super_bowl_projection['afc_champion']} vs {super_bowl_projection['nfc_champion']}."
            ),
        },
        {
            "title": "Top Projected Regular-Season Team",
            "text": (
                f"{top_team['team']} has the best projected record at "
                f"{top_team['record_label']}, with an expected record of "
                f"{top_team['expected_wins']}-{top_team['expected_losses']}."
            ),
        },
        {
            "title": "Closest Projected Matchup",
            "text": (
                f"{closest_game['game_label']} is the closest projected game, with a projected margin of "
                f"{closest_game['predicted_margin_text']}."
            ),
        },
        {
            "title": "Largest Projected Margin",
            "text": (
                f"{largest_margin_game['game_label']} has the largest projected margin, with "
                f"{largest_margin_game['predicted_margin_text']}."
            ),
        },
        {
            "title": "Most Confident Forecast",
            "text": (
                f"The model is most confident in {most_confident_game['predicted_winner']} "
                f"winning {most_confident_game['game_label']}, with a winner win probability of "
                f"{most_confident_game['winner_win_probability']:.1%}."
            ),
        },
        {
            "title": "Most Competitive Division",
            "text": (
                f"{most_competitive_division['division']} currently looks like the most competitive division, "
                f"with only a {int(most_competitive_division['win_gap'])}-win gap between its top and bottom projected teams."
            ),
        },
        {
            "title": "Upset Watch",
            "text": upset_story,
        },
    ]

    return storylines

def render_storyline_card(number, title, text):
    """Render one forecast storyline card."""
    with st.container(border=True):
        st.markdown(f"### {number}. {title}")
        st.write(text)


def render_forecast_hub_card(title, main_value, subtext=None, team=None):
    """Render one forecast hub card."""
    team_logo = get_team_logo(team) if team else None

    with st.container(border=True):
        if team_logo:
            st.image(team_logo, width=70)

        st.markdown(f"**{title}**")
        st.markdown(f"### {main_value}")

        if subtext:
            st.caption(subtext)

def get_next_upcoming_week(upcoming_predictions):
    """
    Return the earliest week that still has pending upcoming games.
    """
    pending_games = upcoming_predictions[
        upcoming_predictions["status"] == "Pending"
    ].copy()

    if len(pending_games) == 0:
        return upcoming_predictions["week"].min()

    return pending_games["week"].min()


main_header(
    title="Fourth & Forecast",
    icon="🏈",
    subtitle="Explainable NFL game predictions powered by team stats, Elo ratings, strength of schedule, and machine learning."
)

try:
    metadata = load_forecast_metadata()

    last_updated_text = metadata["last_updated"]
    forecast_season = metadata["forecast_season"]
    upcoming_games = metadata["upcoming_games_forecasted"]

    win_model_name = metadata.get(
        "win_model",
        "Logistic Regression with Elo and strength of schedule features"
    )

    margin_model_name = metadata.get(
        "margin_model",
        "Random Forest Regressor"
    )

    margin_model_mae = metadata.get(
        "margin_model_mae",
        "Not available"
    )

except FileNotFoundError:
    last_updated_text = "Not available"
    forecast_season = "2026"
    upcoming_games = "Not available"
    win_model_name = "Logistic Regression with Elo and strength of schedule features"
    margin_model_name = "Random Forest Regressor"
    margin_model_mae = "Not available"

st.markdown(
    f"""
    <div class="accent-card">
        <h3 style="margin-top: 0;">🔮 {forecast_season} Upcoming Forecasts</h3>
        <p class="muted-text">
            Explore upcoming NFL matchups, predicted winners, and each team's
            estimated chance of winning.
        </p>
        <p class="muted-text">
            <strong>Win model:</strong> {win_model_name}<br>
            <strong>Upcoming games forecasted:</strong> {upcoming_games}<br>
            <strong>Forecast last updated:</strong> {last_updated_text}
        </p>
        <p class="muted-text">
            Use the <strong>Upcoming Forecasts</strong> page in the sidebar to explore the full schedule predictions.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

try:
    upcoming_predictions = load_upcoming_predictions()

    upcoming_predictions["gameday"] = pd.to_datetime(
        upcoming_predictions["gameday"]
    )

    next_week = get_next_upcoming_week(upcoming_predictions)

    next_week_predictions = upcoming_predictions[
        upcoming_predictions["week"] == next_week
    ].copy()

    next_week_predictions = next_week_predictions.sort_values(
        ["gameday", "away_team", "home_team"]
    )

    section_header(f"Week {next_week} Upcoming Forecasts")

    st.write(
        "Current winner forecasts for the next scheduled week. "
        "Open Upcoming Forecasts to browse other weeks."
    )

    display_columns = [
        "week",
        "gameday",
        "away_team",
        "home_team",
        "predicted_winner",
        "winner_win_probability",
        "status",
    ]

    upcoming_table = next_week_predictions[display_columns].copy()

    upcoming_table["winner_win_probability"] = (
        upcoming_table["winner_win_probability"] * 100
    ).round(1)

    st.dataframe(
        clean_column_names(upcoming_table),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Upcoming Game Cards")

    for _, row in next_week_predictions.iterrows():
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
                st.write(f"Game Date: **{row['gameday'].date()}**")

            with col3:
                st.info(row["status"])

except FileNotFoundError:
    st.info(
        "Upcoming forecast files are not available yet. Run `python src/predict_upcoming.py` to generate them."
    )

section_header("Dashboard Sections")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
        <div class="accent-card">
            <h4>🔮 Upcoming Forecasts</h4>
            <p class="muted-text">
                Browse upcoming matchups, predicted winners, and win probabilities by week.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        """
        <div class="accent-card">
            <h4>🏈 Game Breakdown</h4>
            <p class="muted-text">
                Select one matchup and review the model inputs, prediction, and feature values.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        """
        <div class="accent-card">
            <h4>📊 Model Performance</h4>
            <p class="muted-text">
                Review model accuracy, weekly performance, confidence levels, and prediction results.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

st.write(
    "This dashboard uses NFL team data and machine learning to predict game outcomes. "
    "The current model was evaluated on the 2025 season and is now also used to generate "
    "upcoming 2026 season forecasts."
)

st.divider()

# Load predictions
try:
    predictions = load_predictions()

    # Summary metrics
    accuracy = predictions["correct_prediction"].mean()
    total_games = len(predictions)
    correct_predictions = predictions["correct_prediction"].sum()
    incorrect_predictions = total_games - correct_predictions

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Model Accuracy", f"{accuracy:.2%}")
    col2.metric("Games Tested", total_games)
    col3.metric("Correct Picks", int(correct_predictions))
    col4.metric("Incorrect Picks", int(incorrect_predictions))

    st.divider()

    section_header("2025 Historical Model Evaluation")

    # Week selector
    weeks = sorted(predictions["week"].unique())

    selected_week = st.selectbox(
        "Select a week",
        weeks
    )

    week_predictions = predictions[predictions["week"] == selected_week].copy()

    # Format probability
    week_predictions["home_win_probability_percent"] = (
        week_predictions["home_win_probability"] * 100
    ).round(1)

    week_predictions["result"] = week_predictions["correct_prediction"].apply(
        lambda x: "Correct" if x else "Incorrect"
    )

    display_columns = [
        "week",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "predicted_winner",
        "actual_winner",
        "home_win_probability_percent",
        "result"
    ]

    st.dataframe(
        clean_column_names(week_predictions[display_columns]),
        use_container_width=True,
        hide_index=True
    )

    st.write(
    "This section shows how the model performed on completed 2025 test games. "
    "It is used for model evaluation, while the section above shows upcoming 2026 forecasts."
)

    with st.expander("View 2025 evaluation game cards"):
        st.markdown("### 2025 Evaluation Game Cards")

        for _, row in week_predictions.iterrows():
            result_text = "Correct" if row["correct_prediction"] else "Incorrect"

            home_team = row["home_team"]
            away_team = row["away_team"]

            home_logo = get_team_logo(home_team)
            away_logo = get_team_logo(away_team)

            home_name = get_team_name(home_team)
            away_name = get_team_name(away_team)

            card_color = get_team_primary_color(home_team)

            with st.container(border=True):
                st.markdown(
                    f"""
                    <div style="
                        border-left: 8px solid {card_color};
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
                        st.write(f"{int(row['away_score'])} points")

                    with logo_col2:
                        if home_logo:
                            st.image(home_logo, width=80)
                        st.write(f"**{home_team}**")
                        st.write(f"{int(row['home_score'])} points")

                with col2:
                    st.write(f"Predicted Winner: **{row['predicted_winner']}**")
                    st.write(f"Actual Winner: **{row['actual_winner']}**")
                    st.write(
                        f"Home Win Probability: "
                        f"**{row['home_win_probability_percent']}%**"
                    )

                with col3:
                    if row["correct_prediction"]:
                        st.success(result_text)
                    else:
                        st.error(result_text)

    

    st.caption(
        "Home win probability represents the model's estimated chance that the home team wins."
    )

    st.divider()

    section_header("Model Details")

    st.write(
        "Current best model: **Logistic Regression**"
    )

    st.write(
        "Training seasons: **2018–2024**"
    )

    st.write(
        "Testing season: **2025**"
    )

    st.write(
        "Current features include season-long differences, recent-form differences, Elo rating differences, "
        "and strength of schedule differences between the home and away teams."
    )

    feature_list = [
        "Average points scored difference",
        "Average points allowed difference",
        "Average point differential difference",
        "Win percentage difference",
        "Last 3 games average points scored difference",
        "Last 3 games average points allowed difference",
        "Last 3 games average point differential difference",
        "Last 3 games win percentage difference",
        "Elo rating difference",
        "Elo rating difference with home-field advantage",
        "Elo-based home win probability",
        "Strength of schedule difference",
        "Current opponent win percentage difference"
    ]

    st.markdown("### Features Used")

    for feature in feature_list:
        st.markdown(f"- {feature}")

except FileNotFoundError:
    st.error(
        "Prediction file not found. Run `python src/train_model.py` first to create the predictions file."
    )