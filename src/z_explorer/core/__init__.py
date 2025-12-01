"""Core module for Z-Explorer.

This module contains shared business logic used by both CLI and Server modes.
"""

from z_explorer.core.types import (
    GenerationRequest,
    GenerationResult,
    ProgressEvent,
    ProgressStage,
    GpuInfo,
    VariableInfo,
)
from z_explorer.core.generator import generate, ProgressCallback

__all__ = [
    # Types
    "GenerationRequest",
    "GenerationResult",
    "ProgressEvent",
    "ProgressStage",
    "GpuInfo",
    "VariableInfo",
    # Functions
    "generate",
    "ProgressCallback",
]
