import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import os

# =================================
# Streamlit UI for LifeCoachGPT
# =================================
st.set_page_config(page_title="LifeCoachGPT", page_icon="🌟", layout="centered")

st.title("🌟 LifeCoachGPT")
st.markdown("Your daily 60s motivation — insight, micro-challenge, affirmation")

# CSV for storing local mood history
HISTORY_FILE = "mood_history.csv"

# Load history if exists
if os.path.exists(HISTORY_FILE):
    history_df = pd.read_csv(HISTORY_FILE)
else:
    history_df = pd.DataFrame(columns=["date", "name", "mood", "insight", "challenge", "affirmation"])

# ------------------------
# Streak Counter
# ------------------------
def calculate_streak(df):
    if df.empty:
        return 0
    df_sorted = df.sort_values("date", ascending=False)
    dates = pd.to_datetime(df_sorted["date"]).dt.date.unique()
    today = datetime.now().date()
    streak = 0
    for i, d in enumerate(dates):
        if d == today - timedelta(days=i):
            streak += 1
        else:
            break
    return streak

streak_count = calculate_streak(history_df)
st.markdown(f"🔥 **Current Streak:** {streak_count} day{'s' if streak_count != 1 else ''}")

# ------------------------
# Inputs
# ------------------------
name = st.text_input("What's your name?")
mood = st.selectbox(
    "How are you feeling right now?",
    ["Happy", "Sad", "Motivated", "Stressed", "Neutral", "Excited", "Tired"]
)
mode = st.radio("Choose Mode", ["Daily Boost", "Custom Advice"])

# ------------------------
# Generate Advice
# ------------------------
if st.button("🚀 Get Motivation"):
    if not name.strip():
        st.warning("Please enter your name.")
    else:
        try:
            backend_url_advice = "https://lifecoachgpt-mcp.onrender.com/advice"
            backend_url_old = "https://lifecoachgpt-mcp.onrender.com/lifecoach"

            payload = {"mode": mode, "name": name, "mood": mood}

            # Try new /advice endpoint first
            try:
                response = requests.post(backend_url_advice, json=payload, timeout=10)
            except requests.RequestException:
                response = None

            # Fallback to /lifecoach if needed
            if not response or response.status_code != 200:
                payload_fallback = {"name": name, "mood": mood}
                response = requests.post(backend_url_old, json=payload_fallback, timeout=10)

            if response.status_code == 200:
                data = response.json()

                insight = data.get("insight", "No insight received.")
                challenge = data.get("micro_challenge", "No challenge received.")
                affirmation = data.get("affirmation", "No affirmation received.")

                st.subheader("📜 Life Insight")
                st.write(insight)

                st.subheader("🎯 Micro Challenge")
                st.write(challenge)

                st.subheader("💖 Affirmation")
                st.success(affirmation)

                # Save to history
                today = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_entry = pd.DataFrame([{
                    "date": today,
                    "name": name,
                    "mood": mood,
                    "insight": insight,
                    "challenge": challenge,
                    "affirmation": affirmation
                }])
                history_df = pd.concat([history_df, new_entry], ignore_index=True)
                history_df.to_csv(HISTORY_FILE, index=False)

                # Update streak
                streak_count = calculate_streak(history_df)
                st.markdown(f"🔥 **Updated Streak:** {streak_count} day{'s' if streak_count != 1 else ''}")

            else:
                st.error(f"Backend error: {response.text}")

        except Exception as e:
            st.error(f"Error connecting to backend: {e}")



# ------------------------
# Mood History
# ------------------------
st.subheader("📊 Your History")
if history_df.empty:
    st.write("No history yet — generate your first dose!")
else:
    st.dataframe(history_df.tail(10), use_container_width=True)
