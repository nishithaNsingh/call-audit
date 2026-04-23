from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import json
import re
import os
from dotenv import load_dotenv
load_dotenv()
app = FastAPI(title="Samora Call Audit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

SYSTEM_PROMPT = """You are a voice AI quality analyst for Samora AI.
Analyze call transcripts and return ONLY valid JSON — no markdown, no explanation.

Return this exact structure:
{
  "calls": [
    {
      "id": "Call 1",
      "failure_type": "PROMISE_RISK | USER_CONFUSION | DEAD_END | OVER_VERIFICATION | INFORMATION_OVERLOAD | NONE",
      "severity": "HIGH | MEDIUM | LOW | NONE",
      "reason": "one sentence explaining the failure",
      "bad_response": "the exact agent line that caused the failure",
      "improved_response": "the exact replacement line the agent should say instead"
    }
  ],
  "summary": {
    "top_failures": ["FAILURE_TYPE (N calls)", ...],
    "top_fixes": ["concrete prompt-level instruction ready to deploy", ...]
  }
}

Rules:
- improved_response must be a specific ready-to-use agent line, not advice
- top_fixes must be concrete prompt instructions, not generic tips
- Return max 3 items in top_failures and top_fixes
- If a call has no failure, set failure_type and severity to NONE"""


class AnalyzeRequest(BaseModel):
    transcripts: str


@app.get("/", response_class=HTMLResponse)
async def root():
    with open("templates/index.html") as f:
        return f.read()


@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if not req.transcripts.strip():
        raise HTTPException(status_code=400, detail="Transcripts cannot be empty")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "openai/gpt-oss-120b:free",
                "max_tokens": 1500,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze these call transcripts:\n\n{req.transcripts}"}
                ]
            },
            timeout=60.0
        )
        if response.status_code != 200:
            print(response.text)  # shows exact error in terminal
            response.raise_for_status()
        data = response.json()

    raw = data["choices"][0]["message"]["content"]
    clean = re.sub(r"```json|```", "", raw).strip()

    try:
        result = json.loads(clean)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response")

    return result
