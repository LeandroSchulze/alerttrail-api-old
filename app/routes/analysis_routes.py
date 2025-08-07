
from fastapi import APIRouter

router = APIRouter()

@router.post("/analyze")
def analyze_logs():
    return {"message": "Análisis de logs simulado"}
