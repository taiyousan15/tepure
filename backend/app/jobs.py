"""
Job queue management with idempotency support
"""
import uuid
import structlog
from typing import Optional, Dict, Any, List
from datetime import datetime
from queue import Queue
from threading import Lock
from .sheets import GoogleSheetsClient
from .errors import IdempotencyConflictError

logger = structlog.get_logger()


class JobQueue:
    """
    In-memory job queue with idempotency support

    NOTE: For production, migrate to Cloud Tasks or Redis-based queue
    """

    def __init__(self):
        """Initialize job queue"""
        self.queue = Queue()
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.idempotency_map: Dict[str, str] = {}  # idempotency_key -> job_id
        self.lock = Lock()
        self.sheets_client = GoogleSheetsClient()
        logger.info("job_queue_initialized")

    def create_job(
        self,
        user_id: str,
        template_id: str,
        inputs: Dict[str, Any],
        temperature: float = 0.7,
        intensity: str = 'medium',
        idempotency_key: Optional[str] = None
    ) -> str:
        """
        Create a new job with idempotency support

        Args:
            user_id: User ID
            template_id: Template ID
            inputs: Input data for template
            temperature: LLM temperature (0.0-1.0)
            intensity: Generation intensity (low/medium/high)
            idempotency_key: Optional idempotency key

        Returns:
            Job ID
        """
        with self.lock:
            # Check idempotency
            if idempotency_key:
                existing_job_id = self.check_idempotency(idempotency_key)
                if existing_job_id:
                    logger.info(
                        "idempotent_job_returned",
                        idempotency_key=idempotency_key,
                        job_id=existing_job_id
                    )
                    return existing_job_id

            # Generate job ID
            timestamp = datetime.utcnow().isoformat()
            job_id = f"job_{timestamp.replace(':', '').replace('.', '').replace('-', '')[:17]}"

            # Create job record
            job_data = {
                'job_id': job_id,
                'user_id': user_id,
                'template_id': template_id,
                'status': 'pending',
                'inputs': inputs,
                'temperature': temperature,
                'intensity': intensity,
                'result': None,
                'error': None,
                'usage': None,
                'created_at': timestamp,
                'updated_at': None,
                'completed_at': None
            }

            self.jobs[job_id] = job_data

            # Store idempotency mapping
            if idempotency_key:
                self.idempotency_map[idempotency_key] = job_id

            # Add to queue
            self.queue.put(job_id)

            logger.info(
                "job_created",
                job_id=job_id,
                user_id=user_id,
                template_id=template_id,
                has_idempotency_key=bool(idempotency_key)
            )

            return job_id

    def check_idempotency(self, idempotency_key: str) -> Optional[str]:
        """
        Check if job with idempotency key already exists

        Args:
            idempotency_key: Idempotency key

        Returns:
            Existing job ID or None
        """
        return self.idempotency_map.get(idempotency_key)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status and result

        Args:
            job_id: Job ID

        Returns:
            Job data or None if not found
        """
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                logger.debug("job_status_retrieved", job_id=job_id, status=job['status'])
            return job

    def update_job_status(
        self,
        job_id: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        usage: Optional[Dict[str, Any]] = None
    ):
        """
        Update job status

        Args:
            job_id: Job ID
            status: New status (processing, completed, failed)
            result: Result data (for completed)
            error: Error message (for failed)
            usage: Token usage information
        """
        with self.lock:
            if job_id not in self.jobs:
                logger.warning("job_not_found", job_id=job_id)
                return

            timestamp = datetime.utcnow().isoformat()
            self.jobs[job_id].update({
                'status': status,
                'result': result,
                'error': error,
                'usage': usage,
                'updated_at': timestamp
            })

            if status in ['completed', 'failed']:
                self.jobs[job_id]['completed_at'] = timestamp

            logger.info(
                "job_status_updated",
                job_id=job_id,
                status=status,
                has_result=bool(result),
                has_error=bool(error)
            )

    def get_pending_jobs(self, limit: int = 10) -> List[str]:
        """
        Get pending job IDs

        Args:
            limit: Maximum number of jobs

        Returns:
            List of pending job IDs
        """
        job_ids = []
        for _ in range(min(limit, self.queue.qsize())):
            try:
                job_id = self.queue.get_nowait()
                job_ids.append(job_id)
            except Exception:
                break

        logger.debug("pending_jobs_retrieved", count=len(job_ids))
        return job_ids

    def get_job_count_by_status(self, status: str) -> int:
        """
        Get count of jobs by status

        Args:
            status: Job status

        Returns:
            Count of jobs with given status
        """
        with self.lock:
            count = sum(1 for job in self.jobs.values() if job['status'] == status)
            return count

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Get all jobs (for testing/debugging)

        Returns:
            List of all job data
        """
        with self.lock:
            return list(self.jobs.values())

    def clear_completed_jobs(self, older_than_hours: int = 24):
        """
        Clear completed jobs older than specified hours

        Args:
            older_than_hours: Clear jobs older than this many hours
        """
        with self.lock:
            now = datetime.utcnow()
            job_ids_to_remove = []

            for job_id, job in self.jobs.items():
                if job['status'] in ['completed', 'failed']:
                    completed_at = job.get('completed_at')
                    if completed_at:
                        completed_time = datetime.fromisoformat(completed_at)
                        hours_diff = (now - completed_time).total_seconds() / 3600
                        if hours_diff > older_than_hours:
                            job_ids_to_remove.append(job_id)

            for job_id in job_ids_to_remove:
                del self.jobs[job_id]

            logger.info("completed_jobs_cleared", count=len(job_ids_to_remove))


# Global job queue instance
job_queue = JobQueue()
