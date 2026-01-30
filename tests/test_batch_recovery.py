import asyncio
import sys
import unittest
import os
from unittest.mock import MagicMock, AsyncMock

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Mock dependencies
sys.modules["aiosqlite"] = MagicMock()
sys.modules["pydantic"] = MagicMock()
sys.modules["pydantic_settings"] = MagicMock()
sys.modules["sounddevice"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["torch"] = MagicMock()

# Mock internal modules that might be triggered by __init__
sys.modules["speakeasy.services.settings"] = MagicMock()
sys.modules["speakeasy.services.history"] = MagicMock()
sys.modules["speakeasy.core.transcriber"] = MagicMock()

# Now import BatchService
# We need to bypass speakeasy.services.__init__ if possible, but we can't easily.
# But since we mocked speakeasy.services.settings, it should be fine.

from speakeasy.services.batch import (
    BatchService,
    BatchJob,
    BatchFile,
    BatchJobStatus,
    BatchFileStatus,
)


class TestBatchRecovery(unittest.IsolatedAsyncioTestCase):
    async def test_cuda_recovery(self):
        # Setup
        service = BatchService(MagicMock())
        service._db = AsyncMock()  # Mock database
        service._db.execute.return_value = AsyncMock()
        service._db.commit = AsyncMock()

        # Create a dummy job
        job = BatchJob(id="test-job")
        job.files = [
            BatchFile(
                id="f1", job_id="test-job", filename="crash.wav", file_path="crash.wav"
            ),
            BatchFile(
                id="f2", job_id="test-job", filename="ok.wav", file_path="ok.wav"
            ),
        ]
        job.status = BatchJobStatus.PENDING
        service._jobs["test-job"] = job

        # Mock Transcriber
        transcriber = MagicMock()
        transcriber.reload_model = MagicMock()

        # Mock transcribe_file to fail on first file, succeed on second
        def transcribe_side_effect(path, language):
            if path == "crash.wav":
                raise RuntimeError(
                    "CUDA error: an illegal memory access was encountered"
                )
            return MagicMock(
                text="Success", duration_ms=1000, model_used="test", language="en"
            )

        transcriber.transcribe_file.side_effect = transcribe_side_effect

        # Mock History
        history = AsyncMock()
        history.add.return_value = MagicMock(id="hist-1")

        # Mock broadcast
        broadcast = AsyncMock()

        print("Starting batch processing with simulated crash...")

        # Run process_job
        await service.process_job("test-job", transcriber, history, broadcast)

        # Assertions
        # 1. Reload model should be called
        transcriber.reload_model.assert_called_once()
        print("Verified: reload_model() called")

        # 2. First file should be FAILED with GPU Error
        self.assertEqual(job.files[0].status, BatchFileStatus.FAILED)
        self.assertEqual(job.files[0].error, "GPU Error - Model Reloaded")
        print(
            f"Verified: File 1 status is {job.files[0].status} with error '{job.files[0].error}'"
        )

        # 3. Second file should be COMPLETED (processing continued)
        self.assertEqual(job.files[1].status, BatchFileStatus.COMPLETED)
        print(f"Verified: File 2 status is {job.files[1].status}")

        print("\nTest Passed: Recovery logic triggered and batch continued.")


if __name__ == "__main__":
    unittest.main()
