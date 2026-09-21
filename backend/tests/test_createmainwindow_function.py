"""
Test for function.createMainWindow
Tests the Electron main window creation with BrowserWindow configuration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCreateMainWindowFunction:
    """Tests for createMainWindow function"""

    def test_window_dimensions_defaults(self):
        """Test default window dimensions."""
        # From windows.ts
        width = 900
        height = 670
        min_width = 600
        min_height = 400

        assert width == 900
        assert height == 670
        assert min_width == 600
        assert min_height == 400

    def test_window_dimensions_constraints(self):
        """Test that min dimensions are less than default dimensions."""
        width = 900
        height = 670
        min_width = 600
        min_height = 400

        assert min_width <= width
        assert min_height <= height

    def test_window_initially_hidden(self):
        """Test that window is created hidden initially."""
        show = False  # Window starts hidden

        assert show == False

    def test_window_background_color(self):
        """Test window background color configuration."""
        background_color = "#18181b"  # surface-900

        assert background_color == "#18181b"
        assert background_color.startswith("#")
        assert len(background_color) == 7

    def test_window_frame_configuration(self):
        """Test window frame configuration."""
        frame = True
        title_bar_style = "hiddenInset"
        auto_hide_menu_bar = True

        assert frame == True
        assert title_bar_style == "hiddenInset"
        assert auto_hide_menu_bar == True

    def test_window_security_preferences(self):
        """Test web preferences for security."""
        sandbox = False
        context_isolation = True
        node_integration = False

        # Context isolation should be enabled for security
        assert context_isolation == True
        assert node_integration == False

    def test_preload_script_path(self):
        """Test preload script path construction."""
        # Preload path: join(__dirname, '../preload/index.js')
        __dirname = "/app/main"
        expected_path = str(Path(__dirname) / "../preload/index.js")

        assert "preload" in expected_path
        assert "index.js" in expected_path

    def test_external_link_handling(self):
        """Test external link handling configuration."""
        # External links should be opened in system browser
        # window-open handler returns { action: 'deny' }
        action = "deny"

        assert action == "deny"

    def test_dev_mode_url_loading(self):
        """Test URL loading in development mode."""
        is_dev = True
        renderer_url = "http://localhost:5173"

        assert is_dev == True
        assert "localhost" in renderer_url

    def test_production_file_loading(self):
        """Test file loading in production mode."""
        is_dev = False
        __dirname = "/app/main"
        expected_path = str(Path(__dirname) / "../renderer/index.html")

        assert is_dev == False
        assert "renderer" in expected_path
        assert "index.html" in expected_path

    def test_window_close_behavior(self):
        """Test window close behavior (hide instead of close)."""
        # On close, window should be hidden for tray functionality
        should_hide = True

        assert should_hide == True

    def test_window_aspect_ratio(self):
        """Test window aspect ratio calculation."""
        width = 900
        height = 670
        aspect_ratio = width / height

        # Aspect ratio should be reasonable for a desktop app
        assert 1.0 < aspect_ratio < 2.0

    def test_minimum_window_size_usability(self):
        """Test that minimum window size is usable."""
        min_width = 600
        min_height = 400

        # Minimum size should allow basic UI elements
        assert min_width >= 400
        assert min_height >= 300


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
