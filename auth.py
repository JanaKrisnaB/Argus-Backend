"""
auth.py — FastAPI dependency for Supabase JWT verification.
Set DEV_MODE=true in .env to skip auth during local development.
"""
import os
import httpx
from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
DEV_MODE             = os.getenv("DEV_MODE", "true").lower() == "true"

DEV_USER = {"id": "dev-user-id", "email": "dev@local.dev"}


async def get_current_user(authorization: str = Header(default=None)) -> dict:
    """Verify Supabase JWT and return the user payload."""
    if DEV_MODE:
        return DEV_USER

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = authorization.split(" ", 1)[1]

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{SUPABASE_URL}/auth/v1/user",
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": SUPABASE_SERVICE_KEY,
            },
            timeout=10,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return resp.json()
