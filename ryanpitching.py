import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pybaseball as pb
import requests
import streamlit as st
from scipy.stats import gaussian_kde

# -- PAGE CONFIG --
st.set_page_config(page_title="Pro Scout Dashboard", layout="wide")

# Get current year automatically
current_year = datetime.datetime.now().year


@st.cache_data
def get_data(name, year):
    try:
        # 1. Cleaner Name Lookup
        parts = name.split()
        if len(parts) < 2:
            return None
        lookup = pb.playerid_lookup(parts[-1], parts[0])
        if lookup.empty:
            return None
        id_ = lookup.iloc[0]["key_mlbam"]

        # 2. Wider date range for 2026 starts
        start = f"{year}-01-01"
        end = f"{year}-12-31"

        df = pb.statcast_pitcher(start, end, id_)
        return df
    except Exception as e:
        st.error(f"Search Error: {e}")
        return None


def get_live_pitcher(team_name):
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1"
        data = requests.get(url).json()
        for date in data.get("dates", []):
            for game in date.get("games", []):
                away = game["teams"]["away"]["team"]["name"]
                home = game["teams"]["home"]["team"]["name"]
                if team_name in away or team_name in home:
                    game_pk = game["gamePk"]
                    feed_url = (
                        f"https://statsapi.mlb.com/api/v1/game/{game_pk}/feed/live"
                    )
                    feed = requests.get(feed_url).json()
                    pitcher_info = feed["liveData"]["linescore"]["defense"]["pitcher"]
                    return pitcher_info["fullName"]
    except:
        return None
    return None


# -- SIDEBAR --
st.sidebar.header("Dashboard Controls")
target_year = st.sidebar.selectbox("Select Season", [2026, 2025, 2024], index=0)
auto_live = st.sidebar.checkbox("Sync with Live Game", value=False)
selected_team = st.sidebar.selectbox(
    "Your Team", ["Mets", "Dodgers", "Yankees", "Braves", "Padres", "Mariners"]
)

if auto_live:
    live_name = get_live_pitcher(selected_team)
    if live_name:
        target_name = live_name
        st.sidebar.success(f"Live: {target_name}")
    else:
        st.sidebar.warning("No live game found. Defaulting to Search.")
        target_name = st.sidebar.text_input("Manual Search", "Jacob deGrom")
else:
    target_name = st.sidebar.text_input("Manual Search", "Jacob deGrom")

# -- FETCH DATA --
data = get_data(target_name, target_year)

# -- MAIN UI --
st.title(f"{target_name} - {target_year} Analysis")

if data is None or data.empty:
    st.warning(
        f"No Statcast data found for {target_name} in {target_year}. Note: 2026 data can lag by 24-48 hours."
    )
    st.stop()


# 1. PERCENTILE BARS (UI Placeholders)
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

# 2. THE LATTICE & MOVEMENT ROWS
col_lat, col_mov = st.columns(2)

with col_lat:
    st.subheader("Pitch Sequencing (The Lattice)")
    # Add 'jitter' to make the dots visible on the counts
    data["balls_j"] = data["balls"] + np.random.uniform(-0.2, 0.2, len(data))
    data["strikes_j"] = data["strikes"] + np.random.uniform(-0.2, 0.2, len(data))

    fig_lat = px.scatter(
        data,
        x="balls_j",
        y="strikes_j",
        color="pitch_type",
        labels={"balls_j": "Balls", "strikes_j": "Strikes"},
        hover_data=["release_speed", "pitch_type"],
    )
    fig_lat.update_layout(
        xaxis=dict(tickvals=[0, 1, 2, 3]),
        yaxis=dict(tickvals=[0, 1, 2]),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
    )
    st.plotly_chart(fig_lat, use_container_width=True)

with col_mov:
    st.subheader("Movement Profile")
    data["horz"] = data["pfx_x"] * -12
    data["vert"] = data["pfx_z"] * 12
    fig_mov = px.scatter(data, x="horz", y="vert", color="pitch_type", opacity=0.5)
    fig_mov.add_vline(x=0, line_color="white")
    fig_mov.add_hline(y=0, line_color="white")
    fig_mov.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font_color="white"
    )
    st.plotly_chart(fig_mov, use_container_width=True)

# 3. VELOCITY DISTRIBUTION
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
