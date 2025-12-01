"""Shared type definitions for Z-Explorer.

These Pydantic models are used by both CLI and Server modes to ensure
consistent data structures across the application.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# Valid stage values for progress events
ProgressStage = Literal[
    "starting",
    "loading_vars",
    "substituting",
    "var_missing",
    "var_generating",
    "var_saved",
    "enhancing",
    "enhanced",
    "phase1_complete",
    "final_prompt",
    "llm_unloaded",
    "loading_image_model",
    "generating_image",
    "diffusion_step",
    "image_saved",
    "complete",
    "error",
]


class GenerationRequest(BaseModel):
    """Request to generate images.
    
    Attributes:
        prompt: The text prompt with optional __variables__ and > enhancement
        count: Number of images to generate (1-100)
        width: Image width in pixels (256-2048)
        height: Image height in pixels (256-2048)
        seed: Optional random seed for reproducibility
        enhance: Whether to apply LLM enhancement
        enhancement_instruction: Custom enhancement instructions
    """
    prompt: str = Field(..., min_length=1, description="The generation prompt")
    count: int = Field(default=1, ge=1, le=100, description="Number of images")
    width: int = Field(default=1024, ge=256, le=2048, description="Image width")
    height: int = Field(default=1024, ge=256, le=2048, description="Image height")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed")
    enhance: bool = Field(default=False, description="Apply LLM enhancement")
    enhancement_instruction: str = Field(default="", description="Enhancement instructions")


class ProgressEvent(BaseModel):
    """Progress update during generation.
    
    These events are emitted during the generation process to provide
    real-time feedback to CLI (Rich console) or GUI (SSE stream).
    
    Attributes:
        stage: Current stage of the generation process
        message: Human-readable progress message
        progress: Optional percentage (0-100)
        data: Optional additional data (e.g., image path, variable values)
    """
    stage: ProgressStage
    message: str
    progress: Optional[int] = Field(default=None, ge=0, le=100)
    data: Optional[dict] = None


class GenerationResult(BaseModel):
    """Result of image generation.
    
    Attributes:
        success: Whether generation completed successfully
        images: List of generated image file paths
        final_prompts: The prompts after variable substitution and enhancement
        errors: List of error messages if any
        seeds_used: Seeds used for each image
    """
    success: bool
    images: list[str] = Field(default_factory=list)
    final_prompts: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    seeds_used: list[int] = Field(default_factory=list)


class GpuInfo(BaseModel):
    """GPU memory information.
    
    Attributes:
        available: Whether CUDA GPU is available
        device_name: Name of the GPU device
        allocated_gb: Currently allocated memory in GB
        reserved_gb: Reserved memory in GB
        total_gb: Total GPU memory in GB
        free_gb: Free memory in GB
        error: Error message if GPU info unavailable
    """
    available: bool
    device_name: Optional[str] = None
    allocated_gb: Optional[float] = None
    reserved_gb: Optional[float] = None
    total_gb: Optional[float] = None
    free_gb: Optional[float] = None
    error: Optional[str] = None


class VariableInfo(BaseModel):
    """Information about a prompt variable.
    
    Attributes:
        id: Variable identifier (e.g., "__animal__")
        description: Optional description of the variable
        count: Number of available values
        sample: Sample values for preview
        file_path: Path to the variable definition file
    """
    id: str
    description: Optional[str] = None
    count: int = Field(ge=0)
    sample: list[str] = Field(default_factory=list)
    file_path: str

