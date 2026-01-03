# /convert endpoint
from fastapi import APIRouter

router = APIRouter(prefix="/convert", tags=["convert"])


@router.post("/")
async def convert_data():
    """
    Convert between formats (CSV ↔ JSON)
    """
    pass
