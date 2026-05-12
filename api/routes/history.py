from fastapi import APIRouter
from core.runner import load_job_history

router = APIRouter(prefix="/history", tags=["history"])

@router.get("")
def get_history(limit: int = 50):
    return load_job_history(limit)