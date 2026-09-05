from pathlib import Path
import sys

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from style import apply_global_styles, page_header


st.set_page_config(
    page_title="How the Model Works",
    page_icon="🧠",
    layout="wide",
)

apply_global_styles()

page_header(
    title="How the Model Works",
    icon="🧠",
    subtitle="What goes into the forecasts—and what is still missing.",
)

st.header("What the model predicts")

st.write(
    "Logistic regression estimates the home team's chance of winning. "
    "Winner-model training and evaluation exclude tied games, so the "
    "probabilities are conditional on the game having a winner. "
    "The model does not estimate a separate tie probability."
)

st.header("Information used")

st.markdown(
    """
    - **Scoring:** points scored, points allowed, and point differential.
    - **Recent form:** up to three completed games from the current season.
    - **Win percentage:** completed current-season results.
    - **Elo:** a running team-strength rating updated after games.
    - **Strength of schedule:** previous opponents' win percentages
      as they stood before those matchups.

    Most inputs compare the home team with the away team.
    A positive difference does not always favor the home team:
    allowing more points, for example, is generally undesirable.
    """
)

st.header("How previous seasons contribute")

st.write(
    "Previous-season scoring averages receive the weight of four games. "
    "As current-season results accumulate, their influence increases. "
    "Previous-season averages include playoff games."
)

st.code(
    "(previous average × 4 + current-season total) "
    "/ (4 + current-season games)",
    language="text",
)

st.write(
    "For example, a team averaging 24 points last season that scores "
    "35 in its opener receives a blended scoring average of 26.2."
)

st.caption(
    "Before a team's opener, recent-form, win-percentage, and "
    "strength-of-schedule inputs start at zero, matching training. "
    "Elo carries across seasons. If previous-season scoring history "
    "is unavailable, scoring features use the original current-season "
    "calculation."
)

st.header("How forecasts are generated")

st.write(
    "The forecast script loads available completed results, retrains "
    "the models, and calculates inputs for unplayed games. All future "
    "matchups use information available at the time of that run; "
    "results of intervening games are not assumed."
)

st.write(
    "The dashboard displays saved predictions. Its existing automated "
    "workflow is scheduled weekly on Tuesday. More frequent updates "
    "and a dedicated forecast-history archive are planned."
)

st.header("How performance is measured")

st.markdown(
    """
    - **Accuracy:** the proportion of winners picked correctly.
    - **Brier score:** probability error; lower is better.
    - **Log loss:** probability error that strongly penalizes confident
      mistakes; lower is better.

    Development comparisons used expanding training windows and
    evaluated 2021–2024. The selected carryover setting was then
    checked on 2025, a season already inspected earlier in the project.

    In that 2025 evaluation, the carryover model picked **184 of 284**
    non-tied games correctly (**64.79%**), with a **0.2254 Brier score**
    and **0.6410 log loss**. These are historical experiment results,
    not a guarantee of future performance.
    """
)

st.caption(
    "See Model Comparison for baselines and evaluation details. "
    "Historical tests fix model coefficients for each test season; "
    "the forecast script retrains on available completed games."
)

with st.expander("Preventing future information from entering inputs"):
    st.write(
        "Historical features use earlier game results. Previous-season "
        "averages are attached only to the following season. "
        "Targeted checks verify scoring calculations and compare all "
        "13 model inputs between historical and upcoming-game paths "
        "on fictional examples and selected real matchups."
    )
    st.caption(
        "These checks support consistency but are not an exhaustive "
        "audit of every data source or possible matchup."
    )

with st.expander("Current limitations and secondary projections"):
    st.markdown(
        """
        - No direct injury, starting-quarterback, roster, coaching,
          weather, or betting-market inputs.
        - Probability calibration has not yet been fully assessed.
        - Strong favorites can still lose; probabilities are estimates.
        - A separate Random Forest model produces margin estimates.
          Its performance has not been reevaluated after the scoring
          changes, so older margin-error figures do not describe
          the updated model.
        - Season records and playoff projections are secondary features;
          the current priority is reliable game-winner forecasting.
        """
    )