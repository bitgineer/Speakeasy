"""
Test for BatchService.get_job
Comprehensive test suite for retrieving batch jobs.
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
async def initialized_service_with_job():
    """Create and initialize a BatchService with a job."""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_batch.db"
    service = BatchService(db_path=db_path)
    await service.initialize()

    job = await service.create_job(["/path/to/audio.wav", "/path/to/audio2.wav"])

    yield service, job

    # Cleanup
    await service.close()
    if db_path.exists():
        db_path.unlink()
    if temp_dir:
        os.rmdir(temp_dir)


class TestBatchServiceGetJob:
    """Tests for BatchService.get_job"""

    @pytest.mark.asyncio
    async def test_get_existing_job(self, initialized_service_with_job):
        """Test retrieving an existing job."""
        service, original = await initialized_service_with_job

        retrieved = await service.get_job(original.id)

        assert retrieved is not None
        assert retrieved.id == original.id
        assert len(retrieved.files) == 2

    @pytest.mark.asyncio
    async def test_get_nonexistent_job(self, initialized_service_with_job):
        """Test retrieving a job that doesn't exist."""
        service, _ = await initialized_service_with_job

        result = await service.get_job("non-existent-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_batchjob(self, initialized_service_with_job):
        """Test that get returns a BatchJob instance."""
        service, original = await initialized_service_with_job

        retrieved = await service.get_job(original.id)

        assert isinstance(retrieved, BatchJob)

    @pytest.mark.asyncio
    async def test_get_preserves_file_data(self, initialized_service_with_job):
        """Test that get preserves all file data."""
        service, original = await initialized_service_with_job

        retrieved = await service.get_job(original.id)

        assert len(retrieved.files) == len(original.files)
        for i, file in enumerate(retrieved.files):
            assert file.id == original.files[i].id
            assert file.filename == original.files[i].filename
            assert file.file_path == original.files[i].file_path
            assert file.status == original.files[i].status

    @pytest.mark.asyncio
    async def test_get_preserves_job_status(self, initialized_service_with_job):
        """Test that get preserves job status."""
        service, original = await initialized_service_with_job

        retrieved = await service.get_job(original.id)

        assert retrieved.status == original.status

    @pytest.mark.asyncio
    async def test_get_with_empty_id(self, initialized_service_with_job):
        """Test retrieving with an empty ID."""
        service, _ = await initialized_service_with_job

        result = await service.get_job("")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_multiple_jobs(self):
        """Test getting multiple different jobs."""
        temp_dir = tempfile.mkdtemp()
        db_path = Path(temp_dir) / "test_batch.db"
        service = BatchService(db_path=db_path)
        await service.initialize()

        try:
            # Create multiple jobs
            jobs = []
            for i in range(5):
                job = await service.create_job([f"/file{i}.wav"])
                jobs.append(job)

            # Get each one
            for i, original in enumerate(jobs):
                retrieved = await service.get_job(original.id)
                assert retrieved is not None
                assert retrieved.id == original.id
        finally:
            await service.close()
            if db_path.exists():
                db_path.unlink()
            if temp_dir:
                os.rmdir(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
