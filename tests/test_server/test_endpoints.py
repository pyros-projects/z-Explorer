"""Tests for Z-Explorer server endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from z_explorer.server import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for /api/health endpoint."""
    
    def test_health_returns_ok(self, client):
        """Test health check returns OK status."""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "z-explorer"
        assert "version" in data
    
    def test_health_returns_version(self, client):
        """Test health check includes version."""
        from z_explorer.cli import __version__

        response = client.get("/api/health")
        data = response.json()
        assert data["version"] == __version__


class TestGpuEndpoint:
    """Tests for /api/gpu endpoint."""
    
    def test_gpu_info_available(self, client):
        """Test GPU info when CUDA is available."""
        mock_info = {
            "allocated_gb": 4.5,
            "reserved_gb": 6.0,
            "total_gb": 24.0,
            "free_gb": 18.0,
        }
        
        # Patch at the import location (imported inside the endpoint function)
        with patch('z_explorer.image_generator.get_gpu_memory_info', return_value=mock_info):
            response = client.get("/api/gpu")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["free_gb"] == 18.0
    
    def test_gpu_info_unavailable(self, client):
        """Test GPU info when CUDA is not available."""
        mock_info = {"error": "CUDA not available"}
        
        with patch('z_explorer.image_generator.get_gpu_memory_info', return_value=mock_info):
            response = client.get("/api/gpu")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "CUDA" in data["error"]
    
    def test_gpu_info_exception(self, client):
        """Test GPU info handles exceptions gracefully."""
        with patch('z_explorer.image_generator.get_gpu_memory_info', side_effect=RuntimeError("Test error")):
            response = client.get("/api/gpu")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "error" in data


class TestVariablesEndpoint:
    """Tests for /api/variables endpoint."""
    
    def test_list_variables_success(self, client, mock_current_dir, temp_library):
        """Test listing variables returns success."""
        response = client.get("/api/variables")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] > 0
        assert len(data["variables"]) > 0
    
    def test_list_variables_structure(self, client, mock_current_dir, temp_library):
        """Test variable structure is correct."""
        response = client.get("/api/variables")
        data = response.json()
        
        # Check first variable has correct fields
        var = data["variables"][0]
        assert "id" in var
        assert "count" in var
        assert "sample" in var
        assert "file_path" in var
    
    def test_list_variables_sorted(self, client, mock_current_dir, temp_library):
        """Test variables are sorted by ID."""
        response = client.get("/api/variables")
        data = response.json()
        
        ids = [v["id"] for v in data["variables"]]
        assert ids == sorted(ids)
    
    def test_list_variables_error(self, client):
        """Test variables endpoint handles errors."""
        with patch('z_explorer.models.prompt_vars.load_prompt_vars', side_effect=RuntimeError("Test")):
            response = client.get("/api/variables")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["count"] == 0
        assert "error" in data


class TestUnloadEndpoint:
    """Tests for /api/unload endpoint."""
    
    def test_unload_success(self, client):
        """Test unload models succeeds."""
        with patch('z_explorer.llm_provider.unload_model') as mock_llm:
            with patch('z_explorer.image_generator.unload_pipeline') as mock_img:
                with patch('torch.cuda.is_available', return_value=False):
                    response = client.post("/api/unload")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["llm_unloaded"] is True
        assert data["image_model_unloaded"] is True
    
    def test_unload_partial_failure(self, client):
        """Test unload handles partial failures."""
        with patch('z_explorer.llm_provider.unload_model', side_effect=RuntimeError("LLM error")):
            with patch('z_explorer.image_generator.unload_pipeline'):
                with patch('torch.cuda.is_available', return_value=False):
                    response = client.post("/api/unload")
        
        assert response.status_code == 200
        data = response.json()
        assert data["llm_unloaded"] is False
        assert data["image_model_unloaded"] is True
        assert len(data["errors"]) > 0


class TestImagesEndpoint:
    """Tests for /api/images endpoint."""
    
    def test_list_images_empty(self, client, tmp_path):
        """Test listing images when directory is empty."""
        with patch('z_explorer.server._get_output_dir', return_value=tmp_path):
            response = client.get("/api/images")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["images"] == []
    
    def test_list_images_with_files(self, client, tmp_path):
        """Test listing images returns correct data."""
        # Create test images
        (tmp_path / "test1.png").write_bytes(b"fake png")
        (tmp_path / "test2.png").write_bytes(b"fake png 2")
        
        with patch('z_explorer.server._get_output_dir', return_value=tmp_path):
            response = client.get("/api/images")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["images"]) == 2
        
        # Check structure
        img = data["images"][0]
        assert "name" in img
        assert "url" in img
        assert "modified" in img
    
    def test_list_images_sorted_newest_first(self, client, tmp_path):
        """Test images are sorted by modification time."""
        import time
        
        # Create test images with different times
        (tmp_path / "older.png").write_bytes(b"fake")
        time.sleep(0.1)
        (tmp_path / "newer.png").write_bytes(b"fake")
        
        with patch('z_explorer.server._get_output_dir', return_value=tmp_path):
            response = client.get("/api/images")
        
        data = response.json()
        assert data["images"][0]["name"] == "newer.png"
        assert data["images"][1]["name"] == "older.png"


class TestConfigEndpoint:
    """Tests for /api/config endpoint."""
    
    def test_config_returns_model_info(self, client):
        """Test config returns model information."""
        from z_explorer.model_config import LoadingMode, LLMMode
        
        with patch('z_explorer.model_config.get_image_model_config') as mock_img:
            with patch('z_explorer.model_config.get_llm_config') as mock_llm:
                mock_img.return_value = MagicMock(
                    mode=LoadingMode.SDNQ,
                    sdnq_model="test/sdnq-model",
                    hf_repo=None,
                    local_path=None,
                )
                mock_llm.return_value = MagicMock(
                    mode=LLMMode.HF_DOWNLOAD,
                    hf_repo="Qwen/Qwen3-4B",
                    local_path=None,
                    gguf_file=None,
                )
                
                response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        assert "image_model" in data
        assert "image_mode" in data
        assert "llm_model" in data
        assert "llm_mode" in data
    
    def test_config_handles_errors(self, client):
        """Test config handles errors gracefully."""
        with patch('z_explorer.model_config.get_image_model_config', side_effect=Exception("Test")):
            response = client.get("/api/config")
        
        assert response.status_code == 200
        data = response.json()
        # Should return defaults on error
        assert "image_model" in data


class TestSetupStatusEndpoint:
    """Tests for /api/setup/status endpoint."""
    
    def test_status_returns_configured(self, client):
        """Test status returns configuration state."""
        with patch('z_explorer.model_config.is_configured', return_value=True):
            with patch('z_explorer.services.download.get_models_to_download', 
                       return_value=[("Model", "repo")]):
                with patch('z_explorer.services.download.check_models_downloaded',
                           return_value={"Model": True}):
                    response = client.get("/api/setup/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is True
        assert "models_needed" in data
        assert "models_downloaded" in data
    
    def test_status_unconfigured(self, client):
        """Test status when not configured."""
        with patch('z_explorer.model_config.is_configured', return_value=False):
            response = client.get("/api/setup/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False
    
    def test_status_handles_errors(self, client):
        """Test status handles errors gracefully."""
        with patch('z_explorer.model_config.is_configured', side_effect=Exception("Test")):
            response = client.get("/api/setup/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_configured"] is False


class TestSetupDownloadEndpoint:
    """Tests for /api/setup/download endpoint."""
    
    def test_download_returns_sse(self, client):
        """Test download returns SSE stream."""
        with patch('z_explorer.services.download.download_all_models', return_value=True):
            response = client.get("/api/setup/download")
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_download_streams_progress(self, client):
        """Test download streams progress events."""
        from z_explorer.services.download import DownloadProgress
        
        def mock_download(on_progress=None):
            if on_progress:
                on_progress(DownloadProgress(
                    model_name="Test",
                    repo_id="test/repo",
                    status="downloading",
                ))
            return True
        
        with patch('z_explorer.services.download.download_all_models', side_effect=mock_download):
            response = client.get("/api/setup/download")
        
        assert response.status_code == 200
        # Check response contains event data
        content = response.text
        assert "data:" in content


class TestGenerateEndpoint:
    """Tests for /api/generate endpoint."""
    
    def test_generate_returns_sse(self, client, mock_all_models):
        """Test generate returns SSE stream."""
        with patch('z_explorer.image_generator.generate_image') as mock_gen:
            mock_gen.return_value = (MagicMock(), "/tmp/test.png")
            
            # SSE requests need special handling
            response = client.post(
                "/api/generate",
                json={"prompt": "a cat", "count": 1},
            )
        
        assert response.status_code == 200
        # SSE returns text/event-stream
        assert "text/event-stream" in response.headers.get("content-type", "")
    
    def test_generate_request_validation(self, client):
        """Test generate validates request."""
        # Missing prompt
        response = client.post("/api/generate", json={})
        assert response.status_code == 422  # Validation error
        
        # Invalid count
        response = client.post("/api/generate", json={"prompt": "test", "count": 0})
        assert response.status_code == 422
        
        # Invalid dimensions
        response = client.post("/api/generate", json={"prompt": "test", "width": 100})
        assert response.status_code == 422

