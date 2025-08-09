import os
import re
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import google.generativeai as genai

# =============================
# Load environment variables
# =============================
load_dotenv()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_KEY:
    raise ValueError("GEMINI_API_KEY not found in .env file")

genai.configure(api_key=GEMINI_KEY)

# =============================
# FastAPI app
# =============================
app = FastAPI(title="LifeCoachGPT API")

# -----------------------------
# Helper: Parse JSON Safely & Normalize Keys
# -----------------------------
def safe_parse_json(text_output, fallback):
    """
    Extracts first valid JSON from string, parses it, normalizes keys to lowercase.
    Returns fallback dict if parsing fails.
    """
    try:
        match = re.search(r"\{.*\}", text_output, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            return {k.lower(): v for k, v in parsed.items()}
        return fallback
    except Exception:
        return fallback

# -----------------------------
# Combined Advice Endpoint
# -----------------------------
@app.post("/advice")
async def advice(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "Friend")
        mode = data.get("mode", "daily").lower()
        mood = data.get("mood", "Neutral")
        topic = data.get("topic", "")

        if mode not in ["daily", "custom"]:
            return JSONResponse(content={"error": "Invalid mode. Use 'daily' or 'custom'."}, status_code=400)

        if mode == "custom" and not topic.strip():
            return JSONResponse(content={"error": "Please provide a topic for custom advice."}, status_code=400)

        # Create prompt based on mode
        if mode == "daily":
            prompt = f"""
            You are LifeCoachGPT. Give motivational output for someone named {name} who is feeling {mood}.
            Respond ONLY in valid JSON format:
            {{
                "insight": "...",
                "micro_challenge": "...",
                "affirmation": "..."
            }}
            """
            fallback = {
                "insight": "Keep pushing forward — progress builds momentum.",
                "micro_challenge": "Do one small task right now to build momentum.",
                "affirmation": "I am capable, resilient, and unstoppable."
            }
        else:  # custom mode
            prompt = f"""
            You are LifeCoachGPT. {name} is asking for advice on: "{topic}".
            Respond ONLY in valid JSON format:
            {{
                "insight": "...",
                "micro_challenge": "...",
                "affirmation": "..."
            }}
            """
            fallback = {
                "insight": "Your growth begins with the first step toward your goal.",
                "micro_challenge": "Write down one specific action to take today.",
                "affirmation": "I am moving closer to my dreams each day."
            }

        # Call Gemini
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        text_output = resp.candidates[0].content.parts[0].text

        advice_data = safe_parse_json(text_output, fallback)

        return JSONResponse(content=advice_data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# =============================
# Run with: uvicorn main:app --reload
# =============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
