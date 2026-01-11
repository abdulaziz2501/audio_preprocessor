"""
AudioAI - Batch Processor Module
Background task processing for large batches

Bu modul katta hajmdagi audio fayllarni
background da processing qilish uchun ishlatiladi.
"""

import os
import uuid
import asyncio
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from dataclasses import dataclass, field
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class VerificationTask:
    """
    Bitta audio verification task.
    
    Attributes:
        task_id: Unique task ID
        audio_path: Audio fayl yo'li
        audio_name: Original fayl nomi
        reference_text: Reference matn
        status: Task holati
        progress: Progress (0-100)
        result: Verification natijasi
        error: Xato xabari
        created_at: Yaratilgan vaqt
        started_at: Boshlangan vaqt
        completed_at: Tugallangan vaqt
    """
    task_id: str
    audio_path: str
    audio_name: str
    reference_text: str
    status: str = "pending"  # pending, processing, completed, failed
    progress: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Task ni dict ga aylantirish."""
        return {
            'task_id': self.task_id,
            'audio_name': self.audio_name,
            'status': self.status,
            'progress': self.progress,
            'result': self.result,
            'error': self.error,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }


@dataclass
class BatchJob:
    """
    Batch processing job.
    
    Bir nechta VerificationTask larni o'z ichiga oladi.
    """
    job_id: str
    reference_text: str
    tasks: List[VerificationTask] = field(default_factory=list)
    status: str = "queued"  # queued, running, completed, partial, failed
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    options: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_tasks(self) -> int:
        return len(self.tasks)
    
    @property
    def completed_tasks(self) -> int:
        return sum(1 for t in self.tasks if t.status == "completed")
    
    @property
    def failed_tasks(self) -> int:
        return sum(1 for t in self.tasks if t.status == "failed")
    
    @property
    def progress(self) -> float:
        if self.total_tasks == 0:
            return 0
        return (self.completed_tasks + self.failed_tasks) / self.total_tasks * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """Job ni dict ga aylantirish."""
        return {
            'job_id': self.job_id,
            'status': self.status,
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'progress': self.progress,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'tasks': [t.to_dict() for t in self.tasks]
        }


class BatchProcessor:
    """
    Batch Processing Manager.
    
    Katta hajmdagi audio fayllarni background da
    processing qilish uchun manager.
    
    Attributes:
        max_workers (int): Maksimal parallel worker soni
        jobs (dict): Active jobs
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        use_multiprocessing: bool = False
    ):
        """
        BatchProcessor ni ishga tushirish.
        
        Args:
            max_workers: Parallel worker soni
            use_multiprocessing: Process pool ishlatish (CPU intensive)
        """
        self.max_workers = max_workers
        self.use_multiprocessing = use_multiprocessing
        
        # Jobs storage (in-memory)
        self.jobs: Dict[str, BatchJob] = {}
        
        # Lock for thread safety
        self._lock = threading.Lock()
        
        # Background executor
        if use_multiprocessing:
            self._executor = ProcessPoolExecutor(max_workers=max_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Task processing function
        self._process_func: Optional[Callable] = None
        
        logger.info(f"BatchProcessor initialized: max_workers={max_workers}")
    
    def set_processor(self, func: Callable) -> None:
        """
        Task processing funksiyasini o'rnatish.
        
        Args:
            func: Processing funksiyasi (audio_path, reference_text, options) -> result
        """
        self._process_func = func
    
    def create_job(
        self,
        audio_files: List[Dict[str, str]],
        reference_text: str,
        options: Optional[Dict[str, Any]] = None
    ) -> BatchJob:
        """
        Yangi batch job yaratish.
        
        Args:
            audio_files: Audio fayllar ro'yxati [{'path': ..., 'name': ...}, ...]
            reference_text: Reference matn
            options: Processing options
            
        Returns:
            BatchJob: Yaratilgan job
        """
        job_id = str(uuid.uuid4())
        
        # Tasks yaratish
        tasks = []
        for audio_info in audio_files:
            task = VerificationTask(
                task_id=str(uuid.uuid4()),
                audio_path=audio_info['path'],
                audio_name=audio_info['name'],
                reference_text=reference_text
            )
            tasks.append(task)
        
        # Job yaratish
        job = BatchJob(
            job_id=job_id,
            reference_text=reference_text,
            tasks=tasks,
            options=options or {}
        )
        
        # Jobs ga qo'shish
        with self._lock:
            self.jobs[job_id] = job
        
        logger.info(f"Created batch job {job_id} with {len(tasks)} tasks")
        
        return job
    
    async def start_job(self, job_id: str) -> None:
        """
        Job ni background da boshlash.
        
        Args:
            job_id: Job ID
        """
        if job_id not in self.jobs:
            raise ValueError(f"Job not found: {job_id}")
        
        job = self.jobs[job_id]
        
        if job.status != "queued":
            raise ValueError(f"Job already started: {job_id}")
        
        # Job statusini yangilash
        job.status = "running"
        job.started_at = datetime.utcnow()
        
        # Background task boshlash
        asyncio.create_task(self._run_job(job_id))
        
        logger.info(f"Started job {job_id}")
    
    async def _run_job(self, job_id: str) -> None:
        """
        Job ni bajarish (background).
        
        Args:
            job_id: Job ID
        """
        job = self.jobs[job_id]
        
        try:
            # Har bir task ni sequential yoki parallel bajarish
            # Sequential (oddiyroq va xavfsizroq GPU uchun)
            for task in job.tasks:
                await self._process_task(task, job.options)
            
            # Job statusini yangilash
            if job.failed_tasks == 0:
                job.status = "completed"
            elif job.completed_tasks > 0:
                job.status = "partial"
            else:
                job.status = "failed"
            
            job.completed_at = datetime.utcnow()
            
            logger.info(
                f"Job {job_id} finished: {job.completed_tasks}/{job.total_tasks} completed, "
                f"{job.failed_tasks} failed"
            )
            
        except Exception as e:
            logger.error(f"Job {job_id} error: {e}")
            job.status = "failed"
            job.completed_at = datetime.utcnow()
    
    async def _process_task(
        self,
        task: VerificationTask,
        options: Dict[str, Any]
    ) -> None:
        """
        Bitta task ni bajarish.
        
        Args:
            task: Verification task
            options: Processing options
        """
        task.status = "processing"
        task.started_at = datetime.utcnow()
        task.progress = 10
        
        try:
            if self._process_func is None:
                raise ValueError("Processor function not set")
            
            # Processing (blocking call ni async qilish)
            loop = asyncio.get_event_loop()
            
            task.progress = 30
            
            result = await loop.run_in_executor(
                self._executor,
                self._process_func,
                task.audio_path,
                task.reference_text,
                options
            )
            
            task.progress = 90
            
            # Natija saqlash
            task.result = result
            task.status = "completed"
            task.progress = 100
            task.completed_at = datetime.utcnow()
            
            logger.info(f"Task {task.task_id} completed: {task.audio_name}")
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            task.status = "failed"
            task.error = str(e)
            task.completed_at = datetime.utcnow()
    
    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """
        Job olish.
        
        Args:
            job_id: Job ID
            
        Returns:
            BatchJob yoki None
        """
        return self.jobs.get(job_id)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Job status olish.
        
        Args:
            job_id: Job ID
            
        Returns:
            Status dict yoki None
        """
        job = self.get_job(job_id)
        if job is None:
            return None
        
        # Estimated time remaining
        estimated_time = None
        if job.status == "running" and job.completed_tasks > 0:
            elapsed = (datetime.utcnow() - job.started_at).total_seconds()
            avg_time_per_task = elapsed / job.completed_tasks
            remaining_tasks = job.total_tasks - job.completed_tasks - job.failed_tasks
            estimated_time = avg_time_per_task * remaining_tasks
        
        return {
            'job_id': job.job_id,
            'status': job.status,
            'total_tasks': job.total_tasks,
            'completed_tasks': job.completed_tasks,
            'failed_tasks': job.failed_tasks,
            'progress': job.progress,
            'created_at': job.created_at.isoformat() if job.created_at else None,
            'started_at': job.started_at.isoformat() if job.started_at else None,
            'estimated_time_remaining': estimated_time,
            'tasks': [t.to_dict() for t in job.tasks]
        }
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Job natijalarini olish.
        
        Args:
            job_id: Job ID
            
        Returns:
            Results dict yoki None
        """
        job = self.get_job(job_id)
        if job is None:
            return None
        
        # Summary statistika
        results = [t.result for t in job.tasks if t.result is not None]
        
        valid_count = sum(1 for r in results if r.get('status') == 'valid')
        warning_count = sum(1 for r in results if r.get('status') == 'warning')
        reject_count = sum(1 for r in results if r.get('status') == 'reject')
        
        avg_similarity = 0
        if results:
            avg_similarity = sum(r.get('similarity', 0) for r in results) / len(results)
        
        summary = {
            'total_processed': len(results),
            'valid_count': valid_count,
            'warning_count': warning_count,
            'reject_count': reject_count,
            'failed_count': job.failed_tasks,
            'average_similarity': avg_similarity,
            'valid_percentage': valid_count / len(results) * 100 if results else 0
        }
        
        return {
            'job_id': job.job_id,
            'status': job.status,
            'summary': summary,
            'results': results
        }
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Job ni bekor qilish.
        
        Args:
            job_id: Job ID
            
        Returns:
            bool: Muvaffaqiyatli bekor qilindi yoki yo'q
        """
        job = self.get_job(job_id)
        if job is None:
            return False
        
        if job.status in ["completed", "failed", "partial"]:
            return False
        
        job.status = "failed"
        job.completed_at = datetime.utcnow()
        
        # Pending tasklarni failed qilish
        for task in job.tasks:
            if task.status == "pending":
                task.status = "failed"
                task.error = "Job cancelled"
        
        logger.info(f"Job {job_id} cancelled")
        return True
    
    def cleanup_old_jobs(self, max_age_hours: int = 24) -> int:
        """
        Eski job larni tozalash.
        
        Args:
            max_age_hours: Maksimal yosh (soatda)
            
        Returns:
            int: Tozalangan job lar soni
        """
        from datetime import timedelta
        
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        with self._lock:
            old_jobs = [
                job_id for job_id, job in self.jobs.items()
                if job.created_at < cutoff and job.status in ["completed", "failed", "partial"]
            ]
            
            for job_id in old_jobs:
                del self.jobs[job_id]
        
        if old_jobs:
            logger.info(f"Cleaned up {len(old_jobs)} old jobs")
        
        return len(old_jobs)
    
    def shutdown(self) -> None:
        """
        Executor ni to'xtatish.
        """
        self._executor.shutdown(wait=True)
        logger.info("BatchProcessor shutdown complete")


# Global instance
_batch_processor: Optional[BatchProcessor] = None


def get_batch_processor(max_workers: int = 4) -> BatchProcessor:
    """
    Global BatchProcessor instance olish.
    
    Args:
        max_workers: Worker soni
        
    Returns:
        BatchProcessor instance
    """
    global _batch_processor
    
    if _batch_processor is None:
        _batch_processor = BatchProcessor(max_workers=max_workers)
    
    return _batch_processor


# Test
if __name__ == "__main__":
    processor = BatchProcessor(max_workers=2)
    print("BatchProcessor module initialized successfully!")
