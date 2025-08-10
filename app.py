# app.py
import os
import json
from datetime import datetime
from typing import Dict, Any

import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

# Backend URL: prefer env var BACKEND_URL; fall back to localhost (for local dev)
BACKEND_URL = os.getenv("BACKEND_URL", "https://lifecoachgpt-mcp.onrender.com").strip()
CSV_FILE = os.getenv("CSV_FILE", "mood_history.csv")
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")

def call_backend_advice(backend_url: str, prompt: str, tone: str = "empathetic", length: str = "short", timeout: int = 12):
    url = backend_url.rstrip("/") + "/tools/advice"
    payload = {"prompt": prompt, "tone": tone, "length": length}
    r = requests.post(url, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def parse_motivation_text(text: str):
    # same parsing as backend
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    result = {"insight": "", "micro_challenge": "", "affirmation": "", "raw": text}
    for ln in lines:
        lnl = ln.lower()
        if lnl.startswith("insight:") or ("insight" in lnl and ":" in ln):
            result["insight"] = ln.split(":", 1)[-1].strip()
        elif lnl.startswith("micro-challenge:") or ("micro" in lnl and "challenge" in lnl) or ("challenge" in lnl and ":" in ln):
            result["micro_challenge"] = ln.split(":", 1)[-1].strip()
        elif lnl.startswith("affirmation:") or ("affirm" in lnl and ":" in ln):
            result["affirmation"] = ln.split(":", 1)[-1].strip()
    if not result["insight"]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if paragraphs:
            result["insight"] = paragraphs[0]
    if not result["micro_challenge"]:
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if len(paragraphs) > 1:
            result["micro_challenge"] = paragraphs[1]
    if not result["affirmation"]:
        if lines:
            last = lines[-1]
            if len(last) < 200:
                result["affirmation"] = last
    return result

def append_entry(csv_file, entry):
    df = pd.DataFrame([entry])
    if os.path.exists(csv_file):
        df.to_csv(csv_file, mode="a", index=False, header=False)
    else:
        df.to_csv(csv_file, index=False)

def load_history(csv_file):
    if os.path.exists(csv_file):
        try:
            return pd.read_csv(csv_file)
        except Exception:
            return pd.DataFrame(columns=["date", "name", "mood", "mode", "insight", "micro_challenge", "affirmation"])
    return pd.DataFrame(columns=["date", "name", "mood", "mode", "insight", "micro_challenge", "affirmation"])

st.set_page_config(page_title="LifeCoachGPT", page_icon="💡", layout="wide")
st.markdown("<h1 style='text-align:center'>🌟 LifeCoachGPT</h1>", unsafe_allow_html=True)
left_col, right_col = st.columns([2,1])

with right_col:
    st.markdown("### Info")
    st.markdown(f"- Backend: `{BACKEND_URL}`")
    if DEBUG:
        st.warning("DEBUG ON")

with left_col:
    with st.form("main_form"):
        name = st.text_input("What's your name?", value="")
        mood = st.selectbox("How are you feeling?", ["Neutral","Happy","Sad","Motivated","Tired","Stressed","Calm","Focused"])
        mode = st.selectbox("Mode", ["Daily Boost","Focus Coach","Calm & Reset","Confidence Boost"])
        tone = st.selectbox("Tone", ["empathetic","direct","encouraging"])
        length = st.selectbox("Length", ["short","detailed"])
        prompt_extra = st.text_area("Optional: context (what's bothering you?)", height=80)
        submitted = st.form_submit_button("💥 Give me my daily dose")

if submitted:
    if not name.strip():
        st.warning("Enter your name.")
    else:
        prompt_text = (
            f"You are LifeCoachGPT — a friendly coach.\nMode: {mode}\nName: {name}\nMood: {mood}\nTone: {tone}\nLength: {length}\n\n"
            f"Context: {prompt_extra}\n\nReturn: Insight:, Micro-Challenge:, Affirmation:"
        )
        try:
            if BACKEND_URL and not BACKEND_URL.startswith("http://127.0.0.1") and DEMO_MODE:
                # allow demo mode even if backend configured
                pass
            resp = call_backend_advice(BACKEND_URL, prompt_text, tone=tone, length=length)
            advice_raw = resp.get("advice") if isinstance(resp, dict) else str(resp)
        except Exception as e:
            if DEMO_MODE:
                advice_raw = f"Insight: Small step.\nMicro-Challenge: 2 minutes action.\nAffirmation: I move forward."
            else:
                st.error(f"Error contacting backend: {e}")
                advice_raw = None

        if advice_raw:
            parsed = parse_motivation_text(advice_raw)
            st.markdown(f"### 💡 Insight\n{parsed['insight']}")
            st.markdown(f"### 🔥 Micro-Challenge\n{parsed['micro_challenge']}")
            st.markdown(f"### 🌈 Affirmation\n{parsed['affirmation']}")
            entry = {"date": datetime.utcnow().isoformat(), "name": name.strip(), "mood": mood, "mode": mode, "insight": parsed["insight"], "micro_challenge": parsed["micro_challenge"], "affirmation": parsed["affirmation"]}
            append_entry(CSV_FILE, entry)
            st.download_button("⬇️ Download (TXT)", json.dumps(entry, ensure_ascii=False, indent=2).encode("utf-8"), file_name=f"lifecoach_{name}_{datetime.utcnow().date()}.txt")

st.write("---")
st.markdown("## Your History")
df = load_history(CSV_FILE)
if df.empty:
    st.info("No history yet.")
else:
    st.dataframe(df.sort_values("date", ascending=False).reset_index(drop=True))
    st.markdown("### Mood frequency")
    mood_counts = df["mood"].value_counts()
    fig, ax = plt.subplots(figsize=(6,3))
    mood_counts.plot(kind="bar", ax=ax)
    st.pyplot(fig)
