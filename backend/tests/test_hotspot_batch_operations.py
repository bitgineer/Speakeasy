"""
Hotspot tests for batch.py create_job() method - CRITICAL (21 callers)

Tests the BatchService.create_job() method which creates batch transcription jobs.
This is critical for batch processing workflows - failures here block all batch operations.

Blast Radius:
- 21 direct callers
- Used in all batch transcription workflows
- Affects file processing, job tracking, and result aggregation
- Database operations with potential for data loss

Coverage Targets:
- Basic job creation
- File validation
- Database persistence
- Error handling
- Edge cases (empty files, invalid paths, large batches)
- Concurrent job creation
"""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from speakeasy.services.batch import BatchFile, BatchJob, BatchService, JobStatus


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_db_path():
    """Create temporary database file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_batch.db"
        yield db_path


@pytest.fixture
async def batch_service(temp_db_path):
    """Create batch service with temp database."""
    service = BatchService(db_path=str(temp_db_path))
    await service.initialize()
    yield service
    await service.close()


@pytest.fixture
def sample_audio_files():
    """Create sample audio files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        # Create dummy audio files
        files = []
        for i in range(5):
            file_path = tmpdir / f"test_audio_{i}.wav"
            file_path.write_bytes(b"dummy audio content")
            files.append(str(file_path))
        yield files


# =============================================================================
# Basic Create Job Tests
# =============================================================================


class TestCreateJobBasic:
    """Basic create_job() functionality tests."""

    @pytest.mark.asyncio
    async def test_create_job_single_file(self, batch_service, sample_audio_files):
        """Create job with single file succeeds."""
        job = await batch_service.create_job([sample_audio_files[0]])

        assert isinstance(job, BatchJob)
        assert job.id is not None
        assert len(job.files) == 1
        assert job.files[0].file_path == sample_audio_files[0]
        assert job.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_job_multiple_files(self, batch_service, sample_audio_files):
        """Create job with multiple files succeeds."""
        job = await batch_service.create_job(sample_audio_files)

        assert len(job.files) == 5
        assert all(isinstance(f, BatchFile) for f in job.files)
        assert all(f.status == JobStatus.PENDING for f in job.files)

    @pytest.mark.asyncio
    async def test_create_job_generates_unique_id(self, batch_service, sample_audio_files):
        """Each job gets unique ID."""
        job1 = await batch_service.create_job([sample_audio_files[0]])
        job2 = await batch_service.create_job([sample_audio_files[1]])

        assert job1.id != job2.id

    @pytest.mark.asyncio
    async def test_create_job_file_ids_unique(self, batch_service, sample_audio_files):
        """Each file in job gets unique ID."""
        job = await batch_service.create_job(sample_audio_files)

        file_ids = [f.id for f in job.files]
        assert len(set(file_ids)) == len(file_ids)

    @pytest.mark.asyncio
    async def test_create_job_extracts_filename(self, batch_service, sample_audio_files):
        """Filename extracted from path."""
        job = await batch_service.create_job([sample_audio_files[0]])

        expected_filename = Path(sample_audio_files[0]).name
        assert job.files[0].filename == expected_filename

    @pytest.mark.asyncio
    async def test_create_job_stores_full_path(self, batch_service, sample_audio_files):
        """Full file path stored."""
        job = await batch_service.create_job([sample_audio_files[0]])

        assert job.files[0].file_path == sample_audio_files[0]


# =============================================================================
# File Validation Tests
# =============================================================================


class TestCreateJobValidation:
    """File validation tests for create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_empty_file_list(self, batch_service):
        """Empty file list raises ValueError."""
        with pytest.raises(ValueError, match="At least one file path is required"):
            await batch_service.create_job([])

    @pytest.mark.asyncio
    async def test_create_job_nonexistent_file(self, batch_service):
        """Nonexistent file is accepted (validation happens later)."""
        # Note: create_job doesn't validate file existence
        # This is by design - validation happens during processing
        job = await batch_service.create_job(["/nonexistent/path/file.wav"])

        assert len(job.files) == 1
        assert job.files[0].file_path == "/nonexistent/path/file.wav"

    @pytest.mark.asyncio
    async def test_create_job_mixed_valid_invalid_files(self, batch_service, sample_audio_files):
        """Mixed valid/invalid files accepted."""
        files = sample_audio_files[:2] + ["/nonexistent/file.wav"] + sample_audio_files[2:]
        job = await batch_service.create_job(files)

        assert len(job.files) == 5

    @pytest.mark.asyncio
    async def test_create_job_duplicate_files(self, batch_service, sample_audio_files):
        """Duplicate file paths create separate entries."""
        job = await batch_service.create_job([sample_audio_files[0], sample_audio_files[0]])

        assert len(job.files) == 2
        assert job.files[0].file_path == job.files[1].file_path
        assert job.files[0].id != job.files[1].id  # But different IDs

    @pytest.mark.asyncio
    async def test_create_job_various_extensions(self, batch_service):
        """Various audio file extensions accepted."""
        files = [
            "/path/file.wav",
            "/path/file.mp3",
            "/path/file.flac",
            "/path/file.m4a",
            "/path/file.ogg",
        ]
        job = await batch_service.create_job(files)

        assert len(job.files) == 5
        filenames = [f.filename for f in job.files]
        assert "file.wav" in filenames
        assert "file.mp3" in filenames
        assert "file.flac" in filenames


# =============================================================================
# Database Persistence Tests
# =============================================================================


class TestCreateJobPersistence:
    """Database persistence tests for create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_persists_to_database(self, batch_service, sample_audio_files):
        """Job is persisted to database."""
        job = await batch_service.create_job([sample_audio_files[0]])

        # Retrieve from database
        retrieved = await batch_service.get_job(job.id)
        assert retrieved is not None
        assert retrieved.id == job.id
        assert len(retrieved.files) == 1

    @pytest.mark.asyncio
    async def test_create_job_files_persisted(self, batch_service, sample_audio_files):
        """Files are persisted to database."""
        job = await batch_service.create_job(sample_audio_files)

        # Retrieve and verify files
        retrieved = await batch_service.get_job(job.id)
        assert retrieved is not None
        assert len(retrieved.files) == 5

        for i, file in enumerate(retrieved.files):
            assert file.filename == f"test_audio_{i}.wav"

    @pytest.mark.asyncio
    async def test_create_job_initializes_status(self, batch_service, sample_audio_files):
        """Job status initialized to PENDING."""
        job = await batch_service.create_job(sample_audio_files)

        assert job.status == JobStatus.PENDING
        assert all(f.status == JobStatus.PENDING for f in job.files)

        # Verify in database
        retrieved = await batch_service.get_job(job.id)
        assert retrieved.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_job_timestamp_set(self, batch_service, sample_audio_files):
        """Job created_at timestamp is set."""
        from datetime import datetime, timezone

        before = datetime.now(timezone.utc)
        job = await batch_service.create_job(sample_audio_files)
        after = datetime.now(timezone.utc)

        assert before <= job.created_at <= after

    @pytest.mark.asyncio
    async def test_create_job_without_initialization(self, temp_db_path, sample_audio_files):
        """Create job before initialization raises RuntimeError."""
        service = BatchService(db_path=str(temp_db_path))
        # Don't initialize

        with pytest.raises(RuntimeError, match="Database not initialized"):
            await service.create_job(sample_audio_files)


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestCreateJobErrorHandling:
    """Error handling tests for create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_database_insert_failure(self, batch_service, sample_audio_files):
        """Handle database insert failure."""
        # Mock execute to fail on INSERT
        original_execute = batch_service._db.execute

        async def mock_execute(query, *args):
            if "INSERT" in query:
                raise Exception("Insert failed")
            return await original_execute(query, *args)

        with patch.object(batch_service._db, "execute", side_effect=mock_execute):
            with pytest.raises(Exception, match="Insert failed"):
                await batch_service.create_job(sample_audio_files)

    @pytest.mark.asyncio
    async def test_create_job_commit_failure(self, batch_service, sample_audio_files):
        """Handle commit failure."""
        with patch.object(batch_service._db, "commit", side_effect=Exception("Commit failed")):
            with pytest.raises(Exception, match="Commit failed"):
                await batch_service.create_job(sample_audio_files)

    @pytest.mark.asyncio
    async def test_create_job_rollback_on_failure(self, batch_service, sample_audio_files):
        """Verify rollback happens on failure."""
        # Count jobs before
        jobs_before = await batch_service.list_jobs()

        # Mock to fail after insert but before commit
        with patch.object(batch_service._db, "commit", side_effect=Exception("Commit failed")):
            with pytest.raises(Exception):
                await batch_service.create_job(sample_audio_files)

        # Count jobs after - should be same
        jobs_after = await batch_service.list_jobs()
        assert len(jobs_after) == len(jobs_before)


# =============================================================================
# Concurrent Access Tests
# =============================================================================


class TestCreateJobConcurrency:
    """Concurrent access tests for create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_concurrent_operations(self, batch_service, sample_audio_files):
        """Multiple concurrent job creations succeed."""

        async def create_task(i):
            return await batch_service.create_job([sample_audio_files[i % len(sample_audio_files)]])

        # Run 10 concurrent job creations
        tasks = [create_task(i) for i in range(10)]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 10
        assert all(isinstance(job, BatchJob) for job in results)

        # All should have unique IDs
        ids = [job.id for job in results]
        assert len(set(ids)) == 10

    @pytest.mark.asyncio
    async def test_create_job_rapid_sequential(self, batch_service, sample_audio_files):
        """Rapid sequential job creations succeed."""
        jobs = []
        for i in range(50):
            job = await batch_service.create_job([sample_audio_files[i % len(sample_audio_files)]])
            jobs.append(job)

        assert len(jobs) == 50
        assert all(job.id is not None for job in jobs)

        # Verify all were saved
        all_jobs = await batch_service.list_jobs()
        assert len(all_jobs) == 50


# =============================================================================
# Large Batch Tests
# =============================================================================


class TestCreateJobLargeBatches:
    """Large batch tests for create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_large_file_list(self, batch_service, sample_audio_files):
        """Large file list (1000 files) succeeds."""
        # Simulate 1000 files
        files = [f"/path/file_{i}.wav" for i in range(1000)]
        job = await batch_service.create_job(files)

        assert len(job.files) == 1000
        assert job.files[0].filename == "file_0.wav"
        assert job.files[999].filename == "file_999.wav"

    @pytest.mark.asyncio
    async def test_create_job_very_large_batch_performance(self, batch_service):
        """Very large batch (10000 files) completes in reasonable time."""
        import time

        files = [f"/path/file_{i}.wav" for i in range(10000)]

        start = time.perf_counter()
        job = await batch_service.create_job(files)
        elapsed = time.perf_counter() - start

        assert len(job.files) == 10000
        # Should complete in < 5 seconds
        assert elapsed < 5.0, f"Too slow: {elapsed:.3f}s for 10000 files"


# =============================================================================
# Edge Cases Tests
# =============================================================================


class TestCreateJobEdgeCases:
    """Edge case tests for create_job()."""

    @pytest.mark.asyncio
    async def test_create_job_unicode_filenames(self, batch_service):
        """Unicode filenames handled correctly."""
        files = [
            "/path/文件.wav",
            "/path/файл.mp3",
            "/path/ملف.flac",
        ]
        job = await batch_service.create_job(files)

        assert len(job.files) == 3
        assert "文件.wav" in [f.filename for f in job.files]

    @pytest.mark.asyncio
    async def test_create_job_very_long_paths(self, batch_service):
        """Very long file paths handled."""
        # Create path longer than 260 characters (Windows MAX_PATH)
        long_path = "/very/long/path/" + "subdir/" * 50 + "file.wav"
        job = await batch_service.create_job([long_path])

        assert len(job.files) == 1
        assert job.files[0].file_path == long_path

    @pytest.mark.asyncio
    async def test_create_job_special_characters_in_path(self, batch_service):
        """Special characters in path handled."""
        files = [
            "/path/with spaces/file.wav",
            "/path/with'quotes/file.mp3",
            '/path/with"double"/file.flac',
        ]
        job = await batch_service.create_job(files)

        assert len(job.files) == 3

    @pytest.mark.asyncio
    async def test_create_job_relative_paths(self, batch_service):
        """Relative paths accepted."""
        files = [
            "./relative/path/file.wav",
            "../parent/file.mp3",
            "current/file.flac",
        ]
        job = await batch_service.create_job(files)

        assert len(job.files) == 3


# =============================================================================
# Integration-like Scenarios
# =============================================================================


class TestCreateJobIntegrationScenarios:
    """Integration-like scenarios testing real usage patterns."""

    @pytest.mark.asyncio
    async def test_create_job_batch_upload_flow(self, batch_service, sample_audio_files):
        """Simulate batch upload from UI."""
        # User selects multiple files in UI
        selected_files = sample_audio_files[:3]

        # Create batch job
        job = await batch_service.create_job(selected_files)

        # Verify job created
        assert job is not None
        assert len(job.files) == 3

        # Verify can retrieve (simulating job status check)
        retrieved = await batch_service.get_job(job.id)
        assert retrieved is not None
        assert retrieved.status == JobStatus.PENDING

    @pytest.mark.asyncio
    async def test_create_job_folder_import_flow(self, batch_service):
        """Simulate importing all files from a folder."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            # Create 20 dummy files
            for i in range(20):
                (tmpdir / f"audio_{i}.wav").write_bytes(b"dummy")

            # Import all wav files
            files = [str(f) for f in tmpdir.glob("*.wav")]
            job = await batch_service.create_job(files)

            assert len(job.files) == 20

    @pytest.mark.asyncio
    async def test_create_job_drag_drop_flow(self, batch_service):
        """Simulate drag-and-drop file addition."""
        # User drags 5 files from different locations
        files = [
            "/Users/user/Downloads/recording1.wav",
            "/Users/user/Documents/meeting.mp3",
            "/Users/user/Desktop/interview.flac",
            "/Volumes/External/archive/old_recording.wav",
            "/Network/share/team/meeting.m4a",
        ]

        job = await batch_service.create_job(files)

        assert len(job.files) == 5
        # Verify all paths preserved exactly
        for i, file in enumerate(job.files):
            assert file.file_path == files[i]

    @pytest.mark.asyncio
    async def test_create_job_recurring_batch_flow(self, batch_service, sample_audio_files):
        """Simulate recurring batch processing (daily uploads)."""
        # Simulate 7 days of batch uploads
        jobs = []
        for day in range(7):
            job = await batch_service.create_job(
                [f"/recordings/day{day}/file{i}.wav" for i in range(10)]
            )
            jobs.append(job)

        # All jobs created
        assert len(jobs) == 7

        # Each has 10 files
        for job in jobs:
            assert len(job.files) == 10

        # All persisted
        all_jobs = await batch_service.list_jobs()
        assert len(all_jobs) == 7


# =============================================================================
# Performance Tests
# =============================================================================


class TestCreateJobPerformance:
    """Performance tests for create_job() (21 callers depend on this)."""

    @pytest.mark.asyncio
    async def test_create_job_speed_single_file(self, batch_service, sample_audio_files):
        """Single file job creation is fast."""
        import time

        start = time.perf_counter()
        await batch_service.create_job([sample_audio_files[0]])
        elapsed = time.perf_counter() - start

        # Should complete in < 20ms
        assert elapsed < 0.02, f"Too slow: {elapsed:.3f}s"

    @pytest.mark.asyncio
    async def test_create_job_speed_batch(self, batch_service, sample_audio_files):
        """Batch job creation is reasonably fast."""
        import time

        files = sample_audio_files * 20  # 100 files

        start = time.perf_counter()
        await batch_service.create_job(files)
        elapsed = time.perf_counter() - start

        # 100 files should complete in < 500ms
        assert elapsed < 0.5, f"Too slow: {elapsed:.3f}s for 100 files"

    @pytest.mark.asyncio
    async def test_create_job_memory_efficiency(self, batch_service):
        """Job creation doesn't leak memory."""
        import gc
        import tracemalloc

        tracemalloc.start()

        # Create 100 jobs with 10 files each
        for i in range(100):
            files = [f"/path/job{i}_file{j}.wav" for j in range(10)]
            await batch_service.create_job(files)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be reasonable (< 100MB)
        assert peak < 100 * 1024 * 1024, f"Too much memory: {peak / 1024 / 1024:.2f}MB"

        gc.collect()
