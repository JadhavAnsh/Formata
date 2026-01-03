# In-memory job store
from typing import Dict, Any
from datetime import datetime


class JobStore:
    """
    In-memory storage for job states and results
    """
    
    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
    
    def create_job(self, job_id: str, **kwargs) -> None:
        """Create a new job entry"""
        self.jobs[job_id] = {
            "status": "pending",
            "created_at": datetime.now(),
            **kwargs
        }
    
    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get job details"""
        return self.jobs.get(job_id)
    
    def update_job(self, job_id: str, **kwargs) -> None:
        """Update job details"""
        if job_id in self.jobs:
            self.jobs[job_id].update(kwargs)


# Global job store instance
job_store = JobStore()
