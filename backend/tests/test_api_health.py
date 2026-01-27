"""
Tests for /api/health endpoint.
"""

import pytest


class TestHealthEndpoint:
    """Test suite for health check endpoint."""

    def test_health_returns_200(self, client):
        """GET /api/health returns 200 OK."""
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_response_has_required_fields(self, client):
        """Response has all required fields."""
        response = client.get("/api/health")
        data = response.json()

        # Check all required fields exist
        assert "status" in data
        assert "state" in data
        assert "model_loaded" in data
        assert "gpu_available" in data
        assert "gpu_name" in data
        assert "gpu_vram_gb" in data
        assert "model_name" in data

    def test_health_status_is_ok(self, client):
        """Status field is 'ok'."""
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_gpu_available_is_boolean(self, client):
        """gpu_available field is a boolean."""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data["gpu_available"], bool)

    def test_health_model_loaded_is_boolean(self, client):
        """model_loaded field is a boolean."""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data["model_loaded"], bool)

    def test_health_state_is_string(self, client):
        """state field is a string."""
        response = client.get("/api/health")
        data = response.json()
        assert isinstance(data["state"], str)

    def test_health_model_name_is_string_or_null(self, client):
        """model_name field is string or null."""
        response = client.get("/api/health")
        data = response.json()
        assert data["model_name"] is None or isinstance(data["model_name"], str)

    def test_health_gpu_name_is_string_or_null(self, client):
        """gpu_name field is string or null."""
        response = client.get("/api/health")
        data = response.json()
        assert data["gpu_name"] is None or isinstance(data["gpu_name"], str)

    def test_health_gpu_vram_gb_is_number_or_null(self, client):
        """gpu_vram_gb field is number or null."""
        response = client.get("/api/health")
        data = response.json()
        assert data["gpu_vram_gb"] is None or isinstance(data["gpu_vram_gb"], (int, float))

    def test_health_response_matches_schema(self, client):
        """Response matches HealthResponse schema."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()

        # Verify schema structure
        assert isinstance(data, dict)
        assert len(data) >= 7  # At least 7 fields

    def test_health_multiple_calls_consistent(self, client):
        """Multiple calls return consistent data."""
        response1 = client.get("/api/health")
        response2 = client.get("/api/health")

        data1 = response1.json()
        data2 = response2.json()

        # Status and model_loaded should be consistent
        assert data1["status"] == data2["status"]
        assert data1["model_loaded"] == data2["model_loaded"]
        assert data1["gpu_available"] == data2["gpu_available"]
