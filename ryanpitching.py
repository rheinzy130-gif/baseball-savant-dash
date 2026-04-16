# --- UPDATE THIS BLOCK ---
import datetime

import numpy as np
import pandas as pd
import plotly.express as px  # <-- FIXED THE NAMEERROR
import plotly.graph_objects as go
import pybaseball as pb
import requests
import streamlit as st
from scipy.stats import gaussian_kde

# Get current year automatically (it's 2026!)
current_year = datetime.datetime.now().year


@st.cache_data
def get_data(name, year):
    try:
        # 1. Cleaner Name Lookup
        lookup = pb.playerid_lookup(name.split()[-1], name.split()[0])
        if lookup.empty:
            return None
        id_ = lookup.iloc[0]["key_mlbam"]

        # 2. Use a wider date range to ensure we catch Spring/Early April
        # Some early April 2026 games are categorized strictly.
        start = f"{year}-01-01"
        end = f"{year}-12-31"

        df = pb.statcast_pitcher(start, end, id_)

        # 3. Debugging: This will show up in your 'Manage App' logs
        print(f"Fetched {len(df)} rows for {name} in {year}")

        return df
    except Exception as e:
        st.error(f"Search Error: {e}")
        return None


# --- UPDATE YOUR SIDEBAR YEAR SELECTION ---
# Replace your old target_year line with this one:
target_year = st.sidebar.selectbox("Select Season", [2026, 2025, 2024], index=0)


# -- LIVE GAME LOGIC --
def get_live_pitcher(team_name):
    """Checks MLB API for current live pitcher for a given team"""
    try:
        url = "https://statsapi.mlb.com/api/v1/schedule/games/?sportId=1"
        data = requests.get(url).json()
        for date in data.get("dates", []):
            for game in date.get("games", []):
                # Check if team is playing
                away = game["teams"]["away"]["team"]["name"]
                home = game["teams"]["home"]["team"]["name"]

                if team_name in away or team_name in home:
                    game_pk = game["gamePk"]
                    # Get live boxscore
                    live_url = (
                        f"https://statsapi.mlb.com/api/v1/game/{game_pk}/linescore"
                    )
                    live_data = requests.get(live_url).json()

                    # Identify if our team is pitching or hitting
                    is_home = team_name in home
                    side = "home" if is_home else "away"

                    # Note: This is simplified; in a real game, you'd pull the specific 'defense' pitcher
                    # For now, let's grab the current pitcher ID from the feed
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
st.sidebar.header("Live Feed Control")
auto_live = st.sidebar.checkbox("Sync with Live Game", value=False)
selected_team = st.sidebar.selectbox(
    "Your Team", ["Yankees", "Dodgers", "Mets", "Braves", "Red Sox"]
)  # Add yours!

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

with col_lat:
    st.subheader("Pitch Sequencing (The Lattice)")

    # Create the coordinate map for the "Plinko" look
    # We plot 'balls' on X and 'strikes' on Y
    fig_lat = px.scatter(
        data,
        x="balls",
        y="strikes",
        color="pitch_type",
        title="Pitch Selection by Count",
        symbol="pitch_type",
        height=400,
    )

    # Jitter the points so they don't all stack on top of each other
    fig_lat.update_traces(marker=dict(size=12, opacity=0.6))
    fig_lat.update_layout(
        xaxis=dict(tickvals=[0, 1, 2, 3], title="Balls"),
        yaxis=dict(tickvals=[0, 1, 2], title="Strikes"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
    )
    st.plotly_chart(fig_lat, use_container_width=True)
