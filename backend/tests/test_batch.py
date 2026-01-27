"""
Comprehensive tests for the BatchService.

Tests cover:
- Job creation and management
- Job retrieval and listing
- Job cancellation
- Job status transitions
- BatchFile and BatchJob dataclasses
- Edge cases: empty lists, single items, many items
"""

from datetime import datetime
from pathlib import Path

import pytest

from speakeasy.services.batch import (
    BatchFile,
    BatchFileStatus,
    BatchJob,
    BatchJobStatus,
    BatchService,
)


@pytest.fixture
async def batch_service(tmp_path: Path):
    """
    Provide an initialized BatchService with automatic cleanup.

    Uses tmp_path for test isolation - each test gets a fresh database.
    """
    db_path = tmp_path / "test_batch.db"
    service = BatchService(db_path)
    await service.initialize()
    yield service
    await service.close()


@pytest.fixture
def sample_file_paths(tmp_path: Path) -> list[str]:
    """Provide sample file paths for testing."""
    paths = []
    for i in range(3):
        file_path = tmp_path / f"audio_{i}.wav"
        file_path.touch()  # Create empty file
        paths.append(str(file_path))
    return paths


@pytest.fixture
def single_file_path(tmp_path: Path) -> list[str]:
    """Provide a single file path for testing."""
    file_path = tmp_path / "single_audio.wav"
    file_path.touch()
    return [str(file_path)]


@pytest.fixture
def many_file_paths(tmp_path: Path) -> list[str]:
    """Provide many file paths for edge case testing."""
    paths = []
    for i in range(20):
        file_path = tmp_path / f"audio_{i:03d}.wav"
        file_path.touch()
        paths.append(str(file_path))
    return paths


class TestCreateJob:
    """Tests for job creation."""

    async def test_create_job(self, batch_service: BatchService, sample_file_paths: list[str]):
        """Create job with multiple files returns valid BatchJob."""
        job = await batch_service.create_job(sample_file_paths)

        assert job.id is not None
        assert job.status == BatchJobStatus.PENDING
        assert len(job.files) == 3
        assert job.current_file_index == 0
        assert isinstance(job.created_at, datetime)
        assert job.completed_at is None

    async def test_create_job_single_file(
        self, batch_service: BatchService, single_file_path: list[str]
    ):
        """Create job with single file works correctly."""
        job = await batch_service.create_job(single_file_path)

        assert len(job.files) == 1
        assert job.files[0].filename == "single_audio.wav"
        assert job.files[0].status == BatchFileStatus.PENDING

    async def test_create_job_many_files(
        self, batch_service: BatchService, many_file_paths: list[str]
    ):
        """Create job with many files handles large batches."""
        job = await batch_service.create_job(many_file_paths)

        assert len(job.files) == 20
        # All files should be pending
        assert all(f.status == BatchFileStatus.PENDING for f in job.files)

    async def test_create_job_empty_list_raises(self, batch_service: BatchService):
        """Create job with empty list raises ValueError."""
        with pytest.raises(ValueError, match="At least one file path is required"):
            await batch_service.create_job([])

    async def test_create_job_generates_unique_ids(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """Each job and file gets a unique UUID."""
        job1 = await batch_service.create_job(sample_file_paths)
        job2 = await batch_service.create_job(sample_file_paths)

        # Job IDs are unique
        assert job1.id != job2.id

        # File IDs are unique within a job
        file_ids = [f.id for f in job1.files]
        assert len(file_ids) == len(set(file_ids))

        # File IDs are unique across jobs
        all_file_ids = [f.id for f in job1.files] + [f.id for f in job2.files]
        assert len(all_file_ids) == len(set(all_file_ids))

    async def test_create_job_extracts_filename(self, batch_service: BatchService, tmp_path: Path):
        """File paths are parsed to extract filename."""
        nested_path = tmp_path / "nested" / "dir" / "my_audio.mp3"
        nested_path.parent.mkdir(parents=True)
        nested_path.touch()

        job = await batch_service.create_job([str(nested_path)])

        assert job.files[0].filename == "my_audio.mp3"
        assert job.files[0].file_path == str(nested_path)


class TestGetJob:
    """Tests for job retrieval."""

    async def test_get_job(self, batch_service: BatchService, sample_file_paths: list[str]):
        """Get existing job by ID returns correct job."""
        created = await batch_service.create_job(sample_file_paths)

        retrieved = await batch_service.get_job(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert len(retrieved.files) == 3

    async def test_get_job_nonexistent(self, batch_service: BatchService):
        """Get nonexistent job returns None."""
        result = await batch_service.get_job("nonexistent-job-id")

        assert result is None


class TestListJobs:
    """Tests for listing jobs."""

    async def test_list_jobs(self, batch_service: BatchService, sample_file_paths: list[str]):
        """List returns all created jobs."""
        await batch_service.create_job(sample_file_paths)
        await batch_service.create_job(sample_file_paths)
        await batch_service.create_job(sample_file_paths)

        jobs = await batch_service.list_jobs()

        assert len(jobs) == 3

    async def test_list_jobs_empty(self, batch_service: BatchService):
        """List on empty service returns empty list."""
        jobs = await batch_service.list_jobs()

        assert jobs == []

    async def test_list_jobs_limit(self, batch_service: BatchService, sample_file_paths: list[str]):
        """List respects limit parameter."""
        for _ in range(5):
            await batch_service.create_job(sample_file_paths)

        jobs = await batch_service.list_jobs(limit=3)

        assert len(jobs) == 3

    async def test_list_jobs_ordering(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """List returns jobs in reverse chronological order (newest first)."""
        job1 = await batch_service.create_job(sample_file_paths)
        job2 = await batch_service.create_job(sample_file_paths)
        job3 = await batch_service.create_job(sample_file_paths)

        jobs = await batch_service.list_jobs()

        # Newest first
        assert jobs[0].id == job3.id
        assert jobs[1].id == job2.id
        assert jobs[2].id == job1.id


class TestCancelJob:
    """Tests for job cancellation."""

    async def test_cancel_job(self, batch_service: BatchService, sample_file_paths: list[str]):
        """Cancel pending job returns True and updates status."""
        job = await batch_service.create_job(sample_file_paths)

        result = await batch_service.cancel_job(job.id)

        assert result is True

        # Verify job status updated
        updated = await batch_service.get_job(job.id)
        assert updated.status == BatchJobStatus.CANCELLED
        assert updated.completed_at is not None

        # Verify pending files marked as skipped
        assert all(f.status == BatchFileStatus.SKIPPED for f in updated.files)

    async def test_cancel_job_nonexistent(self, batch_service: BatchService):
        """Cancel nonexistent job returns False."""
        result = await batch_service.cancel_job("nonexistent-job-id")

        assert result is False

    async def test_cancel_job_already_completed(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """Cancel already completed job returns False."""
        job = await batch_service.create_job(sample_file_paths)

        # Manually set to completed
        job.status = BatchJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        await batch_service._update_job_status(job)

        result = await batch_service.cancel_job(job.id)

        assert result is False

    async def test_cancel_job_already_cancelled(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """Cancel already cancelled job returns False."""
        job = await batch_service.create_job(sample_file_paths)

        # Cancel once
        await batch_service.cancel_job(job.id)

        # Try to cancel again
        result = await batch_service.cancel_job(job.id)

        assert result is False


class TestJobStatusTransitions:
    """Tests for job status transitions."""

    async def test_job_status_transitions(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """Job status transitions follow expected flow."""
        job = await batch_service.create_job(sample_file_paths)

        # Initial state
        assert job.status == BatchJobStatus.PENDING

        # Simulate processing start
        job.status = BatchJobStatus.PROCESSING
        await batch_service._update_job_status(job)

        retrieved = await batch_service.get_job(job.id)
        assert retrieved.status == BatchJobStatus.PROCESSING

        # Simulate completion
        job.status = BatchJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        await batch_service._update_job_status(job)

        retrieved = await batch_service.get_job(job.id)
        assert retrieved.status == BatchJobStatus.COMPLETED
        assert retrieved.completed_at is not None

    async def test_file_status_transitions(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """File status transitions follow expected flow."""
        job = await batch_service.create_job(sample_file_paths)
        bf = job.files[0]

        # Initial state
        assert bf.status == BatchFileStatus.PENDING

        # Simulate processing
        bf.status = BatchFileStatus.PROCESSING
        await batch_service._update_file_status(bf)

        # Simulate completion
        bf.status = BatchFileStatus.COMPLETED
        bf.transcription_id = "transcription-uuid-123"
        await batch_service._update_file_status(bf)

        # Verify persisted
        retrieved = await batch_service.get_job(job.id)
        assert retrieved.files[0].status == BatchFileStatus.COMPLETED
        assert retrieved.files[0].transcription_id == "transcription-uuid-123"

    async def test_file_status_failed(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """File can transition to failed status with error message."""
        job = await batch_service.create_job(sample_file_paths)
        bf = job.files[0]

        bf.status = BatchFileStatus.FAILED
        bf.error = "Audio file corrupted"
        await batch_service._update_file_status(bf)

        retrieved = await batch_service.get_job(job.id)
        assert retrieved.files[0].status == BatchFileStatus.FAILED
        assert retrieved.files[0].error == "Audio file corrupted"


class TestBatchFileDataclass:
    """Tests for BatchFile dataclass."""

    def test_batch_file_dataclass(self):
        """BatchFile dataclass has correct fields and defaults."""
        bf = BatchFile(
            id="file-uuid-001",
            job_id="job-uuid-001",
            filename="test.wav",
            file_path="/path/to/test.wav",
        )

        assert bf.id == "file-uuid-001"
        assert bf.job_id == "job-uuid-001"
        assert bf.filename == "test.wav"
        assert bf.file_path == "/path/to/test.wav"
        assert bf.status == BatchFileStatus.PENDING
        assert bf.error is None
        assert bf.transcription_id is None

    def test_batch_file_to_dict(self):
        """BatchFile.to_dict() produces correct JSON-serializable dict."""
        bf = BatchFile(
            id="file-uuid-002",
            job_id="job-uuid-002",
            filename="audio.mp3",
            file_path="/audio/audio.mp3",
            status=BatchFileStatus.COMPLETED,
            error=None,
            transcription_id="trans-uuid-001",
        )

        result = bf.to_dict()

        assert result == {
            "id": "file-uuid-002",
            "job_id": "job-uuid-002",
            "filename": "audio.mp3",
            "file_path": "/audio/audio.mp3",
            "status": "completed",
            "error": None,
            "transcription_id": "trans-uuid-001",
        }

    def test_batch_file_to_dict_with_error(self):
        """BatchFile.to_dict() includes error when present."""
        bf = BatchFile(
            id="file-uuid-003",
            job_id="job-uuid-003",
            filename="bad.wav",
            file_path="/bad.wav",
            status=BatchFileStatus.FAILED,
            error="File not found",
        )

        result = bf.to_dict()

        assert result["status"] == "failed"
        assert result["error"] == "File not found"


class TestBatchJobDataclass:
    """Tests for BatchJob dataclass."""

    def test_batch_job_dataclass(self):
        """BatchJob dataclass has correct fields and defaults."""
        job = BatchJob(id="job-uuid-001")

        assert job.id == "job-uuid-001"
        assert job.status == BatchJobStatus.PENDING
        assert job.files == []
        assert isinstance(job.created_at, datetime)
        assert job.completed_at is None
        assert job.current_file_index == 0

    def test_batch_job_to_dict(self):
        """BatchJob.to_dict() produces correct JSON-serializable dict."""
        created = datetime(2024, 1, 15, 10, 30, 0)
        completed = datetime(2024, 1, 15, 10, 35, 0)

        job = BatchJob(
            id="job-uuid-002",
            status=BatchJobStatus.COMPLETED,
            files=[
                BatchFile(
                    id="f1",
                    job_id="job-uuid-002",
                    filename="a.wav",
                    file_path="/a.wav",
                    status=BatchFileStatus.COMPLETED,
                ),
                BatchFile(
                    id="f2",
                    job_id="job-uuid-002",
                    filename="b.wav",
                    file_path="/b.wav",
                    status=BatchFileStatus.FAILED,
                    error="Error",
                ),
                BatchFile(
                    id="f3",
                    job_id="job-uuid-002",
                    filename="c.wav",
                    file_path="/c.wav",
                    status=BatchFileStatus.SKIPPED,
                ),
            ],
            created_at=created,
            completed_at=completed,
            current_file_index=3,
        )

        result = job.to_dict()

        assert result["id"] == "job-uuid-002"
        assert result["status"] == "completed"
        assert result["created_at"] == "2024-01-15T10:30:00"
        assert result["completed_at"] == "2024-01-15T10:35:00"
        assert result["current_file_index"] == 3
        assert result["total_files"] == 3
        assert result["completed_count"] == 1
        assert result["failed_count"] == 1
        assert result["skipped_count"] == 1
        assert len(result["files"]) == 3

    def test_batch_job_to_dict_no_completed_at(self):
        """BatchJob.to_dict() handles None completed_at."""
        job = BatchJob(id="job-uuid-003")

        result = job.to_dict()

        assert result["completed_at"] is None


class TestDeleteJob:
    """Tests for job deletion."""

    async def test_delete_job(self, batch_service: BatchService, sample_file_paths: list[str]):
        """Delete existing job returns True and removes from storage."""
        job = await batch_service.create_job(sample_file_paths)

        result = await batch_service.delete_job(job.id)

        assert result is True

        # Verify job is gone
        retrieved = await batch_service.get_job(job.id)
        assert retrieved is None

    async def test_delete_job_nonexistent(self, batch_service: BatchService):
        """Delete nonexistent job returns False."""
        result = await batch_service.delete_job("nonexistent-job-id")

        assert result is False


class TestRetryFailed:
    """Tests for retrying failed files."""

    async def test_retry_failed(self, batch_service: BatchService, sample_file_paths: list[str]):
        """Retry resets failed files to pending."""
        job = await batch_service.create_job(sample_file_paths)

        # Mark some files as failed
        job.files[0].status = BatchFileStatus.COMPLETED
        job.files[1].status = BatchFileStatus.FAILED
        job.files[1].error = "Some error"
        job.files[2].status = BatchFileStatus.FAILED
        job.files[2].error = "Another error"
        job.status = BatchJobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

        for bf in job.files:
            await batch_service._update_file_status(bf)
        await batch_service._update_job_status(job)

        # Retry all failed
        updated = await batch_service.retry_failed(job.id)

        assert updated.status == BatchJobStatus.PENDING
        assert updated.completed_at is None
        assert updated.files[0].status == BatchFileStatus.COMPLETED  # Unchanged
        assert updated.files[1].status == BatchFileStatus.PENDING  # Reset
        assert updated.files[1].error is None
        assert updated.files[2].status == BatchFileStatus.PENDING  # Reset
        assert updated.files[2].error is None

    async def test_retry_failed_specific_files(
        self, batch_service: BatchService, sample_file_paths: list[str]
    ):
        """Retry specific failed files by ID."""
        job = await batch_service.create_job(sample_file_paths)

        # Mark all as failed
        for bf in job.files:
            bf.status = BatchFileStatus.FAILED
            bf.error = "Error"
            await batch_service._update_file_status(bf)

        # Retry only first file
        updated = await batch_service.retry_failed(job.id, file_ids=[job.files[0].id])

        assert updated.files[0].status == BatchFileStatus.PENDING
        assert updated.files[1].status == BatchFileStatus.FAILED  # Not retried
        assert updated.files[2].status == BatchFileStatus.FAILED  # Not retried


class TestPersistence:
    """Tests for database persistence."""

    async def test_jobs_persist_across_service_restart(self, tmp_path: Path):
        """Jobs are persisted and loaded on service restart."""
        db_path = tmp_path / "persist_test.db"

        # Create service and add job
        service1 = BatchService(db_path)
        await service1.initialize()

        file_path = tmp_path / "test.wav"
        file_path.touch()
        job = await service1.create_job([str(file_path)])
        job_id = job.id

        await service1.close()

        # Create new service instance
        service2 = BatchService(db_path)
        await service2.initialize()

        # Job should be loaded
        retrieved = await service2.get_job(job_id)
        assert retrieved is not None
        assert retrieved.id == job_id
        assert len(retrieved.files) == 1

        await service2.close()
