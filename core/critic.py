"""
core/critic.py — Critic chain: validates each review comment (1 LLM call each).
"""
import json
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

_llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

_prompt = ChatPromptTemplate.from_messages([
    ("system", """\
You are a strict code review critic.
Check each comment for:
1. Is the line number plausible?
2. Is it relevant to the code?
3. Is it a real issue (not noise like "complexity is low")?
4. Is the confidence justified?

Respond ONLY with valid JSON:
{{
  "approved": true or false,
  "reason": "brief reason",
  "adjusted_confidence": 0.0 to 1.0
}}"""),
    ("user", """\
Code:
{code}

Comment — Line: {line} | Severity: {severity} | Confidence: {confidence}
{comment}

Valid and useful?"""),
])

_chain = _prompt | _llm

CRITIC_THRESHOLD = 0.7
STORE_THRESHOLD  = 0.8


def evaluate_comment(code: str, comment: dict) -> dict:
    """Run the critic on a single comment. Returns approval dict."""
    try:
        resp  = _chain.invoke({
            "code":       code,
            "line":       comment["line"],
            "comment":    comment["comment"],
            "severity":   comment["severity"],
            "confidence": comment["confidence"],
        })
        clean = resp.content.strip().replace("```json", "").replace("```", "")
        return json.loads(clean)
    except Exception as exc:
        print(f"Critic error: {exc}")
        return {"approved": False, "reason": "parse error", "adjusted_confidence": 0.0}


def filter_comments(code: str, comments: list) -> tuple[list, list]:
    """
    Run every comment through the critic.
    Returns (approved_comments, critic_log_lines).
    """
    approved = []
    log      = []

    for c in comments:
        verdict = evaluate_comment(code, c)
        if verdict["approved"] and verdict["adjusted_confidence"] >= CRITIC_THRESHOLD:
            approved.append({**c, "confidence": verdict["adjusted_confidence"]})
            log.append(f"APPROVED  Line {c['line']} | {c['comment'][:60]}")
        else:
            log.append(f"REJECTED  Line {c['line']} | {verdict['reason']}")

    return approved, log
