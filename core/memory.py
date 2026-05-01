"""
core/memory.py — Per-team ChromaDB memory.
Each user/team gets an isolated ChromaDB collection: team_{user_id}
Zero LLM API calls — embeddings are local (SentenceTransformer).
"""
import uuid
from typing import List

import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH    = "./chroma_data"
EMBEDDER_MODEL = "all-MiniLM-L6-v2"

_client   = chromadb.PersistentClient(path=CHROMA_PATH)
_embedder = SentenceTransformer(EMBEDDER_MODEL)


def _collection(team_id: str):
    """Get or create a per-team ChromaDB collection."""
    # ChromaDB collection names: alphanumeric + underscores only
    safe_id = team_id.replace("-", "_")
    return _client.get_or_create_collection(
        name=f"team_{safe_id}",
        metadata={"heuristic": "cosine"},
    )


def store_comment(team_id: str, code: str, comment: dict) -> None:
    col  = _collection(team_id)
    text = f"CODE:\n{code}\nCOMMENT:\n{comment['comment']}"
    col.add(
        ids=[str(uuid.uuid4())],
        embeddings=[_embedder.encode(text).tolist()],
        documents=[text],
        metadatas=[{
            "line":       comment["line"],
            "comment":    comment["comment"],
            "severity":   comment["severity"],
            "confidence": float(comment["confidence"]),
        }],
    )


def retrieve_similar(team_id: str, code: str, top_k: int = 3) -> List[dict]:
    col = _collection(team_id)
    if col.count() == 0:
        return []
    results = col.query(
        query_embeddings=[_embedder.encode(f"CODE:\n{code}").tolist()],
        n_results=min(top_k, col.count()),
    )
    memories = [
        {
            "comment":    results["metadatas"][0][i]["comment"],
            "severity":   results["metadatas"][0][i]["severity"],
            "confidence": results["metadatas"][0][i]["confidence"],
            "distance":   results["distances"][0][i],
        }
        for i in range(len(results["ids"][0]))
    ]
    return sorted(memories, key=lambda x: x["distance"])


def get_all_memories(team_id: str, limit: int = 50) -> List[dict]:
    col = _collection(team_id)
    if col.count() == 0:
        return []
    results = col.get(limit=limit, include=["metadatas"])
    return [
        {
            "id":         results["ids"][i],
            "comment":    results["metadatas"][i]["comment"],
            "severity":   results["metadatas"][i]["severity"],
            "confidence": results["metadatas"][i]["confidence"],
        }
        for i in range(len(results["ids"]))
    ]


def delete_memory(team_id: str, memory_id: str) -> None:
    _collection(team_id).delete(ids=[memory_id])


def memory_count(team_id: str) -> int:
    return _collection(team_id).count()
