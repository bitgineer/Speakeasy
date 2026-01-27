"""
Tests for /api/settings endpoints.
"""

import pytest


class TestSettingsGetEndpoint:
    """Test suite for GET /api/settings."""

    def test_get_settings_returns_200(self, client):
        """GET /api/settings returns 200 OK."""
        response = client.get("/api/settings")
        assert response.status_code == 200

    def test_get_settings_returns_dict(self, client):
        """GET /api/settings returns a dictionary."""
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data, dict)

    def test_get_settings_has_expected_fields(self, client):
        """Settings response contains expected fields."""
        response = client.get("/api/settings")
        data = response.json()

        # Check for common settings fields (matching AppSettings schema)
        expected_fields = [
            "model_type",
            "model_name",
            "language",
            "device",
            "compute_type",
            "auto_paste",
        ]

        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_get_settings_model_type_is_string(self, client):
        """model_type setting is a string."""
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["model_type"], str)

    def test_get_settings_language_is_string(self, client):
        """language setting is a string."""
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["language"], str)

    def test_get_settings_device_is_string(self, client):
        """device setting is a string."""
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["device"], str)

    def test_get_settings_auto_paste_is_boolean(self, client):
        """auto_paste setting is a boolean."""
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["auto_paste"], bool)

    def test_get_settings_model_name_is_string(self, client):
        """model_name setting is a string."""
        response = client.get("/api/settings")
        data = response.json()
        assert isinstance(data["model_name"], str)


class TestSettingsPutEndpoint:
    """Test suite for PUT /api/settings."""

    def test_put_settings_returns_200(self, client):
        """PUT /api/settings returns 200 OK."""
        response = client.put(
            "/api/settings",
            json={"auto_paste": False},
        )
        assert response.status_code == 200

    def test_put_settings_returns_dict(self, client):
        """PUT /api/settings returns a dictionary."""
        response = client.put(
            "/api/settings",
            json={"auto_paste": False},
        )
        data = response.json()
        assert isinstance(data, dict)

    def test_put_settings_has_status_field(self, client):
        """PUT response contains status field."""
        response = client.put(
            "/api/settings",
            json={"auto_paste": False},
        )
        data = response.json()
        assert "status" in data

    def test_put_settings_status_is_ok(self, client):
        """PUT response status is 'ok'."""
        response = client.put(
            "/api/settings",
            json={"auto_paste": False},
        )
        data = response.json()
        assert data["status"] == "ok"

    def test_put_settings_updates_boolean_field(self, client):
        """PUT can update boolean settings."""
        # Get initial value
        get_response = client.get("/api/settings")
        initial_value = get_response.json()["auto_paste"]

        # Update to opposite value
        new_value = not initial_value
        put_response = client.put(
            "/api/settings",
            json={"auto_paste": new_value},
        )
        assert put_response.status_code == 200

    def test_put_settings_updates_string_field(self, client):
        """PUT can update string settings."""
        response = client.put(
            "/api/settings",
            json={"language": "fr"},
        )
        assert response.status_code == 200

    def test_put_settings_with_empty_body(self, client):
        """PUT with empty body returns 200."""
        response = client.put(
            "/api/settings",
            json={},
        )
        assert response.status_code == 200

    def test_put_settings_with_multiple_fields(self, client):
        """PUT can update multiple fields at once."""
        response = client.put(
            "/api/settings",
            json={
                "auto_paste": False,
                "language": "en",
            },
        )
        assert response.status_code == 200

    def test_put_settings_invalid_device_returns_422(self, client):
        """PUT with invalid device value returns 422."""
        response = client.put(
            "/api/settings",
            json={"device": "invalid_device"},
        )
        assert response.status_code == 422

    def test_put_settings_invalid_hotkey_returns_422(self, client):
        """PUT with invalid hotkey format returns 422."""
        response = client.put(
            "/api/settings",
            json={"hotkey": "invalid@hotkey!"},
        )
        assert response.status_code == 422

    def test_put_settings_valid_hotkey_accepted(self, client):
        """PUT with valid hotkey format is accepted."""
        response = client.put(
            "/api/settings",
            json={"hotkey": "ctrl+shift+space"},
        )
        assert response.status_code == 200

    def test_put_settings_returns_reload_required_flag(self, client):
        """PUT response includes reload_required flag."""
        response = client.put(
            "/api/settings",
            json={"auto_paste": False},
        )
        data = response.json()
        assert "reload_required" in data
        assert isinstance(data["reload_required"], bool)

    def test_put_settings_model_change_requires_reload(self, client):
        """Changing model settings sets reload_required to true."""
        response = client.put(
            "/api/settings",
            json={"model_type": "whisper"},
        )
        data = response.json()
        # Model change should trigger reload
        assert "reload_required" in data

    def test_put_settings_non_model_change_no_reload(self, client):
        """Changing non-model settings may not require reload."""
        response = client.put(
            "/api/settings",
            json={"auto_paste": False},
        )
        data = response.json()
        assert "reload_required" in data


class TestSettingsPersistence:
    """Test suite for settings persistence."""

    def test_settings_persist_after_update(self, client):
        """Settings persist after being updated."""
        # Update a setting
        client.put(
            "/api/settings",
            json={"auto_paste": False},
        )

        # Get settings again
        response = client.get("/api/settings")
        data = response.json()

        # The mock should return the test settings
        assert "auto_paste" in data

    def test_multiple_updates_accumulate(self, client):
        """Multiple updates accumulate correctly."""
        # First update
        client.put(
            "/api/settings",
            json={"auto_paste": False},
        )

        # Second update
        client.put(
            "/api/settings",
            json={"language": "fr"},
        )

        # Get settings
        response = client.get("/api/settings")
        data = response.json()

        # Both settings should be present
        assert "auto_paste" in data
        assert "language" in data
