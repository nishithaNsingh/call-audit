# Call Audit — Voice AI Failure Detector   

Paste raw call transcripts in, get back exactly which lines failed, why, and
the precise replacement line to deploy — not generic advice.

Originally built as a targeted technical demo for a voice AI company
(Samora AI) during outreach — scoped to solve one specific, real problem
their agents were likely hitting, not a generic tutorial project.

---


live = https://call-audit-imry.onrender.com/

## The problem

Voice AI agents fail in ways that don't show up as errors or crashes — they
show up as bad conversations. An agent that says "I'll get that resolved for
you" and then never follows through, or gets stuck restating the same
question when the user is confused, looks completely healthy on every
standard metric (uptime, latency, call completion rate). The only way to
catch it today is a human listening to — or reading — every transcript,
which doesn't scale past a handful of calls a day.

Most failure isn't a single bad response either. It's a *pattern*: the same
kind of breakdown recurring across many calls because of one bad line in the
system prompt. Finding that pattern by eye across dozens of transcripts is
slow and easy to miss.

## The solution

Call Audit takes a batch of transcripts, classifies the specific failure in
each one against a fixed taxonomy, and — critically — outputs the *exact*
replacement agent line, not a suggestion to "be clearer." That's the design
constraint that matters: the output has to be something you can paste
straight into a prompt and ship, not something a PM has to translate into an
actual fix first.

**Failure taxonomy:**

| Type | What it catches |
|---|---|
| `PROMISE_RISK` | Agent commits to something ("I'll send that over") with no follow-through path |
| `USER_CONFUSION` | User has to repeat or rephrase because the agent didn't land the point |
| `DEAD_END` | Conversation has nowhere to go — agent can't answer and doesn't redirect |
| `OVER_VERIFICATION` | Agent re-confirms already-confirmed information, wasting the call |
| `INFORMATION_OVERLOAD` | Agent dumps more than the user can act on in one turn |

Each detected failure gets a severity (`HIGH` / `MEDIUM` / `LOW`), the exact
bad line quoted from the transcript, and a ready-to-use replacement line.
Across a batch, it also rolls up the top 3 recurring failure patterns and
top 3 concrete prompt fixes — the part that turns "here's what's wrong with
call #4" into "here's what to change in your system prompt."

## How it works

1. Paste 5–10 call transcripts into the browser UI
2. `POST /analyze` sends them to an LLM with a strict JSON-schema system
   prompt — classification, not open-ended commentary
3. Response is parsed and validated as structured JSON (malformed output is
   caught and surfaced as an error, not silently swallowed)
4. UI renders per-call failures + the cross-call summary

```
POST /analyze
{ "transcripts": "Call 1:\nAgent: ...\nUser: ...\n\nCall 2:\n..." }

→ {
    "calls": [
      { "id": "Call 1", "failure_type": "PROMISE_RISK", "severity": "HIGH",
        "reason": "...", "bad_response": "...", "improved_response": "..." }
    ],
    "summary": {
      "top_failures": ["PROMISE_RISK (3 calls)", ...],
      "top_fixes": ["Add explicit no-follow-up-promises rule to system prompt", ...]
    }
  }
```

## Tech stack

Python · FastAPI · httpx (async) · OpenRouter (LLM inference, currently
`gpt-oss-120b`) · vanilla JS/HTML frontend served directly by FastAPI

The LLM call goes through OpenRouter's OpenAI-compatible API, so swapping
models (or providers) is a one-line change in `main.py` — no code depends
on a specific vendor's SDK.

## Setup

```
pip install -r requirements.txt
echo "OPENROUTER_API_KEY=your_key_here" > .env
uvicorn main:app --reload
```
Visit `http://localhost:8000`.

## Design notes

- **Strict JSON-only system prompt, not free text** — the model is
  constrained to a fixed schema so the frontend can render results reliably
  instead of parsing loose natural language.
- **Malformed model output fails loudly** (`500` with a clear error) instead
  of returning partial or guessed data — for a tool meant to inform real
  prompt changes, a wrong silent answer is worse than a visible failure.
- **Single-file backend, on purpose.** This is a focused demo solving one
  problem end-to-end, not a scaffold for a larger product — kept intentionally
  small rather than padded with unused structure.

## What's next

- Batch history / persistence, so recurring patterns can be tracked across
  audits over time instead of one paste at a time
- Structured output validation (Pydantic model on the LLM response) instead
  of a bare `json.loads`, so a schema drift fails with a specific field error
- Support pasting a call recording URL and transcribing it inline, instead
  of requiring transcripts to already exist
