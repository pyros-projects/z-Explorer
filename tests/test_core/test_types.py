"""Tests for z_explorer.core.types module."""

import pytest
from pydantic import ValidationError

from z_explorer.core.types import (
    GenerationRequest,
    GenerationResult,
    ProgressEvent,
    GpuInfo,
    VariableInfo,
)


class TestGenerationRequest:
    """Tests for GenerationRequest model."""
    
    def test_minimal_request(self):
        """Test creating request with only required fields."""
        req = GenerationRequest(prompt="a cute cat")
        assert req.prompt == "a cute cat"
        assert req.count == 1
        assert req.width == 1024
        assert req.height == 1024
        assert req.seed is None
        assert req.enhance is False
        assert req.enhancement_instruction == ""
    
    def test_full_request(self):
        """Test creating request with all fields."""
        req = GenerationRequest(
            prompt="a cute __animal__",
            count=5,
            width=512,
            height=768,
            seed=12345,
            enhance=True,
            enhancement_instruction="make it magical",
        )
        assert req.prompt == "a cute __animal__"
        assert req.count == 5
        assert req.width == 512
        assert req.height == 768
        assert req.seed == 12345
        assert req.enhance is True
        assert req.enhancement_instruction == "make it magical"
    
    def test_empty_prompt_fails(self):
        """Test that empty prompt raises validation error."""
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="")
    
    def test_count_bounds(self):
        """Test count field validation."""
        # Valid count
        req = GenerationRequest(prompt="test", count=1)
        assert req.count == 1
        
        req = GenerationRequest(prompt="test", count=100)
        assert req.count == 100
        
        # Invalid count - too low
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", count=0)
        
        # Invalid count - too high
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", count=101)
    
    def test_dimension_bounds(self):
        """Test width/height validation."""
        # Valid dimensions
        req = GenerationRequest(prompt="test", width=256, height=256)
        assert req.width == 256
        assert req.height == 256
        
        req = GenerationRequest(prompt="test", width=2048, height=2048)
        assert req.width == 2048
        assert req.height == 2048
        
        # Invalid width - too small
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", width=255)
        
        # Invalid width - too large
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", width=2049)
        
        # Invalid height - too small
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", height=100)
    
    def test_seed_validation(self):
        """Test seed field validation."""
        # Valid seed
        req = GenerationRequest(prompt="test", seed=0)
        assert req.seed == 0
        
        req = GenerationRequest(prompt="test", seed=2**32 - 1)
        assert req.seed == 2**32 - 1
        
        # Invalid seed - negative
        with pytest.raises(ValidationError):
            GenerationRequest(prompt="test", seed=-1)
    
    def test_serialization(self):
        """Test model serialization to dict/json."""
        req = GenerationRequest(prompt="test", count=2, seed=123)
        
        data = req.model_dump()
        assert data["prompt"] == "test"
        assert data["count"] == 2
        assert data["seed"] == 123
        
        json_str = req.model_dump_json()
        assert "test" in json_str
        assert "123" in json_str


class TestProgressEvent:
    """Tests for ProgressEvent model."""
    
    def test_minimal_event(self):
        """Test creating event with required fields only."""
        event = ProgressEvent(stage="starting", message="Starting...")
        assert event.stage == "starting"
        assert event.message == "Starting..."
        assert event.progress is None
        assert event.data is None
    
    def test_full_event(self):
        """Test creating event with all fields."""
        event = ProgressEvent(
            stage="generating_image",
            message="Generating image 1/3",
            progress=50,
            data={"prompt": "a cat"},
        )
        assert event.stage == "generating_image"
        assert event.message == "Generating image 1/3"
        assert event.progress == 50
        assert event.data == {"prompt": "a cat"}
    
    def test_valid_stages(self):
        """Test all valid stage values."""
        valid_stages = [
            "starting", "loading_vars", "substituting", "var_missing",
            "var_generating", "var_saved", "enhancing", "enhanced",
            "phase1_complete", "llm_unloaded", "loading_image_model",
            "generating_image", "image_saved", "complete", "error",
        ]
        
        for stage in valid_stages:
            event = ProgressEvent(stage=stage, message="test")
            assert event.stage == stage
    
    def test_invalid_stage(self):
        """Test that invalid stage raises validation error."""
        with pytest.raises(ValidationError):
            ProgressEvent(stage="invalid_stage", message="test")
    
    def test_progress_bounds(self):
        """Test progress field validation."""
        # Valid progress
        event = ProgressEvent(stage="starting", message="test", progress=0)
        assert event.progress == 0
        
        event = ProgressEvent(stage="complete", message="test", progress=100)
        assert event.progress == 100
        
        # Invalid progress - too low
        with pytest.raises(ValidationError):
            ProgressEvent(stage="starting", message="test", progress=-1)
        
        # Invalid progress - too high
        with pytest.raises(ValidationError):
            ProgressEvent(stage="starting", message="test", progress=101)
    
    def test_serialization(self):
        """Test event serialization."""
        event = ProgressEvent(
            stage="generating_image",
            message="Working...",
            progress=75,
            data={"image": 1},
        )
        
        data = event.model_dump()
        assert data["stage"] == "generating_image"
        assert data["progress"] == 75


class TestGenerationResult:
    """Tests for GenerationResult model."""
    
    def test_empty_result(self):
        """Test creating empty result."""
        result = GenerationResult(success=False)
        assert result.success is False
        assert result.images == []
        assert result.final_prompts == []
        assert result.errors == []
        assert result.seeds_used == []
    
    def test_successful_result(self):
        """Test creating successful result."""
        result = GenerationResult(
            success=True,
            images=["/path/to/img1.png", "/path/to/img2.png"],
            final_prompts=["a cat", "a dog"],
            seeds_used=[123, 456],
        )
        assert result.success is True
        assert len(result.images) == 2
        assert len(result.final_prompts) == 2
        assert len(result.seeds_used) == 2
    
    def test_result_with_errors(self):
        """Test creating result with errors."""
        result = GenerationResult(
            success=False,
            images=["/path/to/img1.png"],
            errors=["Image 2 failed", "Image 3 failed"],
        )
        assert result.success is False
        assert len(result.images) == 1
        assert len(result.errors) == 2


class TestGpuInfo:
    """Tests for GpuInfo model."""
    
    def test_gpu_available(self):
        """Test GPU info when available."""
        info = GpuInfo(
            available=True,
            device_name="NVIDIA RTX 4090",
            allocated_gb=4.5,
            reserved_gb=6.0,
            total_gb=24.0,
            free_gb=18.0,
        )
        assert info.available is True
        assert info.device_name == "NVIDIA RTX 4090"
        assert info.free_gb == 18.0
        assert info.error is None
    
    def test_gpu_unavailable(self):
        """Test GPU info when unavailable."""
        info = GpuInfo(
            available=False,
            error="CUDA not available",
        )
        assert info.available is False
        assert info.device_name is None
        assert info.error == "CUDA not available"


class TestVariableInfo:
    """Tests for VariableInfo model."""
    
    def test_variable_info(self):
        """Test creating variable info."""
        info = VariableInfo(
            id="__animal__",
            description="Various animals",
            count=10,
            sample=["cat", "dog", "fox"],
            file_path="/path/to/animal.md",
        )
        assert info.id == "__animal__"
        assert info.count == 10
        assert len(info.sample) == 3
        assert info.file_path == "/path/to/animal.md"
    
    def test_variable_without_description(self):
        """Test variable info without description."""
        info = VariableInfo(
            id="__color__",
            count=5,
            file_path="/path/to/color.md",
        )
        assert info.description is None
        assert info.sample == []

