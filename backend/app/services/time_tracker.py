# Job timing and performance tracking module
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.utils.logger import logger


class JobTimeTracker:
    """Track processing time for job steps"""
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.steps: Dict[str, Dict[str, Any]] = {}
        self.start_time = time.time()
        
    def start_step(self, step_name: str) -> None:
        """Mark the start of a processing step"""
        if step_name not in self.steps:
            self.steps[step_name] = {}
        self.steps[step_name]["start_time"] = time.time()
        logger.info(f"[TIMER] Job {self.job_id} - Step '{step_name}' started")
    
    def end_step(self, step_name: str, details: Optional[Dict[str, Any]] = None) -> float:
        """Mark the end of a processing step and return duration in seconds"""
        if step_name not in self.steps:
            self.steps[step_name] = {}
        
        start = self.steps[step_name].get("start_time", time.time())
        duration = time.time() - start
        
        self.steps[step_name]["end_time"] = time.time()
        self.steps[step_name]["duration_seconds"] = duration
        if details:
            self.steps[step_name]["details"] = details
        
        logger.info(f"[TIMER] Job {self.job_id} - Step '{step_name}' completed in {duration:.2f}s")
        return duration
    
    def get_total_time(self) -> float:
        """Get total processing time in seconds"""
        return time.time() - self.start_time
    
    def get_step_time(self, step_name: str) -> Optional[float]:
        """Get specific step duration in seconds"""
        if step_name in self.steps:
            return self.steps[step_name].get("duration_seconds")
        return None
    
    def get_summary(self) -> Dict[str, Any]:
        """Get complete timing summary"""
        total_time = self.get_total_time()
        
        step_summaries = {}
        for step_name, step_data in self.steps.items():
            step_summaries[step_name] = {
                "duration_seconds": step_data.get("duration_seconds", 0),
                "duration_formatted": self._format_duration(step_data.get("duration_seconds", 0)),
                "details": step_data.get("details", {})
            }
        
        return {
            "job_id": self.job_id,
            "total_seconds": total_time,
            "total_formatted": self._format_duration(total_time),
            "timestamp": datetime.now().isoformat(),
            "steps": step_summaries
        }
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.2f}s"
        else:
            minutes = seconds / 60
            return f"{minutes:.2f}m"
    
    def log_summary(self) -> str:
        """Log and return timing summary as formatted string"""
        summary = self.get_summary()
        
        log_lines = [
            f"\n{'='*60}",
            f"JOB TIMING SUMMARY: {summary['job_id']}",
            f"{'='*60}",
            f"Total Time: {summary['total_formatted']}",
            "-" * 60,
        ]
        
        for step_name, step_info in summary['steps'].items():
            log_lines.append(f"{step_name}: {step_info['duration_formatted']}")
            if step_info['details']:
                for detail_key, detail_val in step_info['details'].items():
                    log_lines.append(f"  └─ {detail_key}: {detail_val}")
        
        log_lines.append("=" * 60)
        
        result = "\n".join(log_lines)
        logger.info(result)
        return result


# Global tracker registry (for multi-job management)
_trackers: Dict[str, JobTimeTracker] = {}


def get_tracker(job_id: str) -> JobTimeTracker:
    """Get or create a tracker for a job"""
    if job_id not in _trackers:
        _trackers[job_id] = JobTimeTracker(job_id)
    return _trackers[job_id]


def cleanup_tracker(job_id: str) -> None:
    """Clean up tracker after job completion"""
    if job_id in _trackers:
        del _trackers[job_id]
