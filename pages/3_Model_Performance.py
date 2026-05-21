import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Model Performance",
    page_icon="📊",
    layout="wide"
)


@st.cache_data
def load_predictions():
    """Load saved model predictions."""
    filepath = "data/predictions/best_logistic_regression_predictions.csv"
    return pd.read_csv(filepath)


st.title("📊 Model Performance")
st.write(
    "This page evaluates how well the current NFL prediction model performed on the 2025 testing season."
)

try:
    predictions = load_predictions()

    accuracy = predictions["correct_prediction"].mean()
    total_games = len(predictions)
    correct_predictions = predictions["correct_prediction"].sum()
    incorrect_predictions = total_games - correct_predictions

    st.divider()

    st.header("Overall Performance")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Model Accuracy", f"{accuracy:.2%}")
    col2.metric("Games Tested", total_games)
    col3.metric("Correct Picks", int(correct_predictions))
    col4.metric("Incorrect Picks", int(incorrect_predictions))

    st.divider()

    st.header("Accuracy by Week")

    accuracy_by_week = (
        predictions.groupby("week")["correct_prediction"]
        .mean()
        .reset_index()
    )

    accuracy_by_week["accuracy_percent"] = (
        accuracy_by_week["correct_prediction"] * 100
    ).round(2)

    accuracy_by_week = accuracy_by_week.drop(columns=["correct_prediction"])

    st.dataframe(
        accuracy_by_week,
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(
        accuracy_by_week,
        x="week",
        y="accuracy_percent"
    )

    st.divider()

    st.header("Best and Worst Weeks")

    best_week = accuracy_by_week.sort_values(
        "accuracy_percent",
        ascending=False
    ).iloc[0]

    worst_week = accuracy_by_week.sort_values(
        "accuracy_percent",
        ascending=True
    ).iloc[0]

    col1, col2 = st.columns(2)

    with col1:
        st.success(
            f"Best Week: Week {int(best_week['week'])} "
            f"with {best_week['accuracy_percent']}% accuracy"
        )

    with col2:
        st.error(
            f"Worst Week: Week {int(worst_week['week'])} "
            f"with {worst_week['accuracy_percent']}% accuracy"
        )

    st.divider()

    st.header("Accuracy by Confidence Level")

    def get_confidence(prob):
        if prob >= 0.65 or prob <= 0.35:
            return "High"
        elif prob >= 0.57 or prob <= 0.43:
            return "Medium"
        else:
            return "Low"

    predictions["confidence"] = predictions["home_win_probability"].apply(
        get_confidence
    )

    confidence_accuracy = (
        predictions.groupby("confidence")["correct_prediction"]
        .agg(["count", "mean"])
        .reset_index()
    )

    confidence_accuracy["accuracy_percent"] = (
        confidence_accuracy["mean"] * 100
    ).round(2)

    confidence_accuracy = confidence_accuracy.rename(
        columns={
            "count": "number_of_games"
        }
    )

    confidence_accuracy = confidence_accuracy.drop(columns=["mean"])

    st.dataframe(
        confidence_accuracy,
        use_container_width=True,
        hide_index=True
    )

    st.bar_chart(
        confidence_accuracy,
        x="confidence",
        y="accuracy_percent"
    )

    st.divider()

    st.header("Prediction Results")

    predictions_display = predictions.copy()

    predictions_display["result"] = predictions_display[
        "correct_prediction"
    ].apply(lambda x: "Correct" if x else "Incorrect")

    predictions_display["home_win_probability_percent"] = (
        predictions_display["home_win_probability"] * 100
    ).round(1)

    display_columns = [
        "week",
        "home_team",
        "away_team",
        "home_score",
        "away_score",
        "predicted_winner",
        "actual_winner",
        "home_win_probability_percent",
        "confidence",
        "result"
    ]

    st.dataframe(
        predictions_display[display_columns],
        use_container_width=True,
        hide_index=True
    )

except FileNotFoundError:
    st.error(
        "Prediction file not found. Run `python src/train_model.py` first to create the predictions file."
    )