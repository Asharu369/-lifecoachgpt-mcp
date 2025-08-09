import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st

# =============================
# Load environment variables
# =============================
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_KEY)

# =============================
# Flask API for Puch AI
# =============================
app = Flask(__name__)

@app.route("/lifecoach", methods=["POST"])
def lifecoach():
    try:
        data = request.get_json()
        name = data.get("name", "Friend")
        mood = data.get("mood", "Neutral")

        prompt = f"""
        You are LifeCoachGPT. Give motivational output for someone named {name} who is feeling {mood}.
        Respond in JSON with:
        - insight: short life insight
        - micro_challenge: small action they can take now
        - affirmation: positive affirmation
        """

        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        text_output = resp.candidates[0].content.parts[0].text

        # Try to parse JSON safely
        try:
            motivation = json.loads(text_output)
        except:
            motivation = {
                "insight": "Keep pushing forward — progress builds momentum.",
                "micro_challenge": "Do one small task right now to build momentum.",
                "affirmation": "I am capable, resilient, and unstoppable."
            }

        return jsonify(motivation)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================
# Streamlit UI
# =============================
def run_streamlit():
    st.set_page_config(page_title="LifeCoachGPT", layout="wide")
    st.markdown("<h1 style='color:#ff4b4b;'>🌟 LifeCoachGPT — Your Daily Dose of Motivation</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Your Name", "Asharu")
        mood = st.selectbox("How are you feeling today?", ["Happy", "Sad", "Motivated", "Stressed", "Tired", "Excited"])
    with col2:
        st.markdown("### 💡 Daily Tip: Even small actions create big momentum!")

    if st.button("🚀 Give me my daily dose"):
        payload = {"name": name, "mood": mood}
        with st.spinner("Fetching your motivation..."):
            model = genai.GenerativeModel("gemini-2.0-flash")
            resp = model.generate_content(f"""
            You are LifeCoachGPT. Give motivational output for {name} who is feeling {mood}.
            Respond in JSON with insight, micro_challenge, and affirmation.
            """)
            try:
                motivation = json.loads(resp.candidates[0].content.parts[0].text)
            except:
                motivation = {
                    "insight": "Keep pushing forward — progress builds momentum.",
                    "micro_challenge": "Do one small task right now to build momentum.",
                    "affirmation": "I am capable, resilient, and unstoppable."
                }

        # Display sections with colors & icons
        st.success(f"💡 Insight: {motivation['insight']}")
        st.info(f"🎯 Micro-Challenge: {motivation['micro_challenge']}")
        st.warning(f"🌈 Affirmation: {motivation['affirmation']}")

        # Save to mood history
        log_mood(name, mood, motivation)

    # Reset button
    if st.button("🔄 Reset"):
        st.experimental_rerun()

    # Show history
    if os.path.exists("mood_history.csv"):
        st.subheader("📅 Your Mood & Motivation History")
        df = pd.read_csv("mood_history.csv")
        st.dataframe(df)

        # Chart: mood trends
        fig, ax = plt.subplots()
        df["Date"] = pd.to_datetime(df["Date"])
        mood_counts = df.groupby("Mood").size()
        mood_counts.plot(kind="bar", ax=ax, color="skyblue")
        plt.title("Mood Frequency Over Time")
        st.pyplot(fig)

# =============================
# Mood history helper
# =============================
def log_mood(name, mood, motivation):
    entry = {
        "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Name": name,
        "Mood": mood,
        "Insight": motivation["insight"],
        "MicroChallenge": motivation["micro_challenge"],
        "Affirmation": motivation["affirmation"]
    }
    df = pd.DataFrame([entry])
    if os.path.exists("mood_history.csv"):
        df.to_csv("mood_history.csv", mode="a", header=False, index=False)
    else:
        df.to_csv("mood_history.csv", index=False)

# =============================
# Run locally
# =============================
if __name__ == "__main__":
    import sys
    if "streamlit" in sys.argv:
        run_streamlit()
    else:
        app.run(host="0.0.0.0", port=5000)
