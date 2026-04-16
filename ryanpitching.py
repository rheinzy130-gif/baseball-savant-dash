import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pybaseball as pb
import streamlit as st
from scipy.stats import gaussian_kde

# -- PAGE CONFIG --
st.set_page_config(page_title="Ryan's Pitching Dashboard", layout="wide")

# -- 1. SIDEBAR: SELECT PITCHER --
st.sidebar.header("Dashboard Controls")
target_name = st.sidebar.text_input("Pitcher Name", "Jacob deGrom")
target_year = st.sidebar.selectbox("Year", [2024, 2023, 2022], index=0)


@st.cache_data
def get_data(name, year):
    first, last = name.split(" ", 1)
    lookup = pb.playerid_lookup(last, first)
    if lookup.empty:
        return None
    id_ = lookup.iloc[0]["key_mlbam"]
    return pb.statcast_pitcher(f"{year}-03-01", f"{year}-11-15", id_)


data = get_data(target_name, target_year)

if data is None or data.empty:
    st.error("No data found. Check spelling or year.")
    st.stop()

# -- 2. PERCENTILE BARS (Simulated for UI) --
st.title(f"{target_name} - {target_year} Analysis")


def draw_bar(label, val):
    color = "red" if val > 70 else ("#3b4cc0" if val < 30 else "#dddddd")
    st.markdown(f"**{label}**")
    st.markdown(
        f"""<div style="background:#333; border-radius:10px; height:12px; width:100%;">
                <div style="background:{color}; width:{val}%; height:12px; border-radius:10px;"></div>
                </div>""",
        unsafe_allow_html=True,
    )


c1, c2 = st.columns(2)
with c1:
    draw_bar("xERA", 88)
    draw_bar("Fastball Velo", 99)
with c2:
    draw_bar("K %", 95)
    draw_bar("Whiff %", 92)

st.divider()

# -- 3. THE MIDDLE ROW: LATTICE & MOVEMENT --
col_lat, col_mov = st.columns(2)

with col_lat:
    st.subheader("Pitch Sequencing (The Lattice)")
    # Group counts
    data["cnt"] = data["balls"].astype(str) + "-" + data["strikes"].astype(str)
    counts = data.groupby(["cnt", "pitch_type"]).size().reset_index(name="qty")

    # Simple interactive table/chart for now to ensure it loads
    fig_lat = px.bar(counts, x="cnt", y="qty", color="pitch_type", barmode="group")
    fig_lat.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white"
    )
    st.plotly_chart(fig_lat, use_container_width=True)

with col_mov:
    st.subheader("Movement Profile")
    # Convert pfx to inches
    data["horz"] = data["pfx_x"] * -12
    data["vert"] = data["pfx_z"] * 12

    fig_mov = px.scatter(data, x="horz", y="vert", color="pitch_type", opacity=0.4)
    fig_mov.add_vline(x=0, line_color="white")
    fig_mov.add_hline(y=0, line_color="white")
    fig_mov.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white"
    )
    st.plotly_chart(fig_mov, use_container_width=True)

# -- 4. VELOCITY DISTRIBUTION --
st.divider()
st.subheader("Pitch Distribution by Velocity")

fig_vel = go.Figure()
for p in data["pitch_type"].unique():
    v_data = data[data["pitch_type"] == p]["release_speed"].dropna()
    if len(v_data) > 5:
        kde = gaussian_kde(v_data)
        x = np.linspace(v_data.min() - 2, v_data.max() + 2, 100)
        fig_vel.add_trace(go.Scatter(x=x, y=kde(x), fill="tozeroy", name=p))

fig_vel.update_layout(
    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white"
)
st.plotly_chart(fig_vel, use_container_width=True)
