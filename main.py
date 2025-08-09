import os
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_PRO_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("Gemini API key not found. Please set GEMINI_PRO_API_KEY in your .env file.")

# Gemini API endpoint
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# FastAPI app
app = FastAPI(title="LifeCoachGPT MCP Server")

# Request model
class MCPRequest(BaseModel):
    name: str
    mood: str

# MCP tool endpoint
@app.post("/mcp")
def life_coach_tool(request: MCPRequest):
    """Main MCP tool that returns a motivational insight, micro-challenge, and affirmation."""
    prompt_text = f"""
You are LifeCoachGPT — a friendly, wise, and energizing daily coach.
The user's name is {request.name}. Their current mood is {request.mood}.
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
        response = requests.post(GEMINI_API_URL, headers=headers, json=json_data)
        response.raise_for_status()
        data = response.json()
        motivational_text = data["candidates"][0]["content"]["parts"][0]["text"]
        return {"response": motivational_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Validate endpoint (required by Puch AI)
@app.post("/validate")
def validate(bearer_token: str):
    """
    Puch AI will call this to validate the user.
    For now, return your phone number in format {countrycode}{number}.
    Example: '919876543210' for +91-9876543210.
    """
    return {"phone": "916235532605"}  
