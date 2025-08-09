import streamlit as st
import pandas as pd
import datetime
import os

# ============ PAGE CONFIG ============
st.set_page_config(
    page_title="LifeCoachGPT",
    page_icon="🌟",
    layout="centered",
    initial_sidebar_state="expanded"
)

st.title("🌟 LifeCoachGPT – Your AI Coach")
st.write("Get personalized insights, challenges, and affirmations.")

# ============ MOOD TRACKING ============
MOOD_FILE = "mood_tracking.csv"

def load_mood_data():
    if os.path.exists(MOOD_FILE):
        return pd.read_csv(MOOD_FILE)
    else:
        return pd.DataFrame(columns=["date", "mood"])

def save_mood(mood):
    data = load_mood_data()
    today = datetime.date.today().isoformat()
    new_entry = pd.DataFrame([[today, mood]], columns=["date", "mood"])
    data = pd.concat([data, new_entry], ignore_index=True)
    data.to_csv(MOOD_FILE, index=False)

st.sidebar.header("📅 Mood Tracker")
mood = st.sidebar.selectbox(
    "How are you feeling today?",
    ["😊 Happy", "😐 Neutral", "😔 Sad", "😡 Angry", "😴 Tired"]
)

if st.sidebar.button("Save Mood"):
    save_mood(mood)
    st.sidebar.success("Mood saved!")

mood_data = load_mood_data()
if not mood_data.empty:
    st.sidebar.subheader("Mood History")
    st.sidebar.line_chart(mood_data.set_index("date"))

# ============ MAIN CHAT INTERFACE ============
with st.form("life_coach_form"):
    user_input = st.text_area("💬 What's on your mind today?", "")
    submitted = st.form_submit_button("Get Coaching")

if submitted and user_input.strip():
    # Here we simulate AI output (replace with API call to your FastAPI backend if needed)
    st.success("✅ Coaching Results")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 💡 Insight")
        st.info(f"Based on your input, you may want to focus on {user_input.lower()}.")

    with col2:
        st.markdown("### 🎯 Micro-Challenge")
        st.warning("Take 5 minutes to write down your top 3 priorities for today.")

    with col3:
        st.markdown("### 🌈 Affirmation")
        st.success("You are capable, resilient, and ready to grow.")

# Reset button
if st.button("🔄 Reset"):
    st.experimental_rerun()

st.markdown("---")


