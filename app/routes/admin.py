
from fastapi import APIRouter

router = APIRouter()

@router.get("/stats")
def admin_stats():
    return {"users": 10, "analyses": 50}
