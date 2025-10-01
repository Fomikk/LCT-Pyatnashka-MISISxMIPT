# ml/api/server.py
from fastapi import FastAPI
from ml.api.service import router as ml_router
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="ML API (recommend + ddl)")
app.include_router(ml_router)
