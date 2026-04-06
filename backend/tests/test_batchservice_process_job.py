"""
Test for BatchService.process_job
Comprehensive test suite for processing batch jobs.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
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


class TestBatchServiceProcessJob:
    """Tests for BatchService.process_job"""

    @pytest.mark.asyncio
    async def test_process_job_not_found(self, initialized_service_with_job):
        """Test processing a non-existent job raises error."""
        service, _ = await initialized_service_with_job

        mock_transcriber = Mock()
        mock_history = Mock()
        mock_broadcast = AsyncMock()

        with pytest.raises(ValueError, match="Job not found"):
            await service.process_job(
                "non-existent-id",
                mock_transcriber,
                mock_history,
                mock_broadcast,
            )

    @pytest.mark.asyncio
    async def test_process_job_already_processing(self, initialized_service_with_job):
        """Test processing a job that's not pending raises error."""
        service, job = await initialized_service_with_job

        # Change status to processing
        job.status = BatchJobStatus.PROCESSING

        mock_transcriber = Mock()
        mock_history = Mock()
        mock_broadcast = AsyncMock()

        with pytest.raises(ValueError, match="is not pending"):
            await service.process_job(
                job.id,
                mock_transcriber,
                mock_history,
                mock_broadcast,
            )

    @pytest.mark.asyncio
    async def test_process_job_broadcasts_progress(self, initialized_service_with_job):
        """Test that process_job broadcasts progress updates."""
        service, job = await initialized_service_with_job

        mock_transcriber = Mock()
        mock_history = Mock()
        mock_broadcast = AsyncMock()

        # Mock transcribe_file to return immediately
        mock_result = Mock()
        mock_result.text = "Transcribed text"
        mock_result.duration_ms = 5000
        mock_result.model_used = "test-model"
        mock_result.language = "en"
        mock_transcriber.transcribe_file.return_value = mock_result

        mock_history.add = AsyncMock(return_value=Mock(id="record-id"))

        await service.process_job(
            job.id,
            mock_transcriber,
            mock_history,
            mock_broadcast,
            language="en",
        )

        # Should have broadcasted progress multiple times
        assert mock_broadcast.call_count >= 3  # Initial, during, final

    @pytest.mark.asyncio
    async def test_process_job_updates_status(self, initialized_service_with_job):
        """Test that process_job updates job status."""
        service, job = await initialized_service_with_job

        mock_transcriber = Mock()
        mock_history = Mock()
        mock_broadcast = AsyncMock()

        mock_result = Mock()
        mock_result.text = "Transcribed text"
        mock_result.duration_ms = 5000
        mock_result.model_used = "test-model"
        mock_result.language = "en"
        mock_transcriber.transcribe_file.return_value = mock_result

        mock_history.add = AsyncMock(return_value=Mock(id="record-id"))

        await service.process_job(
            job.id,
            mock_transcriber,
            mock_history,
            mock_broadcast,
        )

        # Check status was updated
        assert job.status == BatchJobStatus.COMPLETED

    @pytest.mark.asyncio
    async def test_process_job_handles_transcription_error(self, initialized_service_with_job):
        """Test that process_job handles transcription errors."""
        service, job = await initialized_service_with_job

        mock_transcriber = Mock()
        mock_history = Mock()
        mock_broadcast = AsyncMock()

        # Make transcribe_file fail
        mock_transcriber.transcribe_file.side_effect = Exception("Transcription failed")

        await service.process_job(
            job.id,
            mock_transcriber,
            mock_history,
            mock_broadcast,
        )

        # Check that files have failed status
        for file in job.files:
            assert file.status == BatchJobStatus.FAILED


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
