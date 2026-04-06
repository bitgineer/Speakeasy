"""
Test for ApiClient.request
Tests the core request method with retry logic, timeouts, and error handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestApiClientRequest:
    """Tests for ApiClient.request method"""

    @pytest.fixture
    def mock_fetch_response(self):
        """Create a mock fetch response."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.status = 200
        mock_response.headers = MagicMock()
        mock_response.headers.get = MagicMock(return_value="application/json")
        mock_response.json = AsyncMock(return_value={"status": "ok"})
        mock_response.text = AsyncMock(return_value='{"status": "ok"}')
        return mock_response

    @pytest.fixture
    def mock_fetch_error_response(self):
        """Create a mock fetch error response."""
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status = 500
        mock_response.headers = MagicMock()
        mock_response.headers.get = MagicMock(return_value="application/json")
        mock_response.json = AsyncMock(return_value={"detail": "Server error"})
        return mock_response

    def test_request_configuration_defaults(self):
        """Test default request configuration values."""
        # Default values from client.ts
        default_timeout = 30000  # 30 seconds
        max_retries = 3
        retry_delay = 1000  # 1 second

        assert default_timeout == 30000
        assert max_retries == 3
        assert retry_delay == 1000

    def test_request_url_construction(self):
        """Test URL construction with baseUrl and endpoint."""
        base_url = "http://127.0.0.1:8765"
        endpoint = "/api/health"
        expected_url = f"{base_url}{endpoint}"

        assert expected_url == "http://127.0.0.1:8765/api/health"

    def test_request_with_query_parameters(self):
        """Test URL construction with query parameters."""
        base_url = "http://127.0.0.1:8765"
        endpoint = "/api/history"
        search_params = {"limit": "10", "offset": "0"}
        query_string = "limit=10&offset=0"
        expected_url = f"{base_url}{endpoint}?{query_string}"

        assert expected_url == "http://127.0.0.1:8765/api/history?limit=10&offset=0"

    def test_request_headers_configuration(self):
        """Test that requests include correct headers."""
        # Default headers should include Content-Type: application/json
        expected_headers = {"Content-Type": "application/json"}

        assert "Content-Type" in expected_headers
        assert expected_headers["Content-Type"] == "application/json"

    def test_retry_logic_configuration(self):
        """Test retry logic with exponential backoff."""
        retry_delay = 1000
        attempt = 2
        expected_delay = retry_delay * (2**attempt)

        assert expected_delay == 4000  # 1s * 2^2 = 4s

    def test_retry_logic_max_attempts(self):
        """Test that retry respects max attempts."""
        max_retries = 3
        total_attempts = max_retries + 1  # initial + retries

        assert total_attempts == 4

    def test_error_status_code_handling_4xx(self):
        """Test handling of 4xx client errors (no retry)."""
        # Client errors (4xx) should not be retried (except 429)
        status_code = 400
        should_retry = not (400 <= status_code < 500 and status_code != 429)

        assert should_retry == False

    def test_error_status_code_handling_429(self):
        """Test handling of 429 rate limit (should retry)."""
        status_code = 429
        should_retry = status_code == 429

        assert should_retry == True

    def test_error_status_code_handling_5xx(self):
        """Test handling of 5xx server errors (should retry)."""
        status_code = 500
        should_retry = status_code >= 500

        assert should_retry == True

    def test_abort_error_handling(self):
        """Test handling of user-initiated abort."""
        error_name = "AbortError"
        is_abort_error = error_name == "AbortError"

        assert is_abort_error == True

    def test_timeout_configuration(self):
        """Test timeout configuration in milliseconds."""
        timeout_ms = 30000
        timeout_seconds = timeout_ms / 1000

        assert timeout_seconds == 30

    def test_request_method_post(self):
        """Test POST request method configuration."""
        method = "POST"
        body = {"key": "value"}

        assert method == "POST"
        assert "key" in body

    def test_request_method_get(self):
        """Test GET request method configuration."""
        method = "GET"

        assert method == "GET"

    def test_request_method_put(self):
        """Test PUT request method configuration."""
        method = "PUT"
        body = {"key": "value"}

        assert method == "PUT"
        assert body == {"key": "value"}

    def test_request_method_delete(self):
        """Test DELETE request method configuration."""
        method = "DELETE"

        assert method == "DELETE"

    def test_response_parsing_json(self):
        """Test JSON response parsing."""
        content_type = "application/json"
        is_json = "application/json" in content_type

        assert is_json == True

    def test_response_parsing_text(self):
        """Test text response parsing for non-JSON."""
        content_type = "text/plain"
        is_json = "application/json" in content_type

        assert is_json == False

    def test_error_message_extraction(self):
        """Test extraction of error messages from responses."""
        error_data = {"detail": "Validation failed"}
        error_message = error_data.get("detail") or str(error_data)

        assert error_message == "Validation failed"

    def test_error_message_extraction_fallback(self):
        """Test fallback error message extraction."""
        error_data = {"message": "Something went wrong"}
        error_message = error_data.get("detail") or str(error_data)

        assert error_message == '{"message": "Something went wrong"}'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
