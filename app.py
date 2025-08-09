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
    history_df = pd.DataFrame(columns=["date", "name", "mode", "mood", "topic", "insight", "challenge", "affirmation"])

# ------------------------
# Streak Counter Logic
# ------------------------
def calculate_streak(df):
    if df.empty:
        return 0
    df_sorted = df.sort_values("date", ascending=False)
    dates = [datetime.strptime(d, "%Y-%m-%d %H:%M") for d in df_sorted["date"]]
    streak = 1
    for i in range(1, len(dates)):
        if (dates[i-1] - dates[i]).days == 1:
            streak += 1
        elif (dates[i-1] - dates[i]).days > 1:
            break
    return streak

streak_count = calculate_streak(history_df)
st.metric("🔥 Current Streak", f"{streak_count} days")

# ------------------------
# Mode Switch
# ------------------------
mode = st.radio("Choose Mode", ["Daily Boost", "Custom Advice"])

name = st.text_input("What's your name?")

mood = ""
topic = ""
if mode == "Daily Boost":
    mood = st.selectbox(
        "How are you feeling right now?",
        ["Happy", "Sad", "Motivated", "Stressed", "Neutral", "Excited", "Tired"]
    )
else:
    topic = st.text_area("What topic do you want advice on?")

# ------------------------
# Generate Advice
# ------------------------
if st.button("🚀 Get Advice"):
    if not name.strip():
        st.warning("Please enter your name.")
    elif mode == "Custom Advice" and not topic.strip():
        st.warning("Please enter a topic for custom advice.")
    else:
        try:
            backend_url = "https://lifecoachgpt-mcp.onrender.com/advice"
            payload = {
                "name": name,
                "mood": mood,
                "topic": topic,
                "mode": "daily" if mode == "Daily Boost" else "custom"
            }
            response = requests.post(backend_url, json=payload)

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
                    "mode": mode,
                    "mood": mood,
                    "topic": topic,
                    "insight": insight,
                    "challenge": challenge,
                    "affirmation": affirmation
                }])
                history_df = pd.concat([history_df, new_entry], ignore_index=True)
                history_df.to_csv(HISTORY_FILE, index=False)

                # Update streak
                streak_count = calculate_streak(history_df)
                st.metric("🔥 Current Streak", f"{streak_count} days")

            else:
                st.error(f"Backend error: {response.text}")

        except Exception as e:
            st.error(f"Error connecting to backend: {e}")

# ------------------------
# Quick Info
# ------------------------

# ------------------------
# Mood History
# ------------------------
st.subheader("📊 Your History")
if history_df.empty:
    st.write("No history yet — generate your first dose!")
else:
    st.dataframe(history_df.tail(10), use_container_width=True)
