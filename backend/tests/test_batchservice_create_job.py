"""
Test for BatchService.create_job
Comprehensive test suite for creating batch jobs.
"""

import pytest
import asyncio
from pathlib import Path
import sys
import tempfile
import os

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.services.batch import (
    BatchService,
    BatchJob,
    BatchFile,
    BatchJobStatus,
    BatchFileStatus,
)


@pytest.fixture
async def initialized_service():
    """Create and initialize a BatchService."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_batch.db"
    service = BatchService(db_path=db_path)
    await service.initialize()

    yield service

    # Cleanup
    await service.close()
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestBatchServiceCreateJob:
    """Tests for BatchService.create_job"""

    @pytest.mark.asyncio
    async def test_create_job_single_file(self, initialized_service):
        """Test creating a job with a single file."""
        service = await initialized_service

        file_paths = ["/path/to/audio.wav"]
        job = await service.create_job(file_paths)

        assert isinstance(job, BatchJob)
        assert job.id is not None
        assert len(job.files) == 1
        assert job.status == BatchJobStatus.PENDING
        assert job.files[0].filename == "audio.wav"

    @pytest.mark.asyncio
    async def test_create_job_multiple_files(self, initialized_service):
        """Test creating a job with multiple files."""
        service = await initialized_service

        file_paths = [
            "/path/to/audio1.wav",
            "/path/to/audio2.wav",
            "/path/to/audio3.wav",
        ]
        job = await service.create_job(file_paths)

        assert len(job.files) == 3
        assert job.files[0].filename == "audio1.wav"
        assert job.files[1].filename == "audio2.wav"
        assert job.files[2].filename == "audio3.wav"

    @pytest.mark.asyncio
    async def test_create_job_generates_unique_ids(self, initialized_service):
        """Test that creating multiple jobs generates unique IDs."""
        service = await initialized_service

        job1 = await service.create_job(["/file1.wav"])
        job2 = await service.create_job(["/file2.wav"])

        assert job1.id != job2.id

    @pytest.mark.asyncio
    async def test_create_job_empty_list_raises_error(self, initialized_service):
        """Test that creating a job with empty file list raises error."""
        service = await initialized_service

        with pytest.raises(ValueError, match="At least one file path is required"):
            await service.create_job([])

    @pytest.mark.asyncio
    async def test_create_job_persists_to_database(self, initialized_service):
        """Test that created job is persisted to database."""
        service = await initialized_service

        job = await service.create_job(["/audio.wav"])

        # Retrieve from database
        retrieved = await service.get_job(job.id)

        assert retrieved is not None
        assert retrieved.id == job.id

    @pytest.mark.asyncio
    async def test_create_job_sets_pending_status(self, initialized_service):
        """Test that created job has PENDING status."""
        service = await initialized_service

        job = await service.create_job(["/audio.wav"])

        assert job.status == BatchJobStatus.PENDING
        for file in job.files:
            assert file.status == BatchFileStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_job_handles_various_paths(self, initialized_service):
        """Test creating jobs with various path formats."""
        service = await initialized_service

        paths = [
            "/absolute/path/file.wav",
            "relative/path/file.wav",
            "./current/file.wav",
            "~/home/file.wav",
            "C:\\Windows\\file.wav",
        ]

        job = await service.create_job(paths)

        assert len(job.files) == 5

    @pytest.mark.asyncio
    async def test_create_job_fails_when_not_initialized(self, temp_db_path):
        """Test that create_job fails when database is not initialized."""
        service = BatchService(db_path=temp_db_path)

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.create_job(["/file.wav"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
