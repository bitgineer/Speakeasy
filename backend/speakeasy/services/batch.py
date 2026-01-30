"""
Batch transcription service for processing multiple audio files.

Supports:
- Job queue with SQLite persistence
- Sequential file processing with progress updates
- Per-file error handling
- WebSocket progress broadcasting
- Job cancellation
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

import aiosqlite

logger = logging.getLogger(__name__)


class BatchJobStatus(str, Enum):
    """Status of a batch transcription job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class BatchFileStatus(str, Enum):
    """Status of a file within a batch job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class BatchFile:
    """A file in a batch transcription job."""

    id: str
    job_id: str
    filename: str
    file_path: str
    status: BatchFileStatus = BatchFileStatus.PENDING
    error: Optional[str] = None
    transcription_id: Optional[str] = None  # Links to history after completion

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "job_id": self.job_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "status": self.status.value,
            "error": self.error,
            "transcription_id": self.transcription_id,
        }


@dataclass
class BatchJob:
    """A batch transcription job."""

    id: str
    status: BatchJobStatus = BatchJobStatus.PENDING
    files: list[BatchFile] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    current_file_index: int = 0

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "status": self.status.value,
            "files": [f.to_dict() for f in self.files],
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "current_file_index": self.current_file_index,
            "total_files": len(self.files),
            "completed_count": sum(1 for f in self.files if f.status == BatchFileStatus.COMPLETED),
            "failed_count": sum(1 for f in self.files if f.status == BatchFileStatus.FAILED),
            "skipped_count": sum(1 for f in self.files if f.status == BatchFileStatus.SKIPPED),
        }


class BatchService:
    """
    Service for managing batch transcription jobs.

    Features:
    - Job creation and management
    - Sequential file processing
    - Progress broadcasting via WebSocket
    - Cancellation support
    - SQLite persistence
    """

    def __init__(self, db_path: Path):
        """
        Initialize the batch service.

        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._db: Optional[aiosqlite.Connection] = None
        self._jobs: dict[str, BatchJob] = {}
        self._cancel_flags: dict[str, bool] = {}
        self._processing_locks: dict[str, asyncio.Lock] = {}

    async def initialize(self) -> None:
        """Initialize the database and create tables if needed."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row

        # Create batch_jobs table
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS batch_jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed_at DATETIME,
                current_file_index INTEGER DEFAULT 0
            )
        """)

        # Create batch_files table
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS batch_files (
                id TEXT PRIMARY KEY,
                job_id TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                error TEXT,
                transcription_id TEXT,
                FOREIGN KEY (job_id) REFERENCES batch_jobs(id) ON DELETE CASCADE
            )
        """)

        # Create index for job lookup
        await self._db.execute("""
            CREATE INDEX IF NOT EXISTS idx_batch_files_job_id ON batch_files(job_id)
        """)

        await self._db.commit()

        # Load existing jobs into memory
        await self._load_jobs_from_db()

        logger.info(f"Batch service initialized at {self.db_path}")

    async def _load_jobs_from_db(self) -> None:
        """Load jobs from database into memory."""
        if not self._db:
            return

        cursor = await self._db.execute("SELECT * FROM batch_jobs ORDER BY created_at DESC")
        rows = await cursor.fetchall()

        for row in rows:
            job = BatchJob(
                id=row["id"],
                status=BatchJobStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                completed_at=datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None,
                current_file_index=row["current_file_index"],
            )

            # Load files for this job
            file_cursor = await self._db.execute(
                "SELECT * FROM batch_files WHERE job_id = ?",
                (job.id,),
            )
            file_rows = await file_cursor.fetchall()

            job.files = [
                BatchFile(
                    id=fr["id"],
                    job_id=fr["job_id"],
                    filename=fr["filename"],
                    file_path=fr["file_path"],
                    status=BatchFileStatus(fr["status"]),
                    error=fr["error"],
                    transcription_id=fr["transcription_id"],
                )
                for fr in file_rows
            ]

            self._jobs[job.id] = job

    async def close(self) -> None:
        """Close the database connection."""
        if self._db:
            await self._db.close()
            self._db = None

    async def create_job(self, file_paths: list[str]) -> BatchJob:
        """
        Create a new batch transcription job.

        Args:
            file_paths: List of paths to audio files

        Returns:
            The created BatchJob
        """
        if not self._db:
            raise RuntimeError("Database not initialized")

        if not file_paths:
            raise ValueError("At least one file path is required")

        job_id = str(uuid.uuid4())
        job = BatchJob(id=job_id)

        # Create files for the job
        for file_path in file_paths:
            file_id = str(uuid.uuid4())
            filename = Path(file_path).name
            batch_file = BatchFile(
                id=file_id,
                job_id=job_id,
                filename=filename,
                file_path=file_path,
            )
            job.files.append(batch_file)

        # Persist to database
        await self._db.execute(
            """
            INSERT INTO batch_jobs (id, status, created_at, current_file_index)
            VALUES (?, ?, ?, ?)
            """,
            (job.id, job.status.value, job.created_at, job.current_file_index),
        )

        for bf in job.files:
            await self._db.execute(
                """
                INSERT INTO batch_files (id, job_id, filename, file_path, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (bf.id, bf.job_id, bf.filename, bf.file_path, bf.status.value),
            )

        await self._db.commit()

        self._jobs[job_id] = job
        self._cancel_flags[job_id] = False

        logger.info(f"Created batch job {job_id} with {len(file_paths)} files")

        return job

    async def get_job(self, job_id: str) -> Optional[BatchJob]:
        """
        Get a job by ID.

        Args:
            job_id: The job ID

        Returns:
            The BatchJob or None if not found
        """
        return self._jobs.get(job_id)

    async def list_jobs(self, limit: int = 50) -> list[BatchJob]:
        """
        List all jobs.

        Args:
            limit: Maximum number of jobs to return

        Returns:
            List of BatchJob objects
        """
        jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True,
        )
        return jobs[:limit]

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a job.

        Args:
            job_id: The job ID to cancel

        Returns:
            True if cancelled, False if not found or already completed
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        if job.status in (
            BatchJobStatus.COMPLETED,
            BatchJobStatus.CANCELLED,
            BatchJobStatus.FAILED,
        ):
            return False

        # Set cancel flag
        self._cancel_flags[job_id] = True

        # Mark remaining pending files as skipped
        for bf in job.files:
            if bf.status == BatchFileStatus.PENDING:
                bf.status = BatchFileStatus.SKIPPED
                await self._update_file_status(bf)

        job.status = BatchJobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        await self._update_job_status(job)

        logger.info(f"Cancelled batch job {job_id}")

        return True

    async def _update_job_status(self, job: BatchJob) -> None:
        """Update job status in database."""
        if not self._db:
            return

        await self._db.execute(
            """
            UPDATE batch_jobs 
            SET status = ?, completed_at = ?, current_file_index = ?
            WHERE id = ?
            """,
            (job.status.value, job.completed_at, job.current_file_index, job.id),
        )
        await self._db.commit()

    async def _update_file_status(self, bf: BatchFile) -> None:
        """Update file status in database."""
        if not self._db:
            return

        await self._db.execute(
            """
            UPDATE batch_files 
            SET status = ?, error = ?, transcription_id = ?
            WHERE id = ?
            """,
            (bf.status.value, bf.error, bf.transcription_id, bf.id),
        )
        await self._db.commit()

    async def process_job(
        self,
        job_id: str,
        transcriber: Any,
        history_service: Any,
        broadcast_fn: Callable,
        language: str = "auto",
    ) -> None:
        """
        Process a batch job by transcribing all files.

        Args:
            job_id: The job ID to process
            transcriber: TranscriberService instance
            history_service: HistoryService instance
            broadcast_fn: Async function for WebSocket broadcasting
            language: Language for transcription
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        if job.status != BatchJobStatus.PENDING:
            raise ValueError(f"Job {job_id} is not pending")

        # Acquire lock to prevent concurrent processing
        if job_id not in self._processing_locks:
            self._processing_locks[job_id] = asyncio.Lock()

        async with self._processing_locks[job_id]:
            job.status = BatchJobStatus.PROCESSING
            await self._update_job_status(job)

            # Broadcast initial progress
            await broadcast_fn(
                "batch_progress",
                {
                    "job_id": job_id,
                    "status": job.status.value,
                    "current_file": None,
                    "current_index": 0,
                    "total_files": len(job.files),
                    "completed": 0,
                    "failed": 0,
                },
            )

            completed_count = 0
            failed_count = 0

            for index, bf in enumerate(job.files):
                # Check for cancellation
                if self._cancel_flags.get(job_id, False):
                    logger.info(f"Job {job_id} cancelled at file {index}")
                    break

                job.current_file_index = index
                bf.status = BatchFileStatus.PROCESSING
                await self._update_file_status(bf)

                # Broadcast file start
                await broadcast_fn(
                    "batch_progress",
                    {
                        "job_id": job_id,
                        "status": job.status.value,
                        "current_file": bf.filename,
                        "current_index": index,
                        "total_files": len(job.files),
                        "completed": completed_count,
                        "failed": failed_count,
                    },
                )

                # Retry logic: 1 retry allowed
                max_retries = 1
                last_error = None

                for attempt in range(max_retries + 1):
                    try:
                        # Transcribe the file
                        result = await asyncio.to_thread(
                            transcriber.transcribe_file,
                            bf.file_path,
                            language,
                        )

                        # Save to history
                        record = await history_service.add(
                            text=result.text,
                            duration_ms=result.duration_ms,
                            model_used=result.model_used,
                            language=result.language,
                        )

                        bf.status = BatchFileStatus.COMPLETED
                        bf.transcription_id = record.id
                        bf.error = None  # Clear any previous error from retry
                        completed_count += 1

                        logger.debug(f"Completed transcription for {bf.filename}")
                        break  # Success, exit retry loop

                    except Exception as e:
                        # Check for CUDA/GPU errors - Immediate failure & reload
                        error_msg = str(e)
                        if "CUDA" in error_msg or "illegal memory access" in error_msg:
                            logger.critical(
                                f"CUDA Error encountered on {bf.filename}. Attempting soft restart."
                            )

                            # Reload model
                            try:
                                if hasattr(transcriber, "reload_model"):
                                    await asyncio.to_thread(transcriber.reload_model)
                                else:
                                    logger.error("Transcriber missing reload_model method")
                            except Exception as reload_err:
                                logger.critical(f"Failed to reload model: {reload_err}")

                            bf.status = BatchFileStatus.FAILED
                            bf.error = "GPU Error - Model Reloaded"
                            failed_count += 1
                            break

                        last_error = e
                        if attempt < max_retries:
                            logger.warning(
                                f"Transcription failed for {bf.filename} (attempt {attempt + 1}/{max_retries + 1}), retrying: {e}"
                            )
                            await asyncio.sleep(1)  # Brief pause before retry
                            continue
                        else:
                            # Final failure after retries
                            logger.error(
                                f"Failed to transcribe {bf.filename} after {max_retries + 1} attempts: {e}"
                            )
                            bf.status = BatchFileStatus.FAILED
                            bf.error = str(e)
                            failed_count += 1

                await self._update_file_status(bf)

                # Broadcast file completion
                await broadcast_fn(
                    "batch_progress",
                    {
                        "job_id": job_id,
                        "status": job.status.value,
                        "current_file": bf.filename,
                        "current_index": index + 1,
                        "total_files": len(job.files),
                        "completed": completed_count,
                        "failed": failed_count,
                        "file_status": bf.status.value,
                    },
                )

            # Finalize job status
            if self._cancel_flags.get(job_id, False):
                job.status = BatchJobStatus.CANCELLED
            elif failed_count == len(job.files):
                job.status = BatchJobStatus.FAILED
            else:
                job.status = BatchJobStatus.COMPLETED

            job.completed_at = datetime.now(timezone.utc)
            await self._update_job_status(job)

            # Final broadcast
            await broadcast_fn(
                "batch_progress",
                {
                    "job_id": job_id,
                    "status": job.status.value,
                    "current_file": None,
                    "current_index": len(job.files),
                    "total_files": len(job.files),
                    "completed": completed_count,
                    "failed": failed_count,
                },
            )

            logger.info(
                f"Batch job {job_id} completed: {completed_count} succeeded, {failed_count} failed"
            )

    async def retry_failed(self, job_id: str, file_ids: Optional[list[str]] = None) -> BatchJob:
        """
        Retry failed files in a job.

        Args:
            job_id: The job ID
            file_ids: Specific file IDs to retry, or None to retry all failed

        Returns:
            The updated BatchJob
        """
        job = self._jobs.get(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        # Reset specified or all failed files to pending
        for bf in job.files:
            if bf.status == BatchFileStatus.FAILED:
                if file_ids is None or bf.id in file_ids:
                    bf.status = BatchFileStatus.PENDING
                    bf.error = None
                    await self._update_file_status(bf)

        # Reset job status
        job.status = BatchJobStatus.PENDING
        job.completed_at = None
        job.current_file_index = 0
        self._cancel_flags[job_id] = False
        await self._update_job_status(job)

        logger.info(f"Reset job {job_id} for retry")

        return job

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete a job and its files.

        Args:
            job_id: The job ID to delete

        Returns:
            True if deleted, False if not found
        """
        if job_id not in self._jobs:
            return False

        if not self._db:
            return False

        # Delete from database (cascade deletes files)
        await self._db.execute("DELETE FROM batch_files WHERE job_id = ?", (job_id,))
        await self._db.execute("DELETE FROM batch_jobs WHERE id = ?", (job_id,))
        await self._db.commit()

        # Remove from memory
        del self._jobs[job_id]
        self._cancel_flags.pop(job_id, None)
        self._processing_locks.pop(job_id, None)

        logger.info(f"Deleted batch job {job_id}")

        return True
