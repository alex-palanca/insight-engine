import streamlit as st
from pathlib import Path


# Configurable path to the briefings file
briefing_path = Path("output/briefings")


def get_briefing_files():
    return sorted(briefing_path.glob("*.md"), reverse=True)


def briefing_loader(file_path):

    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def get_briefing_date(file_path):
    """
    Extract date from:
    IB_2026-06-22.md

    Returns:
    2026-06-22
    """

    return file_path.stem.replace("IB_", "")

def render_icon():

    st.markdown(
        """
        <h1 style="
            text-align:center;
            color:#1E3A8A;
            font-family:monospace;
            font-size:3rem;
            margin-bottom:0;
        ">
            ISOLATE
        </h1>
        """,
        unsafe_allow_html=True
    )

# Page configuration
st.set_page_config(
    page_title="ISOLATE - Intelligence Briefing",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="collapsed"
)
render_icon()

# Custom styling
st.markdown(
    """
    <style>

    h1 {
        color: #4F8BF9;
    }

    h2 {
        color: #61AFEF;
    }

    h3 {
        color: #98C379;
    }

    </style>
    """,
    unsafe_allow_html=True,
)

# Navigation bar
with st.container():

    page = st.segmented_control(
        "Navigation",
        [
            "Today's Briefing",
            "Historical Briefings"
        ],
        default="Today's Briefing"
    )

# Today's briefing
if page == "Today's Briefing":

    briefing_files = get_briefing_files()

    if not briefing_files:

        st.warning(
            "No briefing files found."
        )

    else:

        latest_briefing = briefing_files[0]

        briefing_date = get_briefing_date(
            latest_briefing
        )

        content = briefing_loader(
            latest_briefing
        )

        # Briefing metadata
        col1, col2, col3 = st.columns([1,1,6])

        with col1:
            st.metric(
                "Date",
                briefing_date
            )

        with col2:
            st.metric(
                "Status",
                "Latest"
            )

        # Briefing content
        with st.container(border=True):

            st.markdown(content)

# Historical briefings
elif page == "Historical Briefings":

    briefing_files = get_briefing_files()

    if not briefing_files:

        st.warning(
            "No briefing files found."
        )

    else:

        selected_file = st.selectbox(
            "Select a briefing file",
            briefing_files,
            format_func=lambda x: x.stem
        )

        briefing_date = get_briefing_date(
            selected_file
        )

        content = briefing_loader(
            selected_file
        )

        # Briefing metadata
        col1, col2, col3 = st.columns([1,1,6])

        with col1:
            st.metric(
                "Date",
                briefing_date
            )

        with col2:
            st.metric(
                "Status",
                "Historical"
            )

        # Briefing content
        with st.container(border=True):

            st.markdown(content)