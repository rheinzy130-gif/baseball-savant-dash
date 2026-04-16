import numpy as np
import pandas as pd
import plotly.express as px  # <-- FIXED THE NAMEERROR
import plotly.graph_objects as go
import pybaseball as pb
import requests
import streamlit as st
from scipy.stats import gaussian_kde


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
