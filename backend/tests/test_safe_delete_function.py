"""
Test for safe_delete function
Comprehensive test suite for safe file deletion.
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from speakeasy.core.models import safe_delete


class TestSafeDeleteFunction:
    """Tests for safe_delete function"""

    def test_safe_delete_existing_file(self):
        """Test deleting an existing file."""
        # Create temp file
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)

        assert os.path.exists(temp_path)

        safe_delete(temp_path)

        assert not os.path.exists(temp_path)

    def test_safe_delete_nonexistent_file(self):
        """Test deleting a non-existent file."""
        nonexistent_path = "/tmp/nonexistent_file_12345.txt"

        # Should not raise
        safe_delete(nonexistent_path)

    def test_safe_delete_empty_path(self):
        """Test deleting with empty path."""
        # Should not raise
        safe_delete("")
        safe_delete(None)

    def test_safe_delete_directory(self):
        """Test that safe_delete handles directories."""
        temp_dir = tempfile.mkdtemp()

        # Directory should still exist (safe_delete only deletes files)
        safe_delete(temp_dir)

        assert os.path.exists(temp_dir)

        # Cleanup
        os.rmdir(temp_dir)

    def test_safe_delete_with_retries(self):
        """Test that safe_delete retries on failure."""
        # Create temp file
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)

        # Delete should succeed
        safe_delete(temp_path, max_retries=3)

        assert not os.path.exists(temp_path)

    def test_safe_delete_permission_error_handling(self):
        """Test handling of permission errors."""
        # This test is platform-specific
        fd, temp_path = tempfile.mkstemp()
        os.close(fd)

        try:
            # Make file unreadable/unwritable (Unix only)
            if os.name != "nt":
                os.chmod(temp_path, 0o000)

            # Should handle gracefully without crashing
            safe_delete(temp_path, max_retries=1, base_delay=0.01)
        finally:
            # Restore permissions for cleanup
            if os.path.exists(temp_path):
                os.chmod(temp_path, 0o644)
                os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
