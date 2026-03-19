from typing import Any, Optional
import json
import os
from app.jobs.store import job_store, Job, JobStatus
from app.services.appwrite_db import appwrite_db
from app.utils.logger import logger

async def get_job_with_fallback(job_id: str) -> Optional[Job]:
    """Helper to get job from JobStore (now DB-backed)"""
    return job_store.get_job(job_id)
