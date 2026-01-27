"""
Tests for /api/models endpoints.
"""

import pytest


class TestModelsListEndpoint:
    """Test suite for GET /api/models."""

    def test_models_list_returns_200(self, client):
        """GET /api/models returns 200 OK."""
        response = client.get("/api/models")
        assert response.status_code == 200

    def test_models_list_returns_dict(self, client):
        """GET /api/models returns a dictionary."""
        response = client.get("/api/models")
        data = response.json()
        assert isinstance(data, dict)

    def test_models_list_has_models_field(self, client):
        """Response contains 'models' field."""
        response = client.get("/api/models")
        data = response.json()
        assert "models" in data

    def test_models_list_has_current_field(self, client):
        """Response contains 'current' field."""
        response = client.get("/api/models")
        data = response.json()
        assert "current" in data

    def test_models_list_models_is_dict(self, client):
        """'models' field is a dictionary."""
        response = client.get("/api/models")
        data = response.json()
        assert isinstance(data["models"], dict)

    def test_models_list_current_is_dict_or_null(self, client):
        """'current' field is a dictionary or null."""
        response = client.get("/api/models")
        data = response.json()
        assert data["current"] is None or isinstance(data["current"], dict)

    def test_models_list_contains_model_types(self, client):
        """Models dictionary contains model type keys."""
        response = client.get("/api/models")
        data = response.json()
        models = data["models"]

        # Should have at least some model types
        assert len(models) > 0
        assert isinstance(models, dict)

    def test_models_list_each_model_has_required_fields(self, client):
        """Each model in the list has required fields."""
        response = client.get("/api/models")
        data = response.json()
        models = data["models"]

        # Check that each model type has expected structure
        for model_type, model_info in models.items():
            assert isinstance(model_type, str)
            assert isinstance(model_info, dict)


class TestModelsTypesEndpoint:
    """Test suite for GET /api/models/types."""

    def test_models_types_returns_200(self, client):
        """GET /api/models/types returns 200 OK."""
        response = client.get("/api/models/types")
        assert response.status_code == 200

    def test_models_types_returns_dict(self, client):
        """GET /api/models/types returns a dictionary."""
        response = client.get("/api/models/types")
        data = response.json()
        assert isinstance(data, dict)

    def test_models_types_has_types_field(self, client):
        """Response contains 'types' field."""
        response = client.get("/api/models/types")
        data = response.json()
        assert "types" in data

    def test_models_types_is_list(self, client):
        """'types' field is a list."""
        response = client.get("/api/models/types")
        data = response.json()
        assert isinstance(data["types"], list)

    def test_models_types_contains_strings(self, client):
        """'types' list contains strings."""
        response = client.get("/api/models/types")
        data = response.json()
        types = data["types"]

        for model_type in types:
            assert isinstance(model_type, str)


class TestModelsByTypeEndpoint:
    """Test suite for GET /api/models/{model_type}."""

    def test_models_by_type_returns_200_for_valid_type(self, client):
        """GET /api/models/{type} returns 200 for valid type."""
        # First get available types
        types_response = client.get("/api/models/types")
        types = types_response.json()["types"]

        if types:
            model_type = types[0]
            response = client.get(f"/api/models/{model_type}")
            assert response.status_code == 200

    def test_models_by_type_returns_404_for_invalid_type(self, client):
        """GET /api/models/{type} returns 404 for invalid type."""
        response = client.get("/api/models/invalid_type_xyz")
        assert response.status_code == 404

    def test_models_by_type_returns_dict(self, client):
        """GET /api/models/{type} returns a dictionary."""
        types_response = client.get("/api/models/types")
        types = types_response.json()["types"]

        if types:
            model_type = types[0]
            response = client.get(f"/api/models/{model_type}")
            data = response.json()
            assert isinstance(data, dict)

    def test_models_by_type_has_required_fields(self, client):
        """Response has required fields."""
        types_response = client.get("/api/models/types")
        types = types_response.json()["types"]

        if types:
            model_type = types[0]
            response = client.get(f"/api/models/{model_type}")
            data = response.json()

            assert "models" in data
            assert "languages" in data
            assert "compute_types" in data
            assert "info" in data

    def test_models_by_type_models_is_list(self, client):
        """'models' field is a list."""
        types_response = client.get("/api/models/types")
        types = types_response.json()["types"]

        if types:
            model_type = types[0]
            response = client.get(f"/api/models/{model_type}")
            data = response.json()
            assert isinstance(data["models"], list)

    def test_models_by_type_languages_is_list(self, client):
        """'languages' field is a list."""
        types_response = client.get("/api/models/types")
        types = types_response.json()["types"]

        if types:
            model_type = types[0]
            response = client.get(f"/api/models/{model_type}")
            data = response.json()
            assert isinstance(data["languages"], list)

    def test_models_by_type_compute_types_is_list(self, client):
        """'compute_types' field is a list."""
        types_response = client.get("/api/models/types")
        types = types_response.json()["types"]

        if types:
            model_type = types[0]
            response = client.get(f"/api/models/{model_type}")
            data = response.json()
            assert isinstance(data["compute_types"], list)


class TestModelsRecommendEndpoint:
    """Test suite for GET /api/models/recommend."""

    def test_models_recommend_returns_200(self, client):
        """GET /api/models/recommend returns 200 OK."""
        response = client.get("/api/models/recommend")
        assert response.status_code == 200

    def test_models_recommend_returns_dict(self, client):
        """GET /api/models/recommend returns a dictionary."""
        response = client.get("/api/models/recommend")
        data = response.json()
        assert isinstance(data, dict)

    def test_models_recommend_has_required_fields(self, client):
        """Response contains required fields."""
        response = client.get("/api/models/recommend")
        data = response.json()

        assert "recommendation" in data
        assert "gpu" in data
        assert "reason" in data

    def test_models_recommend_recommendation_has_fields(self, client):
        """Recommendation contains model_type and model_name."""
        response = client.get("/api/models/recommend")
        data = response.json()
        recommendation = data["recommendation"]

        assert "model_type" in recommendation
        assert "model_name" in recommendation

    def test_models_recommend_model_type_is_string(self, client):
        """model_type in recommendation is a string."""
        response = client.get("/api/models/recommend")
        data = response.json()
        assert isinstance(data["recommendation"]["model_type"], str)

    def test_models_recommend_model_name_is_string(self, client):
        """model_name in recommendation is a string."""
        response = client.get("/api/models/recommend")
        data = response.json()
        assert isinstance(data["recommendation"]["model_name"], str)

    def test_models_recommend_gpu_is_dict(self, client):
        """'gpu' field is a dictionary."""
        response = client.get("/api/models/recommend")
        data = response.json()
        assert isinstance(data["gpu"], dict)

    def test_models_recommend_reason_is_string(self, client):
        """'reason' field is a string."""
        response = client.get("/api/models/recommend")
        data = response.json()
        assert isinstance(data["reason"], str)

    def test_models_recommend_with_translation_flag(self, client):
        """GET /api/models/recommend?needs_translation=true works."""
        response = client.get("/api/models/recommend?needs_translation=true")
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data

    def test_models_recommend_without_translation_flag(self, client):
        """GET /api/models/recommend?needs_translation=false works."""
        response = client.get("/api/models/recommend?needs_translation=false")
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
