from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for all origins (for hackathon testing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API key from environment
GEMINI_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
if not GEMINI_API_KEY:
    raise RuntimeError("Gemini API key not found. Please set GEMINI_PRO_API_KEY in .env")

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

@app.get("/")
def root():
    return {"message": "LifeCoachGPT MCP server is running"}

@app.post("/validate")
async def validate(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or bad token")

    token = authorization.split(" ")[1]

    # Simple static token check for hackathon
    if token == "lifecoach-secret":
        return {"phone_number": "916235532605"}  # Your number in {country_code}{number} format
    else:
        raise HTTPException(status_code=403, detail="Invalid token")

@app.post("/lifecoach")
async def lifecoach(name: str, mood: str):
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
        "x-goog-api-key": GEMINI_API_KEY
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
        motivational_text = data["candidates"][0]["content"]["parts"][0]["text"]

        return {"output": motivational_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching motivation: {e}")
