# ml/api/server.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ml.api.service import router as ml_router

app = FastAPI(title="ML API (recommend + ddl)", version="0.1.0")

# ✦ CORS для фронта
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173","http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ml_router, prefix="/ml")
