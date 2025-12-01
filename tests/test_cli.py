"""Tests for Z-Explorer CLI module."""

import pytest
from unittest.mock import patch


class TestCliImports:
    """Test that CLI module imports correctly."""

    def test_import_main(self):
        """Test main function imports."""
        from z_explorer.cli import main

        assert callable(main)

    def test_import_start_functions(self):
        """Test start functions import."""
        from z_explorer.cli import start_cli_mode, start_web_mode

        assert callable(start_cli_mode)
        assert callable(start_web_mode)

    def test_import_helpers(self):
        """Test helper functions import."""
        from z_explorer.cli import (
            _check_dependencies,
            _wait_for_server,
        )

        assert callable(_check_dependencies)
        assert callable(_wait_for_server)


class TestCheckDependencies:
    """Tests for _check_dependencies function."""

    def test_dependencies_available(self):
        """Test when dependencies are available."""
        from z_explorer.cli import _check_dependencies

        # Should return True since we have torch installed
        result = _check_dependencies()
        assert result is True

    def test_dependencies_missing(self):
        """Test when dependencies are missing."""

        with patch.dict("sys.modules", {"torch": None}):
            with patch("z_explorer.cli._check_dependencies") as mock:
                mock.return_value = False
                assert mock() is False


class TestDefaultPort:
    """Tests for default port configuration."""

    def test_default_port_value(self):
        """Test that default port is 8345."""
        from z_explorer.cli import DEFAULT_PORT

        assert DEFAULT_PORT == 8345


class TestMainArgParsing:
    """Tests for main() argument parsing."""

    def test_help_flag(self):
        """Test --help flag works."""
        import sys
        from z_explorer.cli import main

        with patch.object(sys, "argv", ["z-explorer", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_flag_calls_start_cli_mode(self):
        """Test --cli flag triggers CLI mode."""
        import sys
        from z_explorer.cli import main

        with patch.object(sys, "argv", ["z-explorer", "--cli"]):
            with patch("z_explorer.model_config.is_configured", return_value=True):
                with patch("z_explorer.cli.start_cli_mode") as mock_cli:
                    main()
                    mock_cli.assert_called_once()

    def test_custom_port(self):
        """Test --port flag is passed correctly."""
        import sys
        from z_explorer.cli import main

        with patch.object(sys, "argv", ["z-explorer", "--port", "9000"]):
            with patch("z_explorer.model_config.is_configured", return_value=True):
                with patch("z_explorer.cli.start_web_mode") as mock_web:
                    main()
                    mock_web.assert_called_once_with(9000, "127.0.0.1")

    def test_default_calls_web_mode(self):
        """Test no flags triggers web mode."""
        import sys
        from z_explorer.cli import main

        with patch.object(sys, "argv", ["z-explorer"]):
            with patch("z_explorer.model_config.is_configured", return_value=True):
                with patch("z_explorer.cli.start_web_mode") as mock_web:
                    main()
                    mock_web.assert_called_once_with(8345, "127.0.0.1")

    def test_custom_host(self):
        """Test --host flag is passed correctly."""
        import sys
        from z_explorer.cli import main

        with patch.object(sys, "argv", ["z-explorer", "--host", "0.0.0.0"]):
            with patch("z_explorer.model_config.is_configured", return_value=True):
                with patch("z_explorer.cli.start_web_mode") as mock_web:
                    main()
                    mock_web.assert_called_once_with(8345, "0.0.0.0")

    def test_custom_port_and_host(self):
        """Test both --port and --host flags work together."""
        import sys
        from z_explorer.cli import main

        with patch.object(
            sys, "argv", ["z-explorer", "--port", "9000", "--host", "0.0.0.0"]
        ):
            with patch("z_explorer.model_config.is_configured", return_value=True):
                with patch("z_explorer.cli.start_web_mode") as mock_web:
                    main()
                    mock_web.assert_called_once_with(9000, "0.0.0.0")
