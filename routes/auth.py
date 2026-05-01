"""routes/auth.py — GET /api/auth/me"""
from fastapi import APIRouter, Depends
from core.auth import get_current_user

router = APIRouter()


@router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return {"id": user["id"], "email": user.get("email", "")}
