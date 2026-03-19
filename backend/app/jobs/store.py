# Job store backed by Appwrite DB
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import uuid
import json

from app.services.appwrite_db import appwrite_db
from app.utils.logger import logger


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Job:
    """Job entity for data transfer and local processing"""
    
    def __init__(self, job_id: str, file_name: str, file_path: str, user_id: str = None):
        self.job_id = job_id
        self.user_id = user_id
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

    @classmethod
    def from_db(cls, job_id: str, doc: Dict[str, Any]) -> 'Job':
        """Create a Job object from an Appwrite document"""
        job = cls(
            job_id=job_id,
            file_name=doc.get("file-name") or doc.get("file_name", "unknown"),
            file_path=f"appwrite://{doc.get('file_id')}" if doc.get('file_id') else "unknown",
            user_id=doc.get("user_id")
        )
        job.status = JobStatus(doc.get("status", "pending"))
        job.progress = doc.get("progress", 0.0)
        
        # Parse created_at
        created_at_str = doc.get("created_at")
        if created_at_str:
            try:
                job.created_at = datetime.fromisoformat(created_at_str)
            except:
                pass
        
        # Parse metadata
        metadata_raw = doc.get("metadata", "{}")
        if isinstance(metadata_raw, str):
            try:
                job.metadata = json.loads(metadata_raw)
            except:
                job.metadata = {}
        else:
            job.metadata = metadata_raw or {}
            
        if "result" in job.metadata:
            job.result = job.metadata["result"]
        if "errors" in job.metadata:
            job.errors = job.metadata["errors"]
            
        return job
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for API response"""
        return {
            "job_id": self.job_id,
            "user_id": self.user_id,
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
    Job storage interface that persists to Appwrite DB
    """
    
    def create_job(self, file_name: str, file_path: str, user_id: str = None, job_id: str = None) -> str:
        """Create a new job entry in DB and return job_id"""
        if not job_id:
            job_id = str(uuid.uuid4())
            
        # Extract file_id from appwrite:// protocol if present
        file_id = file_path.replace("appwrite://", "") if file_path.startswith("appwrite://") else ""
            
        job_data = {
            "user_id": user_id,
            "file_id": file_id,
            "file-name": file_name,
            "status": JobStatus.PENDING.value,
            "progress": 0.0,
            "created_at": datetime.now().isoformat(),
            "metadata": "{}"
        }
        
        try:
            appwrite_db.create_job_document(job_id, job_data)
            return job_id
        except Exception as e:
            logger.error(f"Failed to create job in DB: {str(e)}")
            # Fallback to a temporary job ID (though it won't be persisted well)
            return job_id
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job from DB by ID"""
        try:
            doc = appwrite_db.get_job_document(job_id)
            return Job.from_db(job_id, doc)
        except Exception as e:
            logger.error(f"Failed to fetch job {job_id} from DB: {str(e)}")
            return None
    
    def update_job_status(self, job_id: str, status: JobStatus) -> bool:
        """Update job status in DB"""
        update_data = {"status": status.value}
        
        # Note: started_at and completed_at logic should ideally be in DB schema, 
        # but for now we'll stick to what the worker does or put it in metadata.
        
        try:
            return appwrite_db.update_job_document(job_id, update_data)
        except Exception as e:
            logger.error(f"Failed to update job status {job_id}: {str(e)}")
            return False
    
    def update_job_progress(self, job_id: str, progress: float) -> bool:
        """Update job progress in DB"""
        try:
            return appwrite_db.update_job_document(job_id, {"progress": max(0.0, min(1.0, progress))})
        except Exception as e:
            logger.error(f"Failed to update job progress {job_id}: {str(e)}")
            return False
    
    def add_job_error(self, job_id: str, error: str) -> bool:
        """Add error to job metadata in DB"""
        job = self.get_job(job_id)
        if not job:
            return False
            
        job.errors.append(error)
        try:
            metadata = job.metadata
            metadata["errors"] = job.errors
            return appwrite_db.update_job_document(job_id, {"metadata": json.dumps(metadata)})
        except Exception as e:
            logger.error(f"Failed to add job error {job_id}: {str(e)}")
            return False
    
    def set_job_result(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Set job result in DB by merging with existing metadata"""
        try:
            doc = appwrite_db.get_job_document(job_id)
            metadata_raw = doc.get("metadata", "{}")
            metadata = {}
            if isinstance(metadata_raw, str):
                try:
                    metadata = json.loads(metadata_raw)
                except:
                    pass
            else:
                metadata = metadata_raw or {}
                
            metadata["result"] = result
            return appwrite_db.update_job_document(job_id, {"metadata": json.dumps(metadata)})
        except Exception as e:
            logger.error(f"Failed to set job result {job_id}: {str(e)}")
            return False
    
    def set_job_metadata(self, job_id: str, metadata: Dict[str, Any]) -> bool:
        """Set job metadata in DB by merging with existing metadata"""
        try:
            doc = appwrite_db.get_job_document(job_id)
            metadata_raw = doc.get("metadata", "{}")
            existing_metadata = {}
            if isinstance(metadata_raw, str):
                try:
                    existing_metadata = json.loads(metadata_raw)
                except:
                    pass
            else:
                existing_metadata = metadata_raw or {}
            
            # Merge existing metadata with new metadata
            existing_metadata.update(metadata)
            return appwrite_db.update_job_document(job_id, {"metadata": json.dumps(existing_metadata)})
        except Exception as e:
            logger.error(f"Failed to set job metadata {job_id}: {str(e)}")
            return False
    
    def get_jobs_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all jobs for a specific user from DB"""
        try:
            docs = appwrite_db.list_user_jobs(user_id)
            return [Job.from_db(doc['$id'], doc).to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Failed to fetch user jobs for {user_id}: {str(e)}")
            return []
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from DB"""
        try:
            return appwrite_db.delete_job_document(job_id)
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {str(e)}")
            return False
    
    def job_exists(self, job_id: str) -> bool:
        """Check if job exists in DB"""
        return self.get_job(job_id) is not None


# Global job store instance
job_store = JobStore()
