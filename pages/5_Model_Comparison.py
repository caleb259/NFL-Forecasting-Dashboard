from pathlib import Path
import sys

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from style import apply_global_styles, page_header


st.set_page_config(
    page_title="Model Comparison",
    page_icon="📊",
    layout="wide",
)

apply_global_styles()

page_header(
    title="Model Comparison",
    icon="📊",
    subtitle="Measured results from the scoring-carryover experiment.",
)

st.write(
    "The selected approach uses logistic regression with scoring, "
    "recent-form, Elo, and strength-of-schedule features. "
    "Previous-season scoring averages receive the weight of four games "
    "and gradually give way to current-season results."
)

st.caption(
    "These are recorded experiment results, not live performance metrics. "
    "Accuracy measures winner picks. Lower Brier score and log loss "
    "indicate better probability predictions."
)

development_tab, followup_tab = st.tabs([
    "2021–2024 development",
    "2025 follow-up",
])

with development_tab:
    st.write(
        "Each test season uses a model trained on earlier seasons only: "
        "2018–2020 predicts 2021, and the training window expands through "
        "2018–2023 predicting 2024."
    )

    results = pd.DataFrame({
        "Approach": [
            "Original features",
            "Scoring carryover — weight 4",
            "Elo alone",
            "Home-win baseline",
        ],
        "Accuracy": ["63.29%", "63.91%", "62.76%", "54.93%"],
        "Brier score": [0.2279, 0.2247, 0.2301, 0.2477],
        "Log loss": [0.6493, 0.6415, 0.6532, 0.6886],
    })

    st.dataframe(results, hide_index=True, use_container_width=True)

    st.caption(
        "1,136 non-tied games, including postseason games. "
        "Carryover weights 0, 2, 4, and 8 were compared. "
        "Weight 4 was selected provisionally; weight 2 performed similarly."
    )

    st.write(
        "Weight 4 produced seven additional correct picks overall. "
        "Probability scores improved in three seasons and worsened "
        "slightly in 2024."
    )

with followup_tab:
    st.write(
        "Models were trained on 2018–2024 and evaluated on 2025. "
        "The carryover weight was fixed at four before this comparison."
    )

    results = pd.DataFrame({
        "Approach": [
            "Original features",
            "Scoring carryover — weight 4",
            "Elo alone",
            "Home-win baseline",
        ],
        "Accuracy": ["64.08%", "64.79%", "61.62%", "53.52%"],
        "Brier score": [0.2286, 0.2254, 0.2371, 0.2489],
        "Log loss": [0.6494, 0.6410, 0.6698, 0.6909],
    })

    st.dataframe(results, hide_index=True, use_container_width=True)

    st.caption(
        "284 non-tied games, including postseason games. "
        "2025 had already been inspected earlier in the project, "
        "so it is not a completely untouched holdout."
    )

    st.write(
        "Carryover produced 184 correct picks, compared with 182 "
        "for the original features. These results support a modest "
        "improvement, not a proven optimal setting."
    )

with st.expander("Evaluation scope and limitations"):
    st.markdown(
        """
        - Ties remain in historical feature calculations but are excluded
          from winner-classifier training and evaluation.
        - Model coefficients are fixed for each test season; pregame
          statistics update as earlier games finish.
        - These comparisons do not evaluate the margin model.
        - Current inputs do not include injuries, starting quarterbacks,
          roster changes, or coaching changes.
        - Earlier experiments used different setups and are not ranked
          against these results here.
        """
    )