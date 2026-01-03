# /ingest endpoint
from fastapi import APIRouter, UploadFile, File

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/")
async def ingest_data(file: UploadFile = File(...)):
    """
    Ingest raw data file (CSV, JSON, Excel, MD)
    """
    pass
