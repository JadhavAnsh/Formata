# In-memory job store with disk persistence
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from enum import Enum
import json
import os
import uuid
import math

from app.utils.logger import logger


JOB_STATE_PATH = os.path.join("storage", "jobs", "job_store.json")


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Job entity"""
    
    def __init__(self, job_id: str, file_name: str, file_path: str):
        self.job_id = job_id
        self.file_name = file_name
        self.file_path = file_path
        self.status = JobStatus.PENDING
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.progress = 0.0
        self.result: Optional[Dict[str, Any]] = None
        self.errors: List[str] = []
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary"""
        payload = {
            "job_id": self.job_id,
            "file_name": self.file_name,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "progress": self.progress,
            "result": self.result,
            "errors": self.errors,
            "metadata": self.metadata,
        }
        return _to_json_safe(payload)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Job":
        job = cls(
            job_id=str(payload.get("job_id", "")),
            file_name=str(payload.get("file_name", "")),
            file_path=str(payload.get("file_path", "")),
        )

        status_value = payload.get("status", JobStatus.PENDING.value)
        try:
            job.status = JobStatus(status_value)
        except Exception:
            job.status = JobStatus.PENDING

        created_at = payload.get("created_at")
        started_at = payload.get("started_at")
        completed_at = payload.get("completed_at")

        if isinstance(created_at, str) and created_at:
            try:
                job.created_at = datetime.fromisoformat(created_at)
            except Exception:
                pass
        if isinstance(started_at, str) and started_at:
            try:
                job.started_at = datetime.fromisoformat(started_at)
            except Exception:
                pass
        if isinstance(completed_at, str) and completed_at:
            try:
                job.completed_at = datetime.fromisoformat(completed_at)
            except Exception:
                pass

        progress = payload.get("progress", 0.0)
        try:
            job.progress = max(0.0, min(1.0, float(progress)))
        except Exception:
            job.progress = 0.0

        result = payload.get("result")
        if isinstance(result, dict):
            job.result = result

        errors = payload.get("errors", [])
        if isinstance(errors, list):
            job.errors = [str(error) for error in errors]

        metadata = payload.get("metadata", {})
        if isinstance(metadata, dict):
            job.metadata = metadata

        return job


def _to_json_safe(value: Any) -> Any:
    """Recursively sanitize values for strict JSON compliance."""
    if value is None:
        return None

    if isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        return value if math.isfinite(value) else None

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, dict):
        return {str(k): _to_json_safe(v) for k, v in value.items()}

    if isinstance(value, list):
        return [_to_json_safe(v) for v in value]

    if isinstance(value, tuple):
        return [_to_json_safe(v) for v in value]

    if hasattr(value, "item"):
        try:
            return _to_json_safe(value.item())
        except Exception:
            pass

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass

    return str(value)


class JobStore:
    """
    In-memory storage for job states and results
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self._state_path = JOB_STATE_PATH
        self._load_state()

    def _ensure_state_dir(self) -> None:
        os.makedirs(os.path.dirname(self._state_path), exist_ok=True)

    def _load_state(self) -> None:
        if not os.path.exists(self._state_path):
            return

        try:
            with open(self._state_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)

            jobs_payload = payload.get("jobs", {}) if isinstance(payload, dict) else {}
            restored: Dict[str, Job] = {}
            if isinstance(jobs_payload, dict):
                for job_id, job_payload in jobs_payload.items():
                    if isinstance(job_payload, dict):
                        restored[str(job_id)] = Job.from_dict(job_payload)

            self.jobs = restored
            logger.info(f"Loaded {len(self.jobs)} jobs from disk state")
        except Exception as exc:
            logger.warning(f"Failed to load job state: {exc}")

    def _save_state(self) -> None:
        try:
            self._ensure_state_dir()
            payload = {
                "jobs": {job_id: job.to_dict() for job_id, job in self.jobs.items()},
                "saved_at": datetime.now().isoformat(),
            }
            temp_path = f"{self._state_path}.tmp"
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            os.replace(temp_path, self._state_path)
        except Exception as exc:
            logger.warning(f"Failed to save job state: {exc}")
    
    def create_job(self, file_name: str, file_path: str) -> str:
        """Create a new job entry and return job_id"""
        job_id = str(uuid.uuid4())
        job = Job(job_id, file_name, file_path)
        self.jobs[job_id] = job
        self._save_state()
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID"""
        return self.jobs.get(job_id)
    
    def update_job_status(self, job_id: str, status: JobStatus) -> bool:
        """Update job status"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        job.status = status
        
        if status == JobStatus.PROCESSING:
            job.started_at = datetime.now()
        elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            job.completed_at = datetime.now()
        self._save_state()
        return True
    
    def update_job_progress(self, job_id: str, progress: float) -> bool:
        """Update job progress (0.0 to 1.0)"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].progress = max(0.0, min(1.0, progress))
        self._save_state()
        return True
    
    def add_job_error(self, job_id: str, error: str) -> bool:
        """Add error to job"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].errors.append(error)
        self._save_state()
        return True
    
    def set_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Set job result"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].result = result
        self._save_state()
        return True
    
    def set_job_metadata(self, job_id: str, metadata: Dict[str, Any]) -> bool:
        """Set job metadata"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].metadata = metadata
        self._save_state()
        return True
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs as dictionaries"""
        return [job.to_dict() for job in self.jobs.values()]
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            self._save_state()
            return True
        return False
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job exists"""
        return job_id in self.jobs


# Global job store instance
job_store = JobStore()
