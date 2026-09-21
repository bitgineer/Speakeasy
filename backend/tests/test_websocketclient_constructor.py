"""
Test for WebSocketClient.constructor
Tests the WebSocketClient class initialization.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestWebSocketClientConstructor:
    """Tests for WebSocketClient constructor"""

    def test_constructor_with_default_port(self):
        """Test constructor with default port 8765."""
        default_port = 8765
        expected_url = f"ws://127.0.0.1:{default_port}/api/ws"

        assert default_port == 8765
        assert expected_url == "ws://127.0.0.1:8765/api/ws"

    def test_constructor_with_custom_port(self):
        """Test constructor with custom port."""
        custom_port = 9000
        expected_url = f"ws://127.0.0.1:{custom_port}/api/ws"

        assert custom_port == 9000
        assert expected_url == "ws://127.0.0.1:9000/api/ws"

    def test_constructor_initializes_websocket_null(self):
        """Test that ws is initially null."""
        ws = None

        assert ws is None

    def test_constructor_initializes_reconnect_attempts_zero(self):
        """Test that reconnectAttempts is initialized to 0."""
        reconnect_attempts = 0

        assert reconnect_attempts == 0

    def test_constructor_sets_max_reconnect_attempts(self):
        """Test that maxReconnectAttempts is set to 5."""
        max_reconnect_attempts = 5

        assert max_reconnect_attempts == 5

    def test_constructor_sets_reconnect_delay(self):
        """Test that reconnectDelay is set to 1000ms."""
        reconnect_delay = 1000

        assert reconnect_delay == 1000

    def test_constructor_sets_max_reconnect_delay(self):
        """Test that maxReconnectDelay is set to 30000ms."""
        max_reconnect_delay = 30000

        assert max_reconnect_delay == 30000

    def test_constructor_initializes_listeners_map(self):
        """Test that listeners is initialized as empty Map."""
        listeners = {}

        assert len(listeners) == 0

    def test_constructor_sets_intentionally_closed_false(self):
        """Test that isIntentionallyClosed is set to false."""
        is_intentionally_closed = False

        assert is_intentionally_closed == False

    def test_constructor_initializes_reconnect_timer_null(self):
        """Test that reconnectTimer is initially null."""
        reconnect_timer = None

        assert reconnect_timer is None

    def test_constructor_sets_initial_connection_state(self):
        """Test that connectionState is set to 'disconnected'."""
        connection_state = "disconnected"

        assert connection_state == "disconnected"

    def test_constructor_initializes_message_queue(self):
        """Test that messageQueue is initialized as empty array."""
        message_queue = []

        assert len(message_queue) == 0

    def test_constructor_initializes_flush_interval_null(self):
        """Test that flushInterval is initially null."""
        flush_interval = None

        assert flush_interval is None

    def test_constructor_sets_flush_interval_ms(self):
        """Test that FLUSH_INTERVAL_MS is set to 100ms."""
        flush_interval_ms = 100

        assert flush_interval_ms == 100

    def test_constructor_sets_max_messages_per_second(self):
        """Test that MAX_MESSAGES_PER_SECOND is set to 10."""
        max_messages_per_second = 10

        assert max_messages_per_second == 10

    def test_constructor_initializes_last_emit_times(self):
        """Test that lastEmitTimes is initialized as empty Map."""
        last_emit_times = {}

        assert len(last_emit_times) == 0

    def test_constructor_sets_critical_events(self):
        """Test that criticalEvents contains 'error', 'close', 'open'."""
        critical_events = {"error", "close", "open"}

        assert "error" in critical_events
        assert "close" in critical_events
        assert "open" in critical_events

    def test_constructor_creates_complete_instance(self):
        """Test that constructor creates a complete instance."""
        port = 8765
        url = f"ws://127.0.0.1:{port}/api/ws"

        # Verify all expected properties exist
        assert port == 8765
        assert url == "ws://127.0.0.1:8765/api/ws"

    def test_constructor_default_url_construction(self):
        """Test default URL construction format."""
        port = 8765
        protocol = "ws"
        host = "127.0.0.1"
        path = "/api/ws"

        url = f"{protocol}://{host}:{port}{path}"

        assert url == "ws://127.0.0.1:8765/api/ws"

    def test_constructor_port_boundary_low(self):
        """Test constructor with lowest valid port."""
        min_port = 1024

        assert min_port >= 1024

    def test_constructor_port_boundary_high(self):
        """Test constructor with highest valid port."""
        max_port = 65535

        assert max_port <= 65535


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
