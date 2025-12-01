"""Tests for the download service."""

import pytest
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

from z_explorer.services.download import (
    DownloadProgress,
    get_models_to_download,
    download_model_with_progress,
    download_all_models,
    check_models_downloaded,
)


class TestDownloadProgress:
    """Tests for DownloadProgress dataclass."""
    
    def test_progress_percent_with_bytes(self):
        """Test progress calculation with bytes."""
        progress = DownloadProgress(
            model_name="Test",
            repo_id="test/repo",
            status="downloading",
            bytes_done=500,
            bytes_total=1000,
        )
        assert progress.progress_percent == 50.0
    
    def test_progress_percent_with_files(self):
        """Test progress calculation with files when no bytes."""
        progress = DownloadProgress(
            model_name="Test",
            repo_id="test/repo",
            status="downloading",
            files_done=3,
            files_total=10,
        )
        assert progress.progress_percent == 30.0
    
    def test_progress_percent_zero_total(self):
        """Test progress is 0 when totals are zero."""
        progress = DownloadProgress(
            model_name="Test",
            repo_id="test/repo",
            status="pending",
        )
        assert progress.progress_percent == 0
    
    def test_to_dict(self):
        """Test converting progress to dictionary."""
        progress = DownloadProgress(
            model_name="Test Model",
            repo_id="test/repo",
            status="downloading",
            bytes_done=1024 * 1024,  # 1MB
            bytes_total=10 * 1024 * 1024,  # 10MB
            speed_bps=1024 * 1024,  # 1MB/s
            eta_seconds=9.0,
        )
        
        d = progress.to_dict()
        
        assert d["model_name"] == "Test Model"
        assert d["repo_id"] == "test/repo"
        assert d["status"] == "downloading"
        assert d["progress_percent"] == 10.0
        assert d["speed_mbps"] == 1.0
        assert d["eta_seconds"] == 9


class TestGetModelsToDownload:
    """Tests for get_models_to_download function."""
    
    def test_returns_empty_for_local_mode(self):
        """Test returns empty list when using local models."""
        from z_explorer.model_config import LoadingMode, LLMMode
        
        with patch('z_explorer.model_config.get_image_model_config') as mock_img:
            with patch('z_explorer.model_config.get_llm_config') as mock_llm:
                mock_img.return_value = MagicMock(mode=LoadingMode.HF_LOCAL)
                mock_llm.return_value = MagicMock(mode=LLMMode.HF_LOCAL)
                
                models = get_models_to_download()
                
        assert models == []
    
    def test_returns_sdnq_model(self):
        """Test returns SDNQ model when configured."""
        from z_explorer.model_config import LoadingMode, LLMMode
        
        with patch('z_explorer.model_config.get_image_model_config') as mock_img:
            with patch('z_explorer.model_config.get_llm_config') as mock_llm:
                mock_img.return_value = MagicMock(
                    mode=LoadingMode.SDNQ,
                    sdnq_model="test/sdnq-model"
                )
                mock_llm.return_value = MagicMock(mode=LLMMode.HF_LOCAL)
                
                models = get_models_to_download()
        
        assert len(models) == 1
        assert "SDNQ" in models[0][0]
        assert models[0][1] == "test/sdnq-model"
    
    def test_returns_both_models(self):
        """Test returns both image and LLM models."""
        from z_explorer.model_config import LoadingMode, LLMMode
        
        with patch('z_explorer.model_config.get_image_model_config') as mock_img:
            with patch('z_explorer.model_config.get_llm_config') as mock_llm:
                mock_img.return_value = MagicMock(
                    mode=LoadingMode.HF_DOWNLOAD,
                    hf_repo="test/image-model"
                )
                mock_llm.return_value = MagicMock(
                    mode=LLMMode.HF_DOWNLOAD,
                    hf_repo="test/llm-model"
                )
                
                models = get_models_to_download()
        
        assert len(models) == 2


class TestDownloadModelWithProgress:
    """Tests for download_model_with_progress function."""
    
    def test_calls_progress_callback(self):
        """Test progress callback is called during download."""
        progress_updates = []
        
        def on_progress(progress):
            progress_updates.append(progress.status)
        
        # Mock at the module level where snapshot_download is imported
        import z_explorer.services.download as download_module
        original_snapshot = getattr(download_module, 'snapshot_download', None)
        
        with patch.object(download_module, 'get_repo_size', return_value=(1000, 5)):
            with patch.object(download_module, 'snapshot_download', return_value=None):
                result = download_model_with_progress(
                    model_name="Test",
                    repo_id="test/repo",
                    on_progress=on_progress,
                )
        
        assert result is True
        assert len(progress_updates) > 0
        # Should have checking and downloading stages
        assert "checking" in progress_updates
        assert "downloading" in progress_updates
        # Should end with complete
        assert progress_updates[-1] == "complete"
    
    def test_handles_download_error(self):
        """Test handles download errors gracefully."""
        progress_updates = []
        
        def on_progress(progress):
            progress_updates.append(progress)
        
        import z_explorer.services.download as download_module
        
        with patch.object(download_module, 'get_repo_size', return_value=(1000, 5)):
            with patch.object(download_module, 'snapshot_download', 
                              side_effect=Exception("Download failed")):
                result = download_model_with_progress(
                    model_name="Test",
                    repo_id="test/repo",
                    on_progress=on_progress,
                )
        
        assert result is False
        # Last status should be error
        assert progress_updates[-1].status == "error"
        assert progress_updates[-1].error is not None


class TestDownloadAllModels:
    """Tests for download_all_models function."""
    
    def test_returns_true_when_no_models_needed(self):
        """Test returns True when no models need downloading."""
        with patch('z_explorer.services.download.get_models_to_download', return_value=[]):
            result = download_all_models()
        
        assert result is True
    
    def test_downloads_all_models(self):
        """Test downloads all required models."""
        with patch('z_explorer.services.download.get_models_to_download', 
                   return_value=[("Model1", "repo1"), ("Model2", "repo2")]):
            with patch('z_explorer.services.download.download_model_with_progress', 
                       return_value=True) as mock_download:
                result = download_all_models()
        
        assert result is True
        assert mock_download.call_count == 2
    
    def test_stops_on_first_failure(self):
        """Test stops downloading on first failure."""
        with patch('z_explorer.services.download.get_models_to_download',
                   return_value=[("Model1", "repo1"), ("Model2", "repo2")]):
            with patch('z_explorer.services.download.download_model_with_progress',
                       return_value=False) as mock_download:
                result = download_all_models()
        
        assert result is False
        # Should stop after first failure
        assert mock_download.call_count == 1
    
    def test_is_sync_function(self):
        """Test download_all_models is a sync function (not async)."""
        import inspect
        assert not inspect.iscoroutinefunction(download_all_models)


class TestCheckModelsDownloaded:
    """Tests for check_models_downloaded function."""
    
    def test_returns_dict_of_model_status(self):
        """Test returns dictionary of model download status."""
        with patch.object(
            __import__('z_explorer.services.download', fromlist=['get_models_to_download']),
            'get_models_to_download',
            return_value=[("Model1", "repo1")]
        ):
            with patch('huggingface_hub.try_to_load_from_cache',
                       return_value="/path/to/cached"):
                result = check_models_downloaded()
        
        assert isinstance(result, dict)
        assert "Model1" in result
        assert result["Model1"] is True
    
    def test_returns_false_for_uncached(self):
        """Test returns False for models not in cache."""
        with patch.object(
            __import__('z_explorer.services.download', fromlist=['get_models_to_download']),
            'get_models_to_download',
            return_value=[("Model1", "repo1")]
        ):
            with patch('huggingface_hub.try_to_load_from_cache',
                       return_value=None):
                result = check_models_downloaded()
        
        assert result["Model1"] is False

