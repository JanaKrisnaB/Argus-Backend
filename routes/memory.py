"""routes/memory.py — GET/DELETE /api/memory/{team_id}"""
from fastapi import APIRouter, Depends, HTTPException
from core.auth import get_current_user
from core.memory import get_all_memories, retrieve_similar, delete_memory, memory_count

router = APIRouter()


@router.get("/memory/count")
async def get_count(user: dict = Depends(get_current_user)):
    return {"count": memory_count(user["id"])}


@router.get("/memory")
async def list_memories(limit: int = 50, user: dict = Depends(get_current_user)):
    return {"memories": get_all_memories(user["id"], limit=limit)}


@router.get("/memory/search")
async def search_memories(q: str, top_k: int = 5, user: dict = Depends(get_current_user)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    results = retrieve_similar(user["id"], q, top_k=top_k)
    return {"memories": results}


@router.delete("/memory/{memory_id}")
async def remove_memory(memory_id: str, user: dict = Depends(get_current_user)):
    delete_memory(user["id"], memory_id)
    return {"deleted": memory_id}
