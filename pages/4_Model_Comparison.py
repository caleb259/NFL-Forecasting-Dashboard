import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Model Comparison",
    page_icon="🤖",
    layout="wide"
)


st.title("🤖 Model Comparison")

st.write(
    "This page compares the different modeling approaches tested during the project. "
    "The goal is to show how the current best model was selected."
)

st.divider()

st.header("Current Best Model")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Best Model", "Logistic Regression + Elo")

with col2:
    st.metric("Best Accuracy", "63.51%")

with col3:
    st.metric("Testing Season", "2025")

st.success(
    "Logistic Regression with Elo features is currently the best-performing model."
)

st.divider()

st.header("Model Accuracy Comparison")

model_results = pd.DataFrame(
    {
        "Model Version": [
            "Baseline random split",
            "Season-based split",
            "Recent-form features",
            "Expanded training data",
            "EPA features",
            "Logistic Regression",
            "Random Forest",
            "Gradient Boosting",
            "Logistic Regression + Elo"
        ],
        "Accuracy": [
            59.35,
            61.40,
            61.40,
            62.46,
            61.40,
            62.46,
            60.70,
            56.49,
            63.51
        ],
        "Notes": [
            "First baseline test using random train-test split",
            "More realistic train/test split by season",
            "Added last-3-game recent form features",
            "Expanded data to 2018–2025",
            "Tested play-by-play EPA features",
            "Best model from model comparison without Elo",
            "Tree-based model using same expanded features",
            "Boosting model using same expanded features",
            "Current best model with Elo rating features"
        ]
    }
)

st.dataframe(
    model_results,
    use_container_width=True,
    hide_index=True
)

st.bar_chart(
    model_results,
    x="Model Version",
    y="Accuracy"
)

st.divider()

st.header("Why the Current Model Was Chosen")

st.write(
    "The current best model was selected because it had the highest testing accuracy "
    "while still being simple and explainable."
)

st.markdown(
    """
    **Reasons for choosing Logistic Regression with Elo features:**

    - It had the highest accuracy at 63.51%.
    - It produces win probabilities, which are useful for the dashboard.
    - It is easier to explain than more complex models.
    - Elo ratings add a clear team-strength signal.
    - It fits the goal of making an explainable forecasting dashboard.
    """
)

st.divider()

st.header("Model Comparison Notes")

st.subheader("Logistic Regression")

st.write(
    "Logistic Regression performed well throughout the project. It is simple, stable, "
    "and works well with difference-based features like point differential, win percentage, and Elo rating difference."
)

st.subheader("Random Forest")

st.write(
    "Random Forest did not outperform Logistic Regression in this test. This may be because the current features are already fairly simple and linear, "
    "so the tree-based model did not gain much additional advantage."
)

st.subheader("Gradient Boosting")

st.write(
    "Gradient Boosting performed worse than the other models in this comparison. It may require more tuning or stronger features to perform better."
)

st.subheader("EPA Feature Model")

st.write(
    "EPA features were tested because EPA measures play-level efficiency. However, the first version of the EPA features did not improve accuracy. "
    "Future versions could test more detailed EPA features, such as passing EPA, rushing EPA, and success rate."
)

st.subheader("Elo Feature Model")

st.write(
    "Elo features improved the model because they provide a running team-strength rating before each game. "
    "This helped the model move from 62.46% accuracy to 63.51% accuracy."
)

st.divider()

st.header("Accuracy Improvement Over Time")

improvement_data = model_results[
    [
        "Model Version",
        "Accuracy"
    ]
].copy()

improvement_data["Experiment Number"] = range(1, len(improvement_data) + 1)

st.line_chart(
    improvement_data,
    x="Experiment Number",
    y="Accuracy"
)

st.caption(
    "The line chart shows how model accuracy changed across the main experiments."
)

st.divider()

st.header("Next Modeling Improvements")

st.write(
    "The current model is the strongest version so far, but there are still several ways to improve it."
)

st.markdown(
    """
    Planned future modeling improvements:

    - Tune the Elo settings, such as K-factor and home-field advantage
    - Add strength of schedule
    - Add player injury data
    - Add weather data
    - Add betting spread comparison
    - Predict point margin instead of only winner
    - Test more detailed EPA and success-rate features
    - Tune Random Forest and Gradient Boosting models more carefully
    """
)