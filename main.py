import os
import json
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, Body, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

# Load env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
VALIDATION_TOKEN = os.getenv("VALIDATION_TOKEN", "").strip()
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "").strip()
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lifecoachgpt")

# FastAPI init
app = FastAPI(title="Life Coach GPT - MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Models
class AdviceRequest(BaseModel):
    prompt: str
    tone: Optional[str] = "empathetic"
    length: Optional[str] = "short"

class AdviceResponse(BaseModel):
    advice: str

# Helpers
def call_gemini_http(prompt_text: str, timeout: int = 25) -> Dict[str, Any]:
    if not GEMINI_API_KEY:
        raise RuntimeError("Gemini API key not configured.")
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": GEMINI_API_KEY,
    }
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ]
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()

def build_instruction(prompt: str, tone: str = "empathetic", length: str = "short") -> str:
    return (
        "You are LifeCoachGPT — a friendly, practical and uplifting life coach.\n"
        f"Tone: {tone}\nLength: {length}\n\n"
        "Produce three labelled short items exactly in this format:\n"
        "Insight: <one-sentence insight>\n"
        "Micro-Challenge: <one concrete 1-3 minute action>\n"
        "Affirmation: <one short encouraging line>\n\n"
        f"User prompt: {prompt}\n"
        "Keep output concise, punchy, and action-focused."
    )

def demo_advice(prompt: str) -> str:
    return (
        "Insight: Small consistent actions beat large sporadic efforts — start with one tiny step.\n"
        "Micro-Challenge: Set a timer for 2 minutes and perform one tiny action toward your goal now.\n"
        "Affirmation: I move forward step by step."
    )

# Manifest
@app.get("/mcp/manifest")
async def manifest():
    return {
        "server_name": "life-coach-gpt",
        "description": "Life Coach GPT — quick insight, challenge, affirmation.",
        "tools": [
            {"id": "validate", "name": "validate", "description": "Validate a token and return owner's phone number.", "inputs": {"type":"object","properties":{"token":{"type":"string"}}}, "outputs": {"type":"object","properties":{"phone":{"type":"string"}}}},
            {"id": "advice", "name": "advice", "description": "Generate life-coaching advice", "inputs": {"type":"object","properties":{"prompt":{"type":"string"}}}, "outputs": {"type":"object","properties":{"advice":{"type":"string"}}}}
        ]
    }

@app.post("/tools/validate")
async def tools_validate(payload: Dict[str, Any] = Body(...)):
    token = (payload.get("token") or payload.get("bearer_token") or "").strip()
    logger.info("Validate called (token prefix=%s)", token[:8] if token else "<empty>")
    if token and VALIDATION_TOKEN and token == VALIDATION_TOKEN and PHONE_NUMBER:
        return {"phone": PHONE_NUMBER}
    logger.warning("Validation failed for token prefix=%s", token[:8] if token else "<empty>")
    raise HTTPException(status_code=401, detail="Invalid validation token")

@app.post("/tools/advice")
def advice(
    req: AdviceRequest,
    authorization: Optional[str] = Header(None)
):
    # Check bearer token if validation is enforced
    if VALIDATION_TOKEN:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
        token = authorization.split(" ", 1)[1]
        if token != VALIDATION_TOKEN:
            raise HTTPException(status_code=403, detail="Forbidden: invalid token")

    final_prompt = build_instruction(req.prompt, req.tone, req.length)

    try:
        if GEMINI_API_KEY:
            data = call_gemini_http(final_prompt)
            advice_text = data["candidates"][0]["content"]["parts"][0]["text"]
        elif DEMO_MODE:
            advice_text = demo_advice(req.prompt)
        else:
            raise RuntimeError("No model configured")
    except Exception as e:
        logger.exception("Error generating advice: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"advice": advice_text}

@app.get("/")
async def root():
    return {"status": "ok", "server": "life-coach-gpt", "demo_mode": DEMO_MODE}

@app.post("/chat")
async def chat(payload: Dict[str, Any] = Body(...)):
    q = payload.get("query") or payload.get("prompt") or payload.get("message") or ""
    if not q:
        raise HTTPException(status_code=400, detail="Missing query")
    instruction = build_instruction(q)
    try:
        if GEMINI_API_KEY:
            resp_json = call_gemini_http(instruction)
            raw_text = resp_json["candidates"][0]["content"]["parts"][0]["text"]
            return {"response": raw_text}
        if DEMO_MODE:
            return {"response": demo_advice(q)}
        raise HTTPException(status_code=503, detail="No model configured")
    except Exception as e:
        logger.exception("Chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
