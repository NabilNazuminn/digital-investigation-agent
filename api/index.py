import sys
import os
from fastapi import FastAPI

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
app = FastAPI()

from app.main import app
@app.get("/health")
def health():
    return {"status": "ok"}