"""
core/reviewer.py — Orchestrates the full review pipeline.

API call budget per request:
  Config A: 2 calls  (LLM review + parse)
  Config B: ~4 calls (agent + tools + parse)
  Config C: ~4 + N   (agent + tools + parse + N critic calls)
"""
import json
import os

from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv

from core.tools import TOOLS
from core.memory import retrieve_similar, store_comment, memory_count
from core.critic import filter_comments, STORE_THRESHOLD

load_dotenv()

_llm   = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
_agent = create_react_agent(_llm, TOOLS)


def _parse_comments(raw: str) -> list:
    """Convert agent plain-text output to structured comment list (1 LLM call)."""
    prompt = (
        "Convert this code review to a JSON array. "
        "Each item: line (int), comment (str), severity (low/medium/high), confidence (float 0-1). "
        "Return ONLY valid JSON, no markdown.\n\nReview:\n" + raw
    )
    resp = _llm.invoke(prompt)
    try:
        clean = resp.content.strip().replace("```json", "").replace("```", "")
        return json.loads(clean)
    except Exception as exc:
        print(f"Parse error: {exc}")
        return []


def _agent_review(code: str, team_id: str) -> str:
    """Run the ReAct agent with memory context. Returns raw text output."""
    memories = retrieve_similar(team_id, code)
    if memories:
        mem_block = "PAST REVIEW DECISIONS:\n" + "\n".join(
            f"- {m['comment']} ({m['severity']})" for m in memories
        )
    else:
        mem_block = "No past decisions found."

    prompt = f"Review this Python code.\n\n{mem_block}\n\nCode:\n{code}"
    result = _agent.invoke({"messages": [("user", prompt)]})
    return result["messages"][-1].content


def run_review(team_id: str, code: str, config: str) -> dict:
    """
    Main entry point. Returns dict with comments, critic_log, memory_count.
    config: "A" | "B" | "C"
    """
    # ── Config A: plain LLM, no tools, no memory ──────────
    if config == "A":
        raw      = _llm.invoke(f"Review this Python code and list all issues:\n{code}").content
        comments = _parse_comments(raw)
        return {
            "comments":     comments,
            "critic_log":   "Critic not active for Config A.",
            "memory_count": memory_count(team_id),
        }

    # ── Config B: agent + tools + memory, no critic ───────
    if config == "B":
        raw      = _agent_review(code, team_id)
        comments = _parse_comments(raw)
        for c in comments:
            if c.get("confidence", 0) >= STORE_THRESHOLD:
                store_comment(team_id, code, c)
        return {
            "comments":     comments,
            "critic_log":   "Critic not active for Config B.",
            "memory_count": memory_count(team_id),
        }

    # ── Config C: agent + tools + memory + critic ─────────
    raw          = _agent_review(code, team_id)
    all_comments = _parse_comments(raw)
    approved, log = filter_comments(code, all_comments)

    for c in approved:
        if c.get("confidence", 0) >= STORE_THRESHOLD:
            store_comment(team_id, code, c)

    return {
        "comments":     approved,
        "critic_log":   "\n".join(log),
        "memory_count": memory_count(team_id),
    }
