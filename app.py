import os
import json
from datetime import datetime
import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# Config
# -------------------------
GEMINI_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

CSV_FILE = "mood_history.csv"

# -------------------------
# Helper: Gemini call + robust parsing
# -------------------------
def call_gemini(prompt_text, api_key):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
    # Using prompt form that typically works; tuned params
    payload = {
        "prompt": {"text": prompt_text},
        "temperature": 0.7,
        "maxOutputTokens": 350
    }
    resp = requests.post(GEMINI_API_URL, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()

def extract_text_from_gemini(resp_json):
    """
    Try several possible response shapes and return the generated text.
    """
    # 1) Newer style: top-level 'candidates' with 'output' string
    try:
        if isinstance(resp_json, dict) and "candidates" in resp_json:
            cand0 = resp_json["candidates"][0]
            if isinstance(cand0, dict) and "output" in cand0:
                return cand0["output"]
            # older shape where content object exists
            if "content" in cand0:
                content = cand0["content"]
                # content could be dict with 'text' or 'parts'
                if isinstance(content, dict) and "text" in content:
                    return content["text"]
                if isinstance(content, dict) and "parts" in content:
                    parts = content["parts"]
                    if parts and isinstance(parts, list) and "text" in parts[0]:
                        return parts[0]["text"]
    except Exception:
        pass

    # 2) 'results' -> candidates -> content -> text
    try:
        if "results" in resp_json:
            res0 = resp_json["results"][0]
            cand0 = res0.get("candidates", [{}])[0]
            content = cand0.get("content", {})
            # candidate output may be 'text' or 'output' or nested
            if isinstance(content, dict) and "text" in content:
                return content["text"]
            if isinstance(cand0, dict) and "output" in cand0:
                return cand0["output"]
            # sometimes it's structured differently:
            if isinstance(cand0, dict) and "content" in cand0:
                cont = cand0["content"]
                if isinstance(cont, dict) and "parts" in cont:
                    return cont["parts"][0].get("text", "")
    except Exception:
        pass

    # 3) fallback: try top-level 'parts'
    try:
        if "parts" in resp_json:
            return resp_json["parts"][0].get("text", "")
    except Exception:
        pass

    # 4) last resort: stringify entire response
    return json.dumps(resp_json)

def parse_motivation_text(text):
    """
    Try to parse either JSON output or free text with labeled lines.
    Returns dict with keys: insight, micro_challenge, affirmation
    """
    result = {"insight": "", "micro_challenge": "", "affirmation": "", "raw": text}

    # Try JSON first
    try:
        parsed = json.loads(text)
        # accept multiple naming variants
        result["insight"] = parsed.get("insight") or parsed.get("insight_text") or parsed.get("Insight") or ""
        result["micro_challenge"] = parsed.get("micro_challenge") or parsed.get("challenge") or parsed.get("task") or ""
        result["affirmation"] = parsed.get("affirmation") or parsed.get("aff") or parsed.get("affirm") or ""
        return result
    except Exception:
        pass

    # If not JSON, split into lines and look for keywords
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for ln in lines:
        lnl = ln.lower()
        # common patterns
        if lnl.startswith("insight:") or lnl.startswith("1. insight") or lnl.startswith("1) insight"):
            result["insight"] = ln.split(":", 1)[-1].strip()
        elif "insight" in lnl and (":" in ln):
            result["insight"] = ln.split(":", 1)[-1].strip()
        elif lnl.startswith("micro-challenge:") or lnl.startswith("2. micro") or "micro-challenge" in lnl:
            result["micro_challenge"] = ln.split(":", 1)[-1].strip()
        elif "challenge" in lnl and (":" in ln):
            result["micro_challenge"] = ln.split(":", 1)[-1].strip()
        elif lnl.startswith("affirmation:") or "affirmation" in lnl:
            result["affirmation"] = ln.split(":", 1)[-1].strip()
        elif lnl.startswith("3.") and "affirm" in lnl:
            result["affirmation"] = ln.split(":", 1)[-1].strip()

    # If any field still empty, try to assign from larger chunks heuristically
    if not result["insight"]:
        # first paragraph as insight
        paragraphs = text.split("\n\n")
        if paragraphs:
            result["insight"] = paragraphs[0].strip()
    if not result["micro_challenge"]:
        # second paragraph
        paragraphs = text.split("\n\n")
        if len(paragraphs) >= 2:
            result["micro_challenge"] = paragraphs[1].strip()
    if not result["affirmation"]:
        # last short line as affirmation
        last_lines = lines[-1] if lines else ""
        if len(last_lines) < 120:
            result["affirmation"] = last_lines

    return result

# -------------------------
# Persistence helpers
# -------------------------
def append_entry(csv_file, entry):
    # entry: dict containing date,name,mood,insight,challenge,affirmation
    df = pd.DataFrame([entry])
    if os.path.exists(csv_file):
        df.to_csv(csv_file, mode="a", index=False, header=False)
    else:
        df.to_csv(csv_file, index=False)

def load_history(csv_file):
    if os.path.exists(csv_file):
        return pd.read_csv(csv_file)
    return pd.DataFrame(columns=["date", "name", "mood", "insight", "micro_challenge", "affirmation"])

# -------------------------
# Streamlit UI & flow
# -------------------------
st.set_page_config(page_title="LifeCoachGPT — Daily Dopamine", page_icon="💡", layout="wide")

# Styling
st.markdown(
    """
    <style>
    .header {
        text-align: center;
        padding: 12px 0;
    }
    .card {
        padding: 18px;
        border-radius: 12px;
        color: white;
        margin-bottom: 12px;
    }
    .insight { background: linear-gradient(90deg,#56ab2f,#a8e063); }
    .challenge { background: linear-gradient(90deg,#f7971e,#ffd200); color: #222; }
    .affirmation { background: linear-gradient(90deg,#00c6ff,#0072ff); }
    .small { font-size: 0.9rem; color: #666; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("<div class='header'><h1>🌟 LifeCoachGPT</h1><p class='small'>Your daily 60s motivation — insight, micro-challenge, affirmation</p></div>", unsafe_allow_html=True)
st.write("---")

left_col, right_col = st.columns([2, 1])

with left_col:
    name = st.text_input("What's your name?", value="")
    mood = st.selectbox("How are you feeling right now?", ["Neutral", "Happy", "Sad", "Motivated", "Tired", "Stressed", "Calm", "Focused"])
    mode = st.selectbox("Mode", ["Daily Boost", "Focus Coach", "Calm & Reset", "Confidence Boost"], index=0)
    st.write("")  # spacing
    gen_btn = st.button("💥 Give me my daily dose")
    reset_btn = st.button("🔄 Reset (clear history)")  # reset will clear file below

with right_col:
    st.markdown("### Quick info")
    st.markdown("- Uses **Gemini Pro** for responses")
    st.markdown("- Stores local mood history (CSV)")
    st.markdown("- Shareable & habit-forming")

# Reset logic (clear CSV)
if reset_btn:
    if os.path.exists(CSV_FILE):
        os.remove(CSV_FILE)
        st.success("History cleared.")
    else:
        st.info("No history to clear.")

# When generate pressed
if gen_btn:
    if not GEMINI_API_KEY:
        st.error("Gemini API key not found. Set GEMINI_PRO_API_KEY in your .env file.")
    elif not name.strip():
        st.warning("Please enter your name.")
    else:
        with st.spinner("Generating your 60s dose..."):
            prompt_text = f"""
You are LifeCoachGPT — a friendly, wise, and energizing daily coach.
Mode: {mode}
The user's name is {name}. Their current mood is {mood}.
Return three items: Insight (one sentence), Micro-Challenge (one concrete 1-3 minute action), Affirmation (one short line).
Prefer punchy, actionable language and keep each item short.
Format them clearly with labels (Insight:, Micro-Challenge:, Affirmation:).
"""
            try:
                resp_json = call_gemini(prompt_text, GEMINI_API_KEY)
                raw_text = extract_text_from_gemini(resp_json)
                parsed = parse_motivation_text(raw_text)

                # display nicely
                st.markdown(f"<div class='card insight'><b>💡 Insight</b><div style='margin-top:8px'>{parsed['insight']}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card challenge'><b>🔥 Micro-Challenge</b><div style='margin-top:8px'>{parsed['micro_challenge']}</div></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='card affirmation'><b>🌈 Affirmation</b><div style='margin-top:8px'>{parsed['affirmation']}</div></div>", unsafe_allow_html=True)

                # Save to CSV
                entry = {
                    "date": datetime.utcnow().date().isoformat(),
                    "name": name.strip(),
                    "mood": mood,
                    "insight": parsed["insight"],
                    "micro_challenge": parsed["micro_challenge"],
                    "affirmation": parsed["affirmation"]
                }
                append_entry(CSV_FILE, entry)
                st.success("Saved to your history ✅")
            except requests.exceptions.HTTPError as he:
                st.error(f"API error: {he}")
            except Exception as e:
                st.error(f"Failed to generate: {e}")

# Load & display history
st.write("---")
st.markdown("## Your History")

df = load_history(CSV_FILE)
if df.empty:
    st.info("No history yet — generate your first dose!")
else:
    # allow filter by name
    names = ["All"] + sorted(df["name"].unique().tolist())
    selected_name = st.selectbox("Filter by name", names)
    filtered = df if selected_name == "All" else df[df["name"] == selected_name]

    st.dataframe(filtered.sort_values("date", ascending=False))

    # Mood frequency chart
    st.markdown("### Mood frequency")
    mood_counts = filtered["mood"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 3))
    mood_counts.plot(kind="bar", ax=ax)
    ax.set_ylabel("Count")
    st.pyplot(fig)

    # Mood timeline: number of entries per day
    st.markdown("### Mood over time")
    try:
        timeline = filtered.groupby("date").size().reindex(pd.date_range(filtered["date"].min(), filtered["date"].max()).date, fill_value=0)
        fig2, ax2 = plt.subplots(figsize=(8, 3))
        ax2.plot(timeline.index.astype(str), timeline.values, marker="o")
        ax2.set_xlabel("Date")
        ax2.set_ylabel("Entries")
        plt.xticks(rotation=45)
        st.pyplot(fig2)
    except Exception:
        st.info("Not enough data for timeline chart (need >=2 different dates).")
