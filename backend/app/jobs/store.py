# In-memory job store
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid


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
        return {
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


class JobStore:
    """
    In-memory storage for job states and results
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
    
    def create_job(self, file_name: str, file_path: str) -> str:
        """Create a new job entry and return job_id"""
        job_id = str(uuid.uuid4())
        job = Job(job_id, file_name, file_path)
        self.jobs[job_id] = job
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
        
        return True
    
    def update_job_progress(self, job_id: str, progress: float) -> bool:
        """Update job progress (0.0 to 1.0)"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].progress = max(0.0, min(1.0, progress))
        return True
    
    def add_job_error(self, job_id: str, error: str) -> bool:
        """Add error to job"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].errors.append(error)
        return True
    
    def set_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Set job result"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].result = result
        return True
    
    def set_job_metadata(self, job_id: str, metadata: Dict[str, Any]) -> bool:
        """Set job metadata"""
        if job_id not in self.jobs:
            return False
        
        self.jobs[job_id].metadata = metadata
        return True
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs as dictionaries"""
        return [job.to_dict() for job in self.jobs.values()]
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        if job_id in self.jobs:
            del self.jobs[job_id]
            return True
        return False
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job exists"""
        return job_id in self.jobs


# Global job store instance
job_store = JobStore()
