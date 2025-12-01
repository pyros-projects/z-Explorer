"""Tests for image generator loading modes."""

from unittest.mock import patch, MagicMock

from z_explorer.model_config import LoadingMode, ImageModelConfig


class TestImageGeneratorConfigDetection:
    """Tests for how image_generator detects and uses config."""

    def test_loads_correct_mode_from_config(self, monkeypatch):
        """Image generator should read mode from model_config."""
        monkeypatch.setenv("Z_IMAGE_MODE", "hf_download")

        from z_explorer.model_config import get_image_model_config

        config = get_image_model_config()
        assert config.mode == LoadingMode.HF_DOWNLOAD

    def test_validates_config_before_loading(self, monkeypatch):
        """Should validate config and error on invalid config."""
        # Set components mode but don't provide paths
        monkeypatch.setenv("Z_IMAGE_MODE", "components")
        monkeypatch.delenv("Z_IMAGE_TRANSFORMER", raising=False)
        monkeypatch.delenv("Z_IMAGE_TEXT_ENCODER", raising=False)
        monkeypatch.delenv("Z_IMAGE_VAE", raising=False)

        from z_explorer.model_config import get_image_model_config

        config = get_image_model_config()

        is_valid, errors = config.validate()
        assert is_valid is False
        assert len(errors) > 0


class TestLoadPipelineHF:
    """Tests for HuggingFace loading mode (mocked)."""

    @patch("z_explorer.image_generator._load_pipeline_hf")
    @patch("z_explorer.image_generator._unload_llm_if_needed")
    @patch("z_explorer.model_config.get_image_model_config")
    @patch("torch.cuda.is_available", return_value=False)
    def test_calls_hf_loader_for_hf_download(
        self, mock_cuda, mock_config, mock_unload, mock_hf_loader, monkeypatch
    ):
        """For HF_DOWNLOAD mode, should use _load_pipeline_hf."""
        # Mock ZImagePipeline import (not available in PyPI diffusers)
        import sys

        mock_diffusers = MagicMock()
        mock_diffusers.ZImagePipeline = MagicMock()
        monkeypatch.setitem(sys.modules, "diffusers", mock_diffusers)

        # Configure mock
        config = ImageModelConfig(
            mode=LoadingMode.HF_DOWNLOAD, hf_repo="Tongyi-MAI/Z-Image-Turbo"
        )
        mock_config.return_value = config
        mock_hf_loader.return_value = MagicMock()

        # Reset the global pipeline
        import z_explorer.image_generator as img_gen

        img_gen._pipeline = None

        # Trigger loading
        img_gen._load_pipeline()

        # Verify HF loader was called
        mock_hf_loader.assert_called_once()

    @patch("z_explorer.image_generator._load_pipeline_hf")
    @patch("z_explorer.image_generator._unload_llm_if_needed")
    @patch("z_explorer.model_config.get_image_model_config")
    @patch("torch.cuda.is_available", return_value=False)
    def test_calls_hf_loader_for_hf_local(
        self, mock_cuda, mock_config, mock_unload, mock_hf_loader, tmp_path, monkeypatch
    ):
        """For HF_LOCAL mode, should use _load_pipeline_hf with local path."""
        # Mock ZImagePipeline import (not available in PyPI diffusers)
        import sys

        mock_diffusers = MagicMock()
        mock_diffusers.ZImagePipeline = MagicMock()
        monkeypatch.setitem(sys.modules, "diffusers", mock_diffusers)

        # Create fake HF directory
        (tmp_path / "model_index.json").write_text("{}")

        config = ImageModelConfig(
            mode=LoadingMode.HF_LOCAL, hf_local_path=str(tmp_path)
        )
        mock_config.return_value = config
        mock_hf_loader.return_value = MagicMock()

        # Reset the global pipeline
        import z_explorer.image_generator as img_gen

        img_gen._pipeline = None

        # Trigger loading
        img_gen._load_pipeline()

        # Verify HF loader was called with local path
        mock_hf_loader.assert_called_once_with(str(tmp_path))


class TestLoadPipelineComponents:
    """Tests for component loading mode (mocked)."""

    @patch("z_explorer.image_generator._load_pipeline_components")
    @patch("z_explorer.image_generator._unload_llm_if_needed")
    @patch("z_explorer.model_config.get_image_model_config")
    @patch("torch.cuda.is_available", return_value=False)
    def test_calls_component_loader_for_components_mode(
        self,
        mock_cuda,
        mock_config,
        mock_unload,
        mock_comp_loader,
        tmp_path,
        monkeypatch,
    ):
        """For COMPONENTS mode, should use _load_pipeline_components."""
        # Mock ZImagePipeline import (not available in PyPI diffusers)
        import sys

        mock_diffusers = MagicMock()
        mock_diffusers.ZImagePipeline = MagicMock()
        monkeypatch.setitem(sys.modules, "diffusers", mock_diffusers)

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
        mock_config.return_value = config
        mock_comp_loader.return_value = MagicMock()

        # Reset the global pipeline
        import z_explorer.image_generator as img_gen

        img_gen._pipeline = None

        # Trigger loading
        img_gen._load_pipeline()

        # Verify component loader was called with correct paths
        mock_comp_loader.assert_called_once_with(
            transformer_path=str(transformer),
            text_encoder_path=str(text_encoder),
            vae_path=str(vae),
        )


class TestUnloadLLMIfNeeded:
    """Tests for LLM unloading before image model load."""

    def test_unloads_llm_when_loaded(self):
        """Should unload LLM if it's loaded."""
        with patch("z_explorer.llm_provider._model", new=MagicMock()):
            with patch("z_explorer.llm_provider.unload_model") as mock_unload:
                from z_explorer.image_generator import _unload_llm_if_needed

                _unload_llm_if_needed()
                mock_unload.assert_called_once()

    def test_skips_unload_when_llm_not_loaded(self):
        """Should not unload LLM if it's not loaded."""
        with patch("z_explorer.llm_provider._model", None):
            with patch("z_explorer.llm_provider.unload_model") as mock_unload:
                from z_explorer.image_generator import _unload_llm_if_needed

                _unload_llm_if_needed()
                mock_unload.assert_not_called()


class TestGpuMemoryInfo:
    """Tests for GPU memory info function."""

    @patch("torch.cuda.is_available", return_value=True)
    @patch("torch.cuda.memory_allocated", return_value=1024**3)  # 1GB
    @patch("torch.cuda.memory_reserved", return_value=2 * 1024**3)  # 2GB
    @patch("torch.cuda.get_device_properties")
    @patch("torch.cuda.get_device_name", return_value="Test GPU")
    def test_returns_gpu_info_when_available(
        self, mock_name, mock_props, mock_reserved, mock_allocated, mock_available
    ):
        """Returns GPU memory info when CUDA is available."""
        mock_props.return_value.total_memory = 8 * 1024**3  # 8GB

        from z_explorer.image_generator import get_gpu_memory_info

        info = get_gpu_memory_info()

        assert "device_name" in info
        assert info["device_name"] == "Test GPU"
        assert info["allocated_gb"] == 1.0
        assert info["reserved_gb"] == 2.0
        assert info["total_gb"] == 8.0
        assert info["free_gb"] == 6.0

    @patch("torch.cuda.is_available", return_value=False)
    def test_returns_error_when_cuda_unavailable(self, mock_available):
        """Returns error dict when CUDA is not available."""
        from z_explorer.image_generator import get_gpu_memory_info

        info = get_gpu_memory_info()

        assert "error" in info
        assert "CUDA not available" in info["error"]


class TestOutputDirectory:
    """Tests for output directory handling."""

    def test_uses_env_var_for_output_dir(self, monkeypatch, tmp_path):
        """Should use LOCAL_OUTPUT_DIR env var if set."""
        output_dir = tmp_path / "custom_output"
        monkeypatch.setenv("LOCAL_OUTPUT_DIR", str(output_dir))

        from z_explorer.image_generator import _get_output_dir

        result = _get_output_dir()

        assert result == output_dir
        assert result.exists()  # Should create it

    def test_defaults_to_output_dir(self, monkeypatch, tmp_path):
        """Should default to ./output when env var not set."""
        monkeypatch.delenv("LOCAL_OUTPUT_DIR", raising=False)
        monkeypatch.chdir(tmp_path)

        from z_explorer.image_generator import _get_output_dir

        result = _get_output_dir()

        # Result is relative path ./output, check name matches
        assert result.name == "output"
        assert result.exists()
