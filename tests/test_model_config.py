"""Tests for model configuration and loading strategies."""


from z_explorer.model_config import (
    LoadingMode,
    ImageModelConfig,
    get_image_model_config,
    is_configured,
    save_config,
    DEFAULT_Z_IMAGE_REPO,
)


class TestLoadingMode:
    """Tests for LoadingMode enum."""

    def test_loading_modes_exist(self):
        """Test that all loading modes are defined."""
        assert LoadingMode.HF_DOWNLOAD == "hf_download"
        assert LoadingMode.HF_LOCAL == "hf_local"
        assert LoadingMode.COMPONENTS == "components"

    def test_loading_mode_from_string(self):
        """Test creating LoadingMode from string."""
        assert LoadingMode("hf_download") == LoadingMode.HF_DOWNLOAD
        assert LoadingMode("hf_local") == LoadingMode.HF_LOCAL
        assert LoadingMode("components") == LoadingMode.COMPONENTS


class TestImageModelConfig:
    """Tests for ImageModelConfig validation."""

    def test_hf_download_mode_always_valid(self):
        """HF download mode is always valid (downloads on demand)."""
        config = ImageModelConfig(mode=LoadingMode.HF_DOWNLOAD)
        is_valid, errors = config.validate()
        assert is_valid is True
        assert errors == []

    def test_hf_local_mode_requires_path(self):
        """HF local mode requires a valid path."""
        config = ImageModelConfig(mode=LoadingMode.HF_LOCAL)
        is_valid, errors = config.validate()
        assert is_valid is False
        assert "HF_LOCAL mode requires Z_IMAGE_HF path" in errors[0]

    def test_hf_local_mode_path_must_exist(self, tmp_path):
        """HF local mode path must exist."""
        # Use a path that definitely doesn't exist on any platform
        nonexistent = str(tmp_path / "this_path_definitely_does_not_exist_abc123")
        config = ImageModelConfig(mode=LoadingMode.HF_LOCAL, hf_local_path=nonexistent)
        is_valid, errors = config.validate()
        assert is_valid is False
        assert "does not exist" in errors[0]

    def test_hf_local_mode_valid_with_existing_path(self, tmp_path):
        """HF local mode is valid with existing HF directory."""
        # Create fake HF directory
        (tmp_path / "model_index.json").write_text("{}")

        config = ImageModelConfig(
            mode=LoadingMode.HF_LOCAL, hf_local_path=str(tmp_path)
        )
        is_valid, errors = config.validate()
        assert is_valid is True
        assert errors == []

    def test_components_mode_requires_all_paths(self):
        """Components mode requires transformer, text_encoder, and vae paths."""
        config = ImageModelConfig(mode=LoadingMode.COMPONENTS)
        is_valid, errors = config.validate()
        assert is_valid is False
        assert len(errors) == 3  # Missing all three components

    def test_components_mode_paths_must_exist(self, tmp_path):
        """Components mode paths must exist."""
        config = ImageModelConfig(
            mode=LoadingMode.COMPONENTS,
            transformer_path="/nonexistent/transformer.safetensors",
            text_encoder_path="/nonexistent/text_encoder.safetensors",
            vae_path="/nonexistent/vae.safetensors",
        )
        is_valid, errors = config.validate()
        assert is_valid is False
        assert len(errors) == 3

    def test_components_mode_valid_with_existing_files(self, tmp_path):
        """Components mode is valid with all existing files."""
        # Create fake safetensor files
        transformer = tmp_path / "transformer.safetensors"
        text_encoder = tmp_path / "text_encoder.safetensors"
        vae = tmp_path / "vae.safetensors"

        transformer.write_bytes(b"fake")
        text_encoder.write_bytes(b"fake")
        vae.write_bytes(b"fake")

        config = ImageModelConfig(
            mode=LoadingMode.COMPONENTS,
            transformer_path=str(transformer),
            text_encoder_path=str(text_encoder),
            vae_path=str(vae),
        )
        is_valid, errors = config.validate()
        assert is_valid is True
        assert errors == []


class TestGetImageModelConfig:
    """Tests for get_image_model_config function."""

    def test_defaults_to_hf_download(self, monkeypatch):
        """Without any env vars, defaults to HF download."""
        # Clear all relevant env vars
        for var in [
            "Z_IMAGE_MODE",
            "Z_IMAGE_HF",
            "Z_IMAGE_TRANSFORMER",
            "Z_IMAGE_TEXT_ENCODER",
            "Z_IMAGE_VAE",
            "Z_IMAGE_PATH",
        ]:
            monkeypatch.delenv(var, raising=False)

        config = get_image_model_config()
        assert config.mode == LoadingMode.HF_DOWNLOAD
        assert config.hf_repo == DEFAULT_Z_IMAGE_REPO

    def test_explicit_mode_hf_download(self, monkeypatch):
        """Explicit Z_IMAGE_MODE=hf_download."""
        monkeypatch.setenv("Z_IMAGE_MODE", "hf_download")
        config = get_image_model_config()
        assert config.mode == LoadingMode.HF_DOWNLOAD

    def test_explicit_mode_hf_local(self, monkeypatch, tmp_path):
        """Explicit Z_IMAGE_MODE=hf_local with path."""
        monkeypatch.setenv("Z_IMAGE_MODE", "hf_local")
        monkeypatch.setenv("Z_IMAGE_HF", str(tmp_path))
        config = get_image_model_config()
        assert config.mode == LoadingMode.HF_LOCAL
        assert config.hf_local_path == str(tmp_path)

    def test_explicit_mode_components(self, monkeypatch, tmp_path):
        """Explicit Z_IMAGE_MODE=components with paths."""
        transformer = tmp_path / "t.safetensors"
        text_encoder = tmp_path / "te.safetensors"
        vae = tmp_path / "v.safetensors"

        monkeypatch.setenv("Z_IMAGE_MODE", "components")
        monkeypatch.setenv("Z_IMAGE_TRANSFORMER", str(transformer))
        monkeypatch.setenv("Z_IMAGE_TEXT_ENCODER", str(text_encoder))
        monkeypatch.setenv("Z_IMAGE_VAE", str(vae))

        config = get_image_model_config()
        assert config.mode == LoadingMode.COMPONENTS
        assert config.transformer_path == str(transformer)
        assert config.text_encoder_path == str(text_encoder)
        assert config.vae_path == str(vae)

    def test_auto_detect_components_mode(self, monkeypatch, tmp_path):
        """Auto-detect components mode when all component paths are set."""
        # Clear explicit mode
        monkeypatch.delenv("Z_IMAGE_MODE", raising=False)

        transformer = tmp_path / "t.safetensors"
        text_encoder = tmp_path / "te.safetensors"
        vae = tmp_path / "v.safetensors"

        monkeypatch.setenv("Z_IMAGE_TRANSFORMER", str(transformer))
        monkeypatch.setenv("Z_IMAGE_TEXT_ENCODER", str(text_encoder))
        monkeypatch.setenv("Z_IMAGE_VAE", str(vae))

        config = get_image_model_config()
        assert config.mode == LoadingMode.COMPONENTS

    def test_auto_detect_hf_local_mode(self, monkeypatch, tmp_path):
        """Auto-detect HF local mode when Z_IMAGE_HF is set."""
        monkeypatch.delenv("Z_IMAGE_MODE", raising=False)
        monkeypatch.delenv("Z_IMAGE_TRANSFORMER", raising=False)
        monkeypatch.setenv("Z_IMAGE_HF", str(tmp_path))

        config = get_image_model_config()
        assert config.mode == LoadingMode.HF_LOCAL

    def test_strips_whitespace_from_paths(self, monkeypatch, tmp_path):
        """Whitespace in paths should be stripped."""
        monkeypatch.setenv("Z_IMAGE_MODE", "components")
        monkeypatch.setenv("Z_IMAGE_TRANSFORMER", str(tmp_path / "t.safetensors"))
        monkeypatch.setenv(
            "Z_IMAGE_TEXT_ENCODER", f" {tmp_path}/te.safetensors "
        )  # Extra spaces
        monkeypatch.setenv("Z_IMAGE_VAE", str(tmp_path / "v.safetensors"))

        config = get_image_model_config()
        # Should be stripped
        assert not config.text_encoder_path.startswith(" ")
        assert not config.text_encoder_path.endswith(" ")


class TestIsConfigured:
    """Tests for is_configured function."""

    def test_not_configured_by_default(self, monkeypatch):
        """Without any env vars, not configured."""
        # Must clear ALL indicator vars (both image and LLM)
        for var in [
            "Z_IMAGE_MODE",
            "Z_IMAGE_HF",
            "Z_IMAGE_TRANSFORMER",
            "Z_IMAGE_PATH",
            "LLM_MODE",
            "LLM_PATH",
            "LLM_REPO",
        ]:
            monkeypatch.delenv(var, raising=False)

        assert is_configured() is False

    def test_configured_with_mode(self, monkeypatch):
        """Configured if Z_IMAGE_MODE is set."""
        monkeypatch.setenv("Z_IMAGE_MODE", "hf_download")
        assert is_configured() is True

    def test_configured_with_hf_path(self, monkeypatch):
        """Configured if Z_IMAGE_HF is set."""
        monkeypatch.setenv("Z_IMAGE_HF", "/some/path")
        assert is_configured() is True

    def test_configured_with_transformer(self, monkeypatch):
        """Configured if Z_IMAGE_TRANSFORMER is set."""
        monkeypatch.setenv("Z_IMAGE_TRANSFORMER", "/some/path")
        assert is_configured() is True

    def test_configured_with_legacy_path(self, monkeypatch):
        """Configured if Z_IMAGE_PATH (legacy) is set."""
        monkeypatch.setenv("Z_IMAGE_PATH", "some/repo")
        assert is_configured() is True


class TestSaveConfig:
    """Tests for save_config function."""

    def test_saves_hf_download_mode(self, tmp_path, monkeypatch):
        """Saves HF download mode to .env file."""
        monkeypatch.chdir(tmp_path)

        env_path = save_config(image_mode=LoadingMode.HF_DOWNLOAD)

        assert env_path.exists()
        content = env_path.read_text()
        assert "Z_IMAGE_MODE" in content
        assert "hf_download" in content

    def test_saves_hf_local_mode(self, tmp_path, monkeypatch):
        """Saves HF local mode with path."""
        monkeypatch.chdir(tmp_path)
        local_path = "/home/user/models/z-image"

        env_path = save_config(
            image_mode=LoadingMode.HF_LOCAL,
            image_hf_local=local_path,
        )

        content = env_path.read_text()
        assert "hf_local" in content
        assert "Z_IMAGE_HF" in content
        assert local_path in content

    def test_saves_components_mode(self, tmp_path, monkeypatch):
        """Saves components mode with all paths."""
        monkeypatch.chdir(tmp_path)

        env_path = save_config(
            image_mode=LoadingMode.COMPONENTS,
            image_transformer="/path/transformer.safetensors",
            image_text_encoder="/path/text_encoder.safetensors",
            image_vae="/path/vae.safetensors",
        )

        content = env_path.read_text()
        assert "components" in content
        assert "Z_IMAGE_TRANSFORMER" in content
        assert "Z_IMAGE_TEXT_ENCODER" in content
        assert "Z_IMAGE_VAE" in content


class TestDefaultRepos:
    """Tests for default repository constants."""

    def test_default_z_image_repo(self):
        """Default Z-Image repo is set correctly."""
        assert DEFAULT_Z_IMAGE_REPO == "Tongyi-MAI/Z-Image-Turbo"
