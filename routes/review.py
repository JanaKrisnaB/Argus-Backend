"""routes/review.py — POST /api/review"""
import os
from fastapi import APIRouter, Depends
from supabase import create_client
from core.schema import ReviewRequest, ReviewResponse
from core.auth import get_current_user
from core.reviewer import run_review
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

_supa_url = os.getenv("SUPABASE_URL", "")
_supa_key = os.getenv("SUPABASE_SERVICE_KEY", "")
_db = create_client(_supa_url, _supa_key) if _supa_url and _supa_key else None


@router.post("/review", response_model=ReviewResponse)
async def review(body: ReviewRequest, user: dict = Depends(get_current_user)):
    team_id = user["id"]
    result  = run_review(team_id, body.code, body.config)

    # Persist review history to Supabase (best-effort)
    if _db:
        try:
            _db.table("reviews").insert({
                "user_id":      team_id,
                "code_snippet": body.code[:600],
                "config":       body.config,
                "comment_count": len(result["comments"]),
                "comments":     result["comments"],
            }).execute()
        except Exception as exc:
            print(f"Supabase insert error: {exc}")

    return ReviewResponse(
        comments=result["comments"],
        critic_log=result["critic_log"],
        memory_count=result["memory_count"],
    )
