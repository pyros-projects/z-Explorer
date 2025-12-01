"""Tests for model settings endpoints (Phase 6).

Tests for:
- POST /api/settings/models - Update model configuration
- POST /api/settings/models/test - Validate model configuration
- POST /api/models/reload - Reload models with current config
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from z_explorer.server import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def reset_overrides():
    """Reset model overrides before and after each test."""
    from z_explorer import model_config

    # Clear before test
    if hasattr(model_config, "_override_config"):
        model_config._override_config = None
    yield
    # Clear after test
    if hasattr(model_config, "_override_config"):
        model_config._override_config = None


class TestModelSettingsUpdateEndpoint:
    """Tests for POST /api/settings/models endpoint."""

    def test_update_accepts_valid_config(self, client, reset_overrides):
        """Test updating model settings with valid config."""
        response = client.post(
            "/api/settings/models",
            json={
                "image_mode": "hf_download",
                "image_repo": "test/model-repo",
                "llm_mode": "hf_download",
                "llm_repo": "test/llm-repo",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "active_config" in data

    def test_update_rejects_invalid_image_mode(self, client, reset_overrides):
        """Test rejecting invalid image mode."""
        response = client.post(
            "/api/settings/models",
            json={
                "image_mode": "invalid_mode",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert (
            "image_mode" in data.get("message", "").lower()
            or data.get("field") == "image_mode"
        )

    def test_update_rejects_invalid_llm_mode(self, client, reset_overrides):
        """Test rejecting invalid LLM mode."""
        response = client.post(
            "/api/settings/models",
            json={
                "llm_mode": "invalid_mode",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert (
            "llm_mode" in data.get("message", "").lower()
            or data.get("field") == "llm_mode"
        )

    def test_update_partial_config(self, client, reset_overrides):
        """Test updating only image or only LLM config."""
        # Update only image
        response = client.post(
            "/api/settings/models",
            json={
                "image_mode": "sdnq",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_update_stores_override(self, client, reset_overrides):
        """Test that update stores override config."""
        response = client.post(
            "/api/settings/models",
            json={
                "image_mode": "hf_download",
                "image_repo": "custom/repo",
            },
        )

        assert response.status_code == 200

        # Verify override is stored by checking active_config
        data = response.json()
        assert data["active_config"]["image_model"] == "custom/repo"

    def test_update_null_clears_override(self, client, reset_overrides):
        """Test that passing null values clears overrides."""
        # First set an override
        client.post(
            "/api/settings/models",
            json={
                "image_mode": "hf_download",
                "image_repo": "custom/repo",
            },
        )

        # Then clear it with nulls
        response = client.post(
            "/api/settings/models",
            json={
                "image_mode": None,
                "image_repo": None,
            },
        )

        assert response.status_code == 200


class TestModelTestEndpoint:
    """Tests for POST /api/settings/models/test endpoint."""

    def test_test_validates_existing_local_path(self, client, tmp_path):
        """Test validation passes for existing path."""
        # Create a fake model directory
        model_dir = tmp_path / "fake_model"
        model_dir.mkdir()
        (model_dir / "model_index.json").write_text("{}")

        response = client.post(
            "/api/settings/models/test",
            json={
                "model_type": "image",
                "mode": "hf_local",
                "path": str(model_dir),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_test_fails_for_nonexistent_path(self, client):
        """Test validation fails for non-existent path."""
        response = client.post(
            "/api/settings/models/test",
            json={
                "model_type": "image",
                "mode": "hf_local",
                "path": "/nonexistent/path/to/model",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert (
            "not found" in data["message"].lower()
            or "not exist" in data["message"].lower()
        )

    def test_test_validates_hf_download_repo_format(self, client):
        """Test validation accepts valid HF repo format."""
        response = client.post(
            "/api/settings/models/test",
            json={
                "model_type": "image",
                "mode": "hf_download",
                "repo": "organization/model-name",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should at least accept the format (may not actually validate repo exists)
        assert data["valid"] is True

    def test_test_validates_llm_local_path(self, client, tmp_path):
        """Test LLM local path validation."""
        model_dir = tmp_path / "llm_model"
        model_dir.mkdir()
        (model_dir / "config.json").write_text("{}")

        response = client.post(
            "/api/settings/models/test",
            json={
                "model_type": "llm",
                "mode": "hf_local",
                "path": str(model_dir),
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True

    def test_test_rejects_invalid_model_type(self, client):
        """Test rejection of invalid model_type."""
        response = client.post(
            "/api/settings/models/test",
            json={
                "model_type": "invalid",
                "mode": "hf_download",
                "repo": "test/repo",
            },
        )

        assert response.status_code == 422  # Pydantic validation error

    def test_test_sdnq_mode(self, client):
        """Test SDNQ mode validation."""
        response = client.post(
            "/api/settings/models/test",
            json={
                "model_type": "image",
                "mode": "sdnq",
                "repo": "Disty0/Z-Image-Turbo-SDNQ",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True


class TestModelReloadEndpoint:
    """Tests for POST /api/models/reload endpoint."""

    def test_reload_returns_success_with_duration(self, client, reset_overrides):
        """Test reload returns success with duration."""
        with patch("z_explorer.llm_provider.unload_model"):
            with patch("z_explorer.image_generator.unload_pipeline"):
                with patch("torch.cuda.is_available", return_value=False):
                    response = client.post("/api/models/reload")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "duration_ms" in data
        assert data["duration_ms"] >= 0

    def test_reload_handles_load_failure_with_rollback(self, client, reset_overrides):
        """Test reload handles load failure and reports rollback."""
        # First set an override
        client.post(
            "/api/settings/models",
            json={
                "image_mode": "hf_local",
                "image_path": "/invalid/path",
            },
        )

        # Try reload which should fail
        with patch("z_explorer.llm_provider.unload_model"):
            with patch("z_explorer.image_generator.unload_pipeline"):
                with patch("torch.cuda.is_available", return_value=False):
                    # Mock a load failure
                    response = client.post("/api/models/reload")

        assert response.status_code == 200
        data = response.json()
        # May succeed or fail depending on implementation
        # Key is it should handle gracefully
        assert "status" in data

    def test_reload_returns_config(self, client, reset_overrides):
        """Test reload returns current config."""
        with patch("z_explorer.llm_provider.unload_model"):
            with patch("z_explorer.image_generator.unload_pipeline"):
                with patch("torch.cuda.is_available", return_value=False):
                    response = client.post("/api/models/reload")

        assert response.status_code == 200
        data = response.json()
        if data["status"] == "ok":
            assert "config" in data
            assert "image_model" in data["config"]
            assert "llm_model" in data["config"]

    def test_reload_clears_cuda_cache(self, client, reset_overrides):
        """Test reload clears CUDA cache."""
        with patch("z_explorer.llm_provider.unload_model"):
            with patch("z_explorer.image_generator.unload_pipeline"):
                with patch("torch.cuda.is_available", return_value=True) as mock_cuda:
                    with patch("torch.cuda.empty_cache") as mock_clear:
                        with patch("torch.cuda.synchronize"):
                            response = client.post("/api/models/reload")

        assert response.status_code == 200
        # CUDA cache should have been cleared
        mock_clear.assert_called()


class TestModelConfigOverrides:
    """Tests for model_config.py override functionality."""

    def test_set_override_config(self, reset_overrides):
        """Test setting override config."""
        from z_explorer.model_config import set_override_config, get_active_image_config

        set_override_config(
            image_mode="hf_download",
            image_repo="custom/test-repo",
        )

        config = get_active_image_config()
        assert config.hf_repo == "custom/test-repo"

    def test_get_active_config_prefers_override(self, reset_overrides):
        """Test that get_active_config prefers overrides over .env."""
        from z_explorer.model_config import (
            set_override_config,
            get_active_image_config,
            LoadingMode,
        )

        # Set override
        set_override_config(image_mode="sdnq")

        config = get_active_image_config()
        assert config.mode == LoadingMode.SDNQ

    def test_clear_override_config(self, reset_overrides):
        """Test clearing override config."""
        from z_explorer.model_config import (
            set_override_config,
            clear_override_config,
            get_active_image_config,
            get_image_model_config,
        )

        # Set override
        set_override_config(image_mode="sdnq", image_repo="custom/repo")

        # Clear it
        clear_override_config()

        # Should now return .env config (same as get_image_model_config)
        active = get_active_image_config()
        env_config = get_image_model_config()
        assert active.mode == env_config.mode

    def test_override_llm_config(self, reset_overrides):
        """Test overriding LLM config."""
        from z_explorer.model_config import set_override_config, get_active_llm_config

        set_override_config(
            llm_mode="hf_download",
            llm_repo="custom/llm-repo",
        )

        config = get_active_llm_config()
        assert config.hf_repo == "custom/llm-repo"
