# Call Audit — Voice Failure Fixer

Detects failures in voice AI call transcripts and outputs exact prompt fixes to deploy.


## What it does

1. Paste 5–10 call transcripts
2. Detects primary failure per call (PROMISE_RISK, USER_CONFUSION, DEAD_END, etc.)
3. Shows severity (HIGH / MEDIUM / LOW)
4. Outputs the exact bad agent line + the exact replacement to deploy
5. Summary: top 3 failure patterns + top 3 ready-to-use prompt fixes

## Stack

- **Backend:** Python, FastAPI, Anthropic SDK
- **Frontend:** Vanilla JS + HTML (served by FastAPI)
- **AI:** openai/gpt-oss-120b:free
