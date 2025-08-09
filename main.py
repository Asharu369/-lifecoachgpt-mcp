from fastapi import FastAPI
from pydantic import BaseModel
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Load Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found. Set GEMINI_PRO_API_KEY in environment variables.")

# ✅ 1. Validate Tool for Puch AI Authentication
class ValidateRequest(BaseModel):
    bearer_token: str

@app.post("/validate")
def validate(req: ValidateRequest):
    # Return your phone number in required format (country code + number, no + sign)
    return {"phone_number": "916235532605"}  # <-- Replace with your number

# ✅ 2. LifeCoach API Endpoint
class LifeCoachRequest(BaseModel):
    name: str
    mood: str

@app.post("/lifecoach")
def lifecoach(req: LifeCoachRequest):
    prompt_text = f"""
    You are LifeCoachGPT — a friendly, wise, and energizing daily coach.
    The user's name is {req.name}. Their current mood is {req.mood}.
    Return:
    1. One motivational insight
    2. One micro-challenge they can do now (1–3 mins)
    3. A one-liner affirmation to repeat aloud
    Make it punchy, positive, and personal. No fluff.
    """

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    json_data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text.strip()}
                ]
            }
        ]
    }

    try:
        response = requests.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            headers=headers,
            json=json_data
        )
        response.raise_for_status()
        data = response.json()
        motivational_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"message": motivational_text}

    except Exception as e:
        return {"error": str(e)}

# Root route
@app.get("/")
def root():
    return {"status": "LifeCoachGPT MCP server is running"}
