import os
import streamlit as st
from dotenv import load_dotenv
import requests

load_dotenv()

# Get Gemini API key from .env
GEMINI_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
if not GEMINI_API_KEY:
    st.error("Gemini API key not found. Please set GEMINI_PRO_API_KEY in your .env file.")
    st.stop()

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

st.set_page_config(page_title="LifeCoachGPT", page_icon="💡")
st.title("💡 LifeCoachGPT – Your Daily Dopamine Coach")

name = st.text_input("What's your name?", "")
mood = st.selectbox(
    "What's your current mood or intention?",
    ["Motivated", "Tired", "Stressed", "Calm", "Focused", "Happy", "Sad"]
)

if st.button("Give me my daily dose 🚀"):
    if not name:
        st.warning("Please enter your name to get your daily dose.")
    else:
        with st.spinner("Summoning your daily motivation..."):
            prompt_text = f"""
You are LifeCoachGPT — a friendly, wise, and energizing daily coach.
The user's name is {name}. Their current mood is {mood}.
Return:
1. One motivational insight
2. One micro-challenge they can do now (1–3 mins)
3. A one-liner affirmation to repeat aloud
Make it punchy, positive, and personal. No fluff.
"""

            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY  # lowercase 'x' here works fine too
            }

            json_data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt_text.strip()
                            }
                        ]
                    }
                ]
            }

            try:
                response = requests.post(GEMINI_API_URL, headers=headers, json=json_data)
                response.raise_for_status()
                data = response.json()

                # Extract the text output from Gemini's response
                motivational_text = data["candidates"][0]["content"]["parts"][0]["text"]

                st.markdown("### Your Daily Dose from LifeCoachGPT 🚀")
                st.write(motivational_text)

            except Exception as e:
                st.error(f"Error fetching motivation: {e}")
                st.code(response.text, language="json")  # Show Gemini's full error for debugging
