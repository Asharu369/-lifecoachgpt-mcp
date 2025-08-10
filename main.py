import os
import json
import logging
from typing import Dict, Any, Optional

from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import requests

# Load env
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_PRO_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
VALIDATION_TOKEN = os.getenv("VALIDATION_TOKEN", "").strip()
PHONE_NUMBER = os.getenv("PHONE_NUMBER", "").strip()  # digits-only, e.g. 919876543210
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() in ("1", "true", "yes")
DEBUG = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("lifecoachgpt")

# FastAPI init
app = FastAPI(title="Life Coach GPT - MCP Server")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in production
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

# Helpers (same parsing logic as frontend)
def extract_text_from_gemini(resp_json: Dict[str, Any]) -> str:
    try:
        if not isinstance(resp_json, dict):
            return json.dumps(resp_json)
        candidates = resp_json.get("candidates") or (resp_json.get("results", [{}])[0].get("candidates") if "results" in resp_json else None)
        if candidates and isinstance(candidates, list):
            cand0 = candidates[0] or {}
            if isinstance(cand0, dict):
                for key in ("output", "text"):
                    if key in cand0:
                        return cand0[key]
                if "content" in cand0:
                    content = cand0["content"]
                    if isinstance(content, dict):
                        if "text" in content:
                            return content["text"]
                        parts = content.get("parts")
                        if isinstance(parts, list) and parts:
                            p = parts[0]
                            if isinstance(p, dict) and "text" in p:
                                return p["text"]
        if "parts" in resp_json and isinstance(resp_json["parts"], list) and resp_json["parts"]:
            p = resp_json["parts"][0]
            if isinstance(p, dict) and "text" in p:
                return p["text"]
    except Exception:
        pass
    return json.dumps(resp_json)

def parse_motivation_text(text: str) -> Dict[str, str]:
    result = {"insight": "", "micro_challenge": "", "affirmation": "", "raw": text}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            result["insight"] = parsed.get("insight") or parsed.get("insight_text") or parsed.get("Insight") or ""
            result["micro_challenge"] = parsed.get("micro_challenge") or parsed.get("challenge") or parsed.get("task") or ""
            result["affirmation"] = parsed.get("affirmation") or parsed.get("affirm") or parsed.get("aff") or ""
            return result
    except Exception:
        pass
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
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
    insight = "Small consistent actions beat large sporadic efforts — start with one tiny step."
    challenge = "Set a timer for 2 minutes and perform one tiny action toward your goal now."
    affirmation = "I move forward step by step."
    return f"Insight: {insight}\nMicro-Challenge: {challenge}\nAffirmation: {affirmation}"

# Manifest (MCP)
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

@app.post("/tools/advice", response_model=AdviceResponse)
async def tools_advice(payload: AdviceRequest = Body(...)):
    prompt = (payload.prompt or "").strip()
    tone = (payload.tone or "empathetic").strip()
    length = (payload.length or "short").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Missing prompt")
    logger.info("Advice requested (tone=%s length=%s prompt_len=%d)", tone, length, len(prompt))
    instruction = build_instruction(prompt, tone=tone, length=length)
    try:
        if GEMINI_API_KEY:
            resp_json = call_gemini_http(instruction)
            raw_text = extract_text_from_gemini(resp_json)
            parsed = parse_motivation_text(raw_text)
            advice_text = (
                f"Insight: {parsed['insight']}\nMicro-Challenge: {parsed['micro_challenge']}\nAffirmation: {parsed['affirmation']}"
                if (parsed.get("insight") or parsed.get("micro_challenge") or parsed.get("affirmation"))
                else raw_text
            )
            return AdviceResponse(advice=advice_text)
        else:
            if DEMO_MODE:
                return AdviceResponse(advice=demo_advice(prompt))
            raise HTTPException(status_code=503, detail="Gemini API key not configured and DEMO_MODE disabled")
    except requests.exceptions.RequestException as re:
        logger.exception("RequestException calling Gemini: %s", re)
        if DEMO_MODE:
            return AdviceResponse(advice=demo_advice(prompt))
        raise HTTPException(status_code=502, detail=f"Upstream error: {re}")
    except Exception as e:
        logger.exception("Unhandled error in tools_advice: %s", e)
        if DEMO_MODE:
            return AdviceResponse(advice=demo_advice(prompt))
        raise HTTPException(status_code=500, detail="Internal error generating advice")

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
            raw_text = extract_text_from_gemini(resp_json)
            return {"response": raw_text}
        if DEMO_MODE:
            return {"response": demo_advice(q)}
        raise HTTPException(status_code=503, detail="No model configured")
    except Exception as e:
        logger.exception("Chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
