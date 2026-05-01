"""
main.py — FastAPI application entry point.
Run: uvicorn main:app --reload --port 8000
"""
import os
import sys

# Ensure the backend directory is always in sys.path
# so 'auth', 'schema', 'core.*' etc. are importable from anywhere
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from routes.review import router as review_router
from routes.memory import router as memory_router
from routes.auth   import router as auth_router

app = FastAPI(title="Argus Code Reviewer API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_URL", "http://localhost:5173"),
        "http://localhost:5173",
        "http://172.22.11.225:5173",
        "http://192.168.56.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(review_router, prefix="/api")
app.include_router(memory_router, prefix="/api")
app.include_router(auth_router,   prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "service": "argus-backend"}
