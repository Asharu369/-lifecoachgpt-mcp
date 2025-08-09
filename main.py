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

# Allow all origins for now (you can restrict later to your Streamlit app URL)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =============================
# Daily Boost Endpoint
# =============================
@app.post("/lifecoach")
async def lifecoach(request: Request):
    try:
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

        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        text_output = resp.candidates[0].content.parts[0].text

        # Parse safely
        try:
            motivation = json.loads(text_output)
        except:
            motivation = {
                "insight": "Keep pushing forward — progress builds momentum.",
                "micro_challenge": "Do one small task right now to build momentum.",
                "affirmation": "I am capable, resilient, and unstoppable."
            }

        return JSONResponse(content=motivation)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# =============================
# Custom Advice Endpoint
# =============================
@app.post("/advice")
async def advice(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "Friend")
        mood = data.get("mood", "Neutral")
        topic = data.get("topic", "general life advice")

        prompt = f"""
        You are LifeCoachGPT. {name} is feeling {mood}.
        They want custom advice about: {topic}.
        Respond in JSON with:
        - advice: 2-3 sentence personalized advice
        - action_steps: 2-3 bullet points of actionable steps
        - encouragement: short encouraging message
        """

        model = genai.GenerativeModel("gemini-2.0-flash")
        resp = model.generate_content(prompt)
        text_output = resp.candidates[0].content.parts[0].text

        try:
            advice_data = json.loads(text_output)
        except:
            advice_data = {
                "advice": "Focus on one step at a time, and don't overwhelm yourself.",
                "action_steps": [
                    "Take a short break to clear your mind",
                    "Write down your top 3 priorities",
                    "Start with the smallest task"
                ],
                "encouragement": "You are stronger than you think!"
            }

        return JSONResponse(content=advice_data)

    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


# =============================
# Run with: uvicorn main:app --reload
# =============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
