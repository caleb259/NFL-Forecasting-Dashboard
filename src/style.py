import streamlit as st


def apply_global_styles():
    """
    Apply custom CSS styling across the Streamlit dashboard.
    """
    st.markdown(
        """
        <style>
        .main-title {
            font-size: 3rem;
            font-weight: 800;
            letter-spacing: -0.04em;
            margin-bottom: 0.2rem;
            color: #F8FAFC;
        }

        .page-title {
            font-size: 2.6rem !important;
            line-height: 1.1 !important;
            font-weight: 800 !important;
            letter-spacing: -0.04em !important;
            margin-bottom: 0.3rem !important;
            color: #F8FAFC !important;
        }

        .subtitle {
            font-size: 1.1rem !important;
            line-height: 1.5 !important;
            color: #CBD5E1 !important;
            margin-bottom: 1.5rem !important;
        }

        .section-header {
            font-size: 1.6rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: #F8FAFC;
        }

        .small-section-header {
            font-size: 1.25rem;
            font-weight: 700;
            margin-top: 1rem;
            margin-bottom: 0.5rem;
            color: #F8FAFC;
        }

        .muted-text {
            color: #CBD5E1;
        }

        .accent-card {
            background-color: #1E293B;
            border: 1px solid #334155;
            border-radius: 14px;
            padding: 1rem;
            margin-bottom: 1rem;
        }

        div[data-testid="stMetric"] {
            background-color: #1E293B;
            border: 1px solid #334155;
            padding: 1rem;
            border-radius: 14px;
        }

        div[data-testid="stMetric"] label {
            color: #CBD5E1;
        }

        div[data-testid="stMetric"] div {
            color: #F8FAFC;
        }

        div[data-testid="stDataFrame"] {
            border-radius: 12px;
        }

        .stAlert {
            border-radius: 12px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def page_header(title, subtitle=None, icon=None):
    """
    Display a consistent page header.
    """
    display_title = f"{icon} {title}" if icon else title

    st.markdown(
        f"""
        <h1 class="page-title">{display_title}</h1>
        """,
        unsafe_allow_html=True
    )

    if subtitle:
        st.markdown(
            f"""
            <p class="subtitle">{subtitle}</p>
            """,
            unsafe_allow_html=True
        )


def main_header(title, subtitle=None, icon=None):
    """
    Display a larger homepage-style header.
    """
    display_title = f"{icon} {title}" if icon else title

    st.markdown(
        f"""
        <div class="main-title">{display_title}</div>
        """,
        unsafe_allow_html=True
    )

    if subtitle:
        st.markdown(
            f"""
            <div class="subtitle">{subtitle}</div>
            """,
            unsafe_allow_html=True
        )


def section_header(title):
    """
    Display a consistent section header.
    """
    st.markdown(
        f"""
        <div class="section-header">{title}</div>
        """,
        unsafe_allow_html=True
    )


def small_section_header(title):
    """
    Display a smaller section header.
    """
    st.markdown(
        f"""
        <div class="small-section-header">{title}</div>
        """,
        unsafe_allow_html=True
    )