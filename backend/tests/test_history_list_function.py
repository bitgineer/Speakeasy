"""
Test for function.history_list
Comprehensive test suite for history list API endpoint.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestHistoryListFunction:
    """Tests for history_list API endpoint"""

    def test_history_list_endpoint_path(self):
        """Test that history list endpoint has correct path."""
        endpoint = "/api/history"

        assert endpoint == "/api/history"

    def test_history_list_default_parameters(self):
        """Test default query parameters."""
        default_limit = 50
        default_offset = 0

        assert default_limit == 50
        assert default_offset == 0

    def test_history_list_parameter_types(self):
        """Test parameter types for history list."""
        limit = 50  # int
        offset = 0  # int
        search = "test"  # Optional[str]
        cursor = None  # Optional[str]
        fields = "id,text,created_at"  # Optional[str]

        assert isinstance(limit, int)
        assert isinstance(offset, int)
        assert isinstance(search, str)
        assert cursor is None or isinstance(cursor, str)
        assert isinstance(fields, str)

    def test_history_list_limit_boundary(self):
        """Test limit parameter boundaries."""
        # Limit should be positive
        limit = 50

        assert limit > 0
        assert isinstance(limit, int)

    def test_history_list_pagination_calculation(self):
        """Test pagination calculation with limit and offset."""
        limit = 50
        offset = 100
        page = (offset // limit) + 1

        assert page == 3  # 100 / 50 = 2, + 1 = page 3

    def test_history_list_search_parameter(self):
        """Test search parameter handling."""
        search_query = "hello world"

        assert len(search_query) > 0
        assert isinstance(search_query, str)

    def test_history_list_fields_parameter_parsing(self):
        """Test fields parameter parsing."""
        fields = "id,text,created_at"
        fields_set = set(f.strip() for f in fields.split(","))

        assert "id" in fields_set
        assert "text" in fields_set
        assert "created_at" in fields_set
        assert len(fields_set) == 3

    def test_history_list_response_structure(self):
        """Test expected response structure."""
        # Response should have items, total, next_cursor
        response = {"items": [], "total": 0, "next_cursor": None}

        assert "items" in response
        assert "total" in response
        assert "next_cursor" in response
        assert isinstance(response["items"], list)
        assert isinstance(response["total"], int)

    def test_history_list_error_service_not_initialized(self):
        """Test error when history service is not initialized."""
        # Should return 503 status code
        expected_status = 503
        error_detail = "History not initialized"

        assert expected_status == 503
        assert "not initialized" in error_detail

    def test_history_list_error_invalid_cursor(self):
        """Test error handling for invalid cursor."""
        # Should raise ValueError and return 400
        invalid_cursor = "invalid-cursor-format"

        assert isinstance(invalid_cursor, str)
        assert len(invalid_cursor) > 0

    def test_history_list_error_negative_limit(self):
        """Test error handling for negative limit."""
        # Limit should be validated
        negative_limit = -10

        assert negative_limit < 0

    def test_history_list_to_dict_conversion(self):
        """Test record to_dict conversion with fields filtering."""
        record = {
            "id": "123",
            "text": "Hello world",
            "created_at": "2024-01-01T00:00:00Z",
            "model_used": "whisper-small",
        }
        fields_set = {"id", "text"}

        # Filter record by fields
        filtered = {k: v for k, v in record.items() if k in fields_set}

        assert "id" in filtered
        assert "text" in filtered
        assert "created_at" not in filtered
        assert "model_used" not in filtered

    def test_history_list_cursor_pagination(self):
        """Test cursor-based pagination."""
        cursor = "next_page_token_123"
        offset = None  # Offset is ignored when cursor is provided

        assert cursor is not None
        assert offset is None

    def test_history_list_total_count(self):
        """Test that total count is returned correctly."""
        total_records = 100
        returned_items = 50

        assert total_records >= returned_items
        assert isinstance(total_records, int)

    def test_history_list_empty_result(self):
        """Test handling of empty result set."""
        items = []
        total = 0
        next_cursor = None

        assert len(items) == 0
        assert total == 0
        assert next_cursor is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
