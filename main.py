"""
main.py — FastAPI application entry point.
Run: uvicorn main:app --reload --port 8000
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes.review import router as review_router
from routes.memory import router as memory_router
from routes.auth   import router as auth_router

load_dotenv()

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
