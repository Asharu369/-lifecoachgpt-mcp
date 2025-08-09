import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
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

# -------- Enable CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# -------- Helper: call Gemini and ensure JSON output --------
def get_gemini_json(prompt: str):
    try:
        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        text_output = resp.candidates[0].content.parts[0].text

        try:
            return json.loads(text_output)
        except json.JSONDecodeError:
            # fallback
            return {
                "insight": "Keep pushing forward — progress builds momentum.",
                "micro_challenge": "Do one small task right now to build momentum.",
                "affirmation": "I am capable, resilient, and unstoppable."
            }
    except Exception as e:
        return {"error": str(e)}


# -------- Old endpoint (kept for compatibility) --------
@app.post("/lifecoach")
async def lifecoach(request: Request):
    data = await request.json()
    name = data.get("name", "Friend")
    mood = data.get("mood", "Neutral")

    prompt = f"""
    You are LifeCoachGPT. Give motivational output for someone named {name} who is feeling {mood}.
    Respond in JSON with:
    - insight: short life insight
    - micro_challenge: small action they can take now
    - affirmation: positive affirmation
    """
    return JSONResponse(content=get_gemini_json(prompt))


# -------- New endpoint for Mode Switch --------
@app.post("/advice")
async def advice(request: Request):
    data = await request.json()
    mode = data.get("mode", "Daily Boost")
    name = data.get("name", "Friend")

    if mode == "Daily Boost":
        mood = data.get("mood", "Neutral")
        prompt = f"""
        You are LifeCoachGPT. Give motivational output for someone named {name} who is feeling {mood}.
        Respond in JSON with:
        - insight: short life insight
        - micro_challenge: small action they can take now
        - affirmation: positive affirmation
        """
    else:  # Custom Advice
        topic = data.get("topic", "self-improvement")
        prompt = f"""
        You are LifeCoachGPT. Give personalized advice on {topic} for someone named {name}.
        Respond in JSON with:
        - insight: short insight about the topic
        - micro_challenge: small actionable step they can take now
        - affirmation: short encouraging affirmation
        """

    return JSONResponse(content=get_gemini_json(prompt))


# =============================
# Run with: uvicorn app:app --reload
# =============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
