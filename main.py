# main.py
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from dotenv import load_dotenv

load_dotenv()

# ENV variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
VALID_TOKEN = os.getenv("VALID_TOKEN", "my-secret-token")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in environment variables.")

app = FastAPI()

# Allow frontend requests from anywhere (or limit to your domain)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to your frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== Models =====================
class ValidateRequest(BaseModel):
    token: str

class AdviceRequest(BaseModel):
    prompt: str
    tone: str = "empathetic"
    length: str = "short"

class ChatRequest(BaseModel):
    messages: list

# ===================== Routes =====================
@app.get("/manifest")
def manifest():
    return {
        "server_name": "life-coach-gpt",
        "description": "Life Coach GPT — quick insight, challenge, affirmation.",
        "tools": [
            {
                "id": "validate",
                "name": "validate",
                "description": "Validate a token and return owner's phone number.",
                "inputs": {
                    "type": "object",
                    "properties": {
                        "token": {"type": "string"}
                    }
                },
                "outputs": {
                    "type": "object",
                    "properties": {
                        "phone": {"type": "string"}
                    }
                }
            },
            {
                "id": "advice",
                "name": "advice",
                "description": "Generate life-coaching advice",
                "inputs": {
                    "type": "object",
                    "properties": {
                        "prompt": {"type": "string"},
                        "tone": {"type": "string"},
                        "length": {"type": "string"}
                    }
                },
                "outputs": {
                    "type": "object",
                    "properties": {
                        "advice": {"type": "string"}
                    }
                }
            }
        ]
    }

@app.post("/tools/validate")
def validate(req: ValidateRequest):
    if req.token != VALID_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token.")
    return {"phone": "+1234567890"}

@app.post("/tools/advice")
def advice(req: AdviceRequest):
    try:
        final_prompt = (
            f"You are LifeCoachGPT — a friendly coach.\n"
            f"Tone: {req.tone}\nLength: {req.length}\n"
            f"Prompt: {req.prompt}\n\n"
            f"Return JSON with fields: Insight, Micro-Challenge, Affirmation."
        )

        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a helpful and motivational life coach."},
                    {"role": "user", "content": final_prompt}
                ],
                "max_tokens": 300
            },
            timeout=15
        )

        if resp.status_code != 200:
            # Log the API's full response for debugging
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        data = resp.json()
        advice_text = data["choices"][0]["message"]["content"]
        return {"advice": advice_text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Advice generation error: {e}")

@app.post("/chat")
def chat(req: ChatRequest):
    try:
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-3.5-turbo",
                "messages": req.messages,
                "max_tokens": 500
            },
            timeout=15
        )

        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)

        data = resp.json()
        return {"response": data["choices"][0]["message"]["content"]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {e}")
