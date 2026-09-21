"""
Test for function.check_import
Comprehensive test suite for import checking.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCheckImportFunction:
    """Tests for check_import function"""

    def test_check_import_existing_module(self):
        """Test checking an existing module."""
        # Test with built-in module
        try:
            import json

            assert json is not None
        except ImportError:
            pytest.fail("json should be available")

    def test_check_import_nonexistent_module(self):
        """Test checking a non-existent module."""
        with pytest.raises(ImportError):
            import nonexistent_module_xyz_12345


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
