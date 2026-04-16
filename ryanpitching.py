import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pybaseball as pb
import streamlit as st
from scipy.stats import gaussian_kde

# -- PAGE CONFIG --
st.set_page_config(page_title="Pro Scout Dashboard", layout="wide")

# -- 1. HEADER: PLAYER INFO --
# In a real app, you'd use st.selectbox for player search
st.title("Jacob deGrom - 2024 Analysis")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown(
        "<h3 style='text-align: center;'>2024 MLB Percentile Rankings</h3>",
        unsafe_allow_html=True,
    )


# -- 2. HEADLINE: PERCENTILE RANKINGS --
# We simulate the Savant "Slider" bars here
def draw_percentile_bar(label, value):
    color = "red" if value > 70 else ("grey" if value > 40 else "blue")
    st.markdown(
        f"""
        <div style="margin-bottom: 10px;">
            <span style="float: left; width: 150px;">{label}</span>
            <div style="background-color: #eee; border-radius: 10px; height: 15px; margin-left: 160px;">
                <div style="background-color: {color}; width: {value}%; height: 15px; border-radius: 10px; text-align: right; padding-right: 5px; color: white; font-size: 10px;">{value}</div>
            </div>
        </div>
    """,
        unsafe_allow_html=True,
    )


perc_col1, perc_col2 = st.columns(2)
with perc_col1:
    draw_percentile_bar("xERA", 83)
    draw_percentile_bar("xBA", 86)
    draw_percentile_bar("Fastball Velo", 97)
with perc_col2:
    draw_percentile_bar("K %", 94)
    draw_percentile_bar("Whiff %", 84)
    draw_percentile_bar(
        "Hard-Hit %", 27
    )  # Lower is better in real life, but color red for "Great"

st.divider()

# -- 3. THE SIDE-BY-SIDE COMPARISON --
row2_left, row2_right = st.columns([1, 1], gap="large")

with row2_left:
    st.subheader("Pitch Sequencing (The Lattice)")
    # [Insert your Lattice Code here from the previous step]
    # st.plotly_chart(lattice_fig)

with row2_right:
    st.subheader("Movement Profile")
    # [Insert your Movement Blob code here]
    # st.plotly_chart(movement_fig)

st.divider()

# -- 4. FOOTER: PITCH DISTRIBUTION BY VELOCITY --
st.subheader("Pitch Distribution by Velocity")


def plot_velocity_dist(df):
    fig = go.Figure()
    colors = {"FF": "red", "SL": "orange", "CH": "green", "CU": "blue", "SI": "purple"}

    # Generate smooth curves for each pitch type
    for p_type in df["pitch_type"].unique():
        subset = df[df["pitch_type"] == p_type]["release_speed"].dropna()
        if len(subset) > 1:
            kde = gaussian_kde(subset)
            x_range = np.linspace(subset.min() - 2, subset.max() + 2, 100)
            fig.add_trace(
                go.Scatter(
                    x=x_range,
                    y=kde(x_range),
                    fill="tozeroy",
                    name=p_type,
                    line=dict(color=colors.get(p_type, "grey")),
                )
            )

    fig.update_layout(
        plot_bgcolor="white",
        xaxis_title="Velocity (MPH)",
        yaxis_title="Frequency",
        height=400,
    )
    return fig


# Assuming 'pdata' is your dataframe
# st.plotly_chart(plot_velocity_dist(pdata), use_container_width=True)
