"""FastAPI server for Z-Explorer GUI mode.

This module provides a REST API with Server-Sent Events (SSE) for real-time
progress streaming. It serves as the backend for the Tauri/browser GUI.

Default port: 8345

Usage:
    # As module
    from z_explorer.server import serve
    serve(port=8345)

    # Or via CLI
    z-explorer --server --port 8345
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Literal
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from loguru import logger

from z_explorer.core.types import (
    GenerationRequest,
    GenerationResult,
    ProgressEvent,
    GpuInfo,
    VariableInfo,
)
from z_explorer.core.generator import generate
from z_explorer.cli import __version__

# Configure loguru for server
logger.remove()  # Remove default handler
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="DEBUG",
    colorize=True,
)
logger.add(
    "logs/server_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="7 days",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
)

# Default configuration
DEFAULT_PORT = 8345
DEFAULT_HOST = "127.0.0.1"


def _get_output_dir() -> Path:
    """Get the output directory for generated images."""
    import os

    output_dir = Path(os.getenv("LOCAL_OUTPUT_DIR", "./output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _get_gui_dist_dir() -> Optional[Path]:
    """Get the GUI dist directory if it exists."""
    # Check relative to this module (for installed package)
    module_dir = Path(__file__).parent
    gui_dist = module_dir / "gui" / "dist"
    if gui_dist.exists():
        return gui_dist

    # Check for development mode (running from source)
    dev_dist = module_dir.parent.parent / "gui" / "dist"
    if dev_dist.exists():
        return dev_dist

    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    output_dir = _get_output_dir()
    print(f"[output] Output directory: {output_dir.absolute()}")

    # Mount output directory for serving generated images
    if output_dir.exists():
        app.mount("/output", StaticFiles(directory=str(output_dir)), name="output")

    # Mount GUI dist directory if it exists
    gui_dist = _get_gui_dist_dir()
    if gui_dist:
        print(f"[gui] Serving GUI from: {gui_dist}")
        # Mount assets directory
        assets_dir = gui_dist / "assets"
        if assets_dir.exists():
            app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")
    else:
        print("[gui] No GUI dist found - API only mode")

    yield
    # Shutdown
    print("[shutdown] Server shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Z-Explorer API",
    description="Local AI image generation with Z-Image-Turbo + Qwen3-4B",
    version=__version__,
    lifespan=lifespan,
)

# Enable CORS for Tauri and browser frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local desktop app
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Health & Status Endpoints
# ============================================================================


@app.get("/", include_in_schema=False)
async def serve_gui():
    """Serve the GUI index.html."""
    gui_dist = _get_gui_dist_dir()
    if gui_dist:
        index_file = gui_dist / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return JSONResponse(
        {"error": "GUI not found. Run 'npm run build' in src/z_explorer/gui first."},
        status_code=404,
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "version": __version__,
        "service": "z-explorer",
    }


@app.get("/api/gpu", response_model=GpuInfo)
async def get_gpu_info():
    """Get GPU memory information."""
    try:
        from z_explorer.image_generator import get_gpu_memory_info

        info = get_gpu_memory_info()

        if "error" in info:
            return GpuInfo(available=False, error=info.get("error"))

        return GpuInfo(
            available=True,
            device_name=info.get("device_name"),
            allocated_gb=info.get("allocated_gb"),
            reserved_gb=info.get("reserved_gb"),
            total_gb=info.get("total_gb"),
            free_gb=info.get("free_gb"),
        )
    except Exception as e:
        return GpuInfo(available=False, error=str(e))


# ============================================================================
# Variables Endpoints
# ============================================================================


class VariablesResponse(BaseModel):
    """Response model for variables listing."""

    success: bool
    count: int
    variables: list[VariableInfo]
    error: Optional[str] = None


@app.get("/api/variables", response_model=VariablesResponse)
async def list_variables():
    """List all available prompt variables."""
    try:
        from z_explorer.models.prompt_vars import load_prompt_vars

        prompt_vars = load_prompt_vars()

        variables = []
        for var_id, var in prompt_vars.items():
            variables.append(
                VariableInfo(
                    id=var_id,
                    description=var.description,
                    count=len(var.values),
                    sample=var.values[:5] if var.values else [],
                    file_path=var.file_path or "",
                )
            )

        # Sort by ID
        variables.sort(key=lambda v: v.id)

        return VariablesResponse(
            success=True,
            count=len(variables),
            variables=variables,
        )
    except Exception as e:
        return VariablesResponse(
            success=False,
            count=0,
            variables=[],
            error=str(e),
        )


# ============================================================================
# Setup & Download Endpoints
# ============================================================================


class SetupStatusResponse(BaseModel):
    """Response model for setup status."""

    is_configured: bool
    models_needed: list[dict]
    models_downloaded: dict[str, bool]


class DownloadProgressData(BaseModel):
    """Progress data for a download."""

    model_name: str
    repo_id: str
    status: str  # "pending", "checking", "downloading", "complete", "error"
    current_file: Optional[str] = None
    files_done: int = 0
    files_total: int = 0
    bytes_done: int = 0
    bytes_total: int = 0
    progress_percent: float = 0
    speed_mbps: float = 0
    eta_seconds: Optional[int] = None
    error: Optional[str] = None


class ModelConfigResponse(BaseModel):
    """Response model for current model configuration."""

    image_model: str
    image_mode: str
    llm_model: str
    llm_mode: str


@app.get("/api/config", response_model=ModelConfigResponse)
async def get_model_config():
    """Get the current model configuration for display.

    Returns the actual configured values from environment/config,
    not shortened/processed names.
    """
    try:
        from z_explorer.model_config import (
            get_image_model_config,
            get_llm_config,
            LoadingMode,
            LLMMode,
        )

        img_config = get_image_model_config()
        llm_config = get_llm_config()

        # Image model - show actual configured repo/path
        if img_config.mode == LoadingMode.SDNQ:
            image_model = img_config.sdnq_model or "SDNQ"
            image_mode = "sdnq"
        elif img_config.mode == LoadingMode.HF_DOWNLOAD:
            image_model = img_config.hf_repo or "Tongyi-MAI/Z-Image-Turbo"
            image_mode = "hf_download"
        elif img_config.mode == LoadingMode.HF_LOCAL:
            image_model = img_config.hf_local_path or "(not configured)"
            image_mode = "hf_local"
        elif img_config.mode == LoadingMode.COMPONENTS:
            # Show component paths summary
            image_model = "Custom components"
            image_mode = "components"
        else:
            image_model = "Unknown"
            image_mode = str(img_config.mode.value) if img_config.mode else "unknown"

        # LLM - show actual configured repo/path (no shortening!)
        if llm_config.mode == LLMMode.HF_DOWNLOAD:
            llm_model = llm_config.hf_repo or "Qwen/Qwen3-4B"
            llm_mode = "hf_download"
        elif llm_config.mode == LLMMode.GGUF:
            llm_model = llm_config.gguf_file or "(not configured)"
            llm_mode = "gguf"
        elif llm_config.mode == LLMMode.HF_LOCAL:
            llm_model = llm_config.hf_local_path or "(not configured)"
            llm_mode = "hf_local"
        elif llm_config.mode == LLMMode.Z_IMAGE:
            llm_model = "Z-Image Text Encoder"
            llm_mode = "z_image"
        else:
            llm_model = "Unknown"
            llm_mode = str(llm_config.mode.value) if llm_config.mode else "unknown"

        return ModelConfigResponse(
            image_model=image_model,
            image_mode=image_mode,
            llm_model=llm_model,
            llm_mode=llm_mode,
        )
    except Exception as e:
        logger.error(f"Error getting model config: {e}")
        return ModelConfigResponse(
            image_model="Z-Image-Turbo",
            image_mode="Unknown",
            llm_model="Qwen3-4B",
            llm_mode="Unknown",
        )


@app.get("/api/setup/status", response_model=SetupStatusResponse)
async def get_setup_status():
    """Check if models are configured and downloaded."""
    try:
        from z_explorer.model_config import is_configured
        from z_explorer.services.download import (
            get_models_to_download,
            check_models_downloaded,
        )

        configured = is_configured()
        models_needed = []

        if configured:
            for name, repo_id in get_models_to_download():
                models_needed.append({"name": name, "repo_id": repo_id})
            downloaded = check_models_downloaded()
        else:
            downloaded = {}

        return SetupStatusResponse(
            is_configured=configured,
            models_needed=models_needed,
            models_downloaded=downloaded,
        )
    except Exception as e:
        logger.error(f"Error getting setup status: {e}")
        return SetupStatusResponse(
            is_configured=False,
            models_needed=[],
            models_downloaded={},
        )


async def _download_event_stream():
    """SSE event stream for model download progress."""
    import queue
    import threading

    from z_explorer.services.download import download_all_models, DownloadProgress

    progress_queue: queue.Queue[DownloadProgress] = queue.Queue()
    download_complete = threading.Event()
    download_result = [False]  # Use list to allow mutation in thread
    download_error = [None]  # Track error message for final status

    def on_progress(progress: DownloadProgress):
        progress_queue.put(progress)

    def do_download():
        try:
            download_result[0] = download_all_models(on_progress=on_progress)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            download_error[0] = str(e)
        finally:
            download_complete.set()

    # Start download in background thread
    download_thread = threading.Thread(target=do_download)
    download_thread.start()

    last_error = None  # Track last error from progress updates

    # Stream progress events (non-blocking to keep event loop responsive)
    while not download_complete.is_set():
        # Use non-blocking get + async sleep to avoid blocking the event loop
        try:
            progress = progress_queue.get_nowait()
            progress_dict = progress.to_dict()
            # Capture error message from progress
            if progress_dict.get("error"):
                last_error = progress_dict["error"]
            yield {"data": json.dumps(progress_dict)}
        except queue.Empty:
            # Yield control back to event loop instead of blocking
            await asyncio.sleep(0.1)
            continue

    # Drain remaining events
    while not progress_queue.empty():
        try:
            progress = progress_queue.get_nowait()
            progress_dict = progress.to_dict()
            # Capture error message from progress
            if progress_dict.get("error"):
                last_error = progress_dict["error"]
            yield {"data": json.dumps(progress_dict)}
        except queue.Empty:
            break

    download_thread.join()

    # Determine final error message
    final_error = download_error[0] or last_error

    # Send final status with error message if failed
    final_status = {
        "status": "all_complete" if download_result[0] else "error",
        "success": download_result[0],
    }
    if not download_result[0] and final_error:
        final_status["message"] = final_error

    yield {"data": json.dumps(final_status)}


@app.get("/api/setup/download")
async def download_models_stream():
    """Download all required models with progress streaming via SSE."""
    return EventSourceResponse(
        _download_event_stream(),
        ping=1,
    )


# ============================================================================
# Model Management Endpoints
# ============================================================================


class UnloadResponse(BaseModel):
    """Response model for model unloading."""

    success: bool
    llm_unloaded: bool
    image_model_unloaded: bool
    cuda_cache_cleared: bool
    errors: list[str]


@app.post("/api/unload", response_model=UnloadResponse)
async def unload_models():
    """Unload all models to free GPU memory."""
    result = UnloadResponse(
        success=False,
        llm_unloaded=False,
        image_model_unloaded=False,
        cuda_cache_cleared=False,
        errors=[],
    )

    # Unload LLM
    try:
        from z_explorer.llm_provider import unload_model

        unload_model()
        result.llm_unloaded = True
    except Exception as e:
        result.errors.append(f"LLM unload: {e}")

    # Unload Image model
    try:
        from z_explorer.image_generator import unload_pipeline

        unload_pipeline()
        result.image_model_unloaded = True
    except Exception as e:
        result.errors.append(f"Image model unload: {e}")

    # Clear CUDA cache
    try:
        import gc

        gc.collect()

        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            result.cuda_cache_cleared = True
    except Exception as e:
        result.errors.append(f"CUDA cache: {e}")

    result.success = result.llm_unloaded or result.image_model_unloaded
    return result


# ============================================================================
# Model Settings Override Endpoints
# ============================================================================

# Valid modes for validation
VALID_IMAGE_MODES = {"hf_download", "hf_local", "sdnq", "components"}
VALID_LLM_MODES = {"hf_download", "hf_local", "gguf", "z_image"}


class ModelSettingsUpdate(BaseModel):
    """Request model for updating model settings."""

    image_mode: Optional[str] = None
    image_repo: Optional[str] = None
    image_path: Optional[str] = None
    llm_mode: Optional[str] = None
    llm_repo: Optional[str] = None
    llm_path: Optional[str] = None


class ModelSettingsResponse(BaseModel):
    """Response model for model settings update."""

    status: str
    active_config: Optional[ModelConfigResponse] = None
    message: Optional[str] = None
    field: Optional[str] = None


class ModelTestRequest(BaseModel):
    """Request model for testing model configuration."""

    model_type: Literal["image", "llm"]
    mode: str
    repo: Optional[str] = None
    path: Optional[str] = None


class ModelTestResponse(BaseModel):
    """Response model for model configuration test."""

    valid: bool
    message: str


class ModelReloadResponse(BaseModel):
    """Response model for model reload."""

    status: str
    duration_ms: Optional[int] = None
    config: Optional[ModelConfigResponse] = None
    message: Optional[str] = None
    rollback: Optional[bool] = None


def _get_active_model_config() -> ModelConfigResponse:
    """Get current active model configuration (with overrides applied)."""
    try:
        from z_explorer.model_config import (
            get_active_image_config,
            get_active_llm_config,
            LoadingMode,
            LLMMode,
        )

        img_config = get_active_image_config()
        llm_config = get_active_llm_config()

        # Image model
        if img_config.mode == LoadingMode.SDNQ:
            image_model = img_config.sdnq_model or "SDNQ"
            image_mode = "sdnq"
        elif img_config.mode == LoadingMode.HF_DOWNLOAD:
            image_model = img_config.hf_repo or "Tongyi-MAI/Z-Image-Turbo"
            image_mode = "hf_download"
        elif img_config.mode == LoadingMode.HF_LOCAL:
            image_model = img_config.hf_local_path or "(not configured)"
            image_mode = "hf_local"
        elif img_config.mode == LoadingMode.COMPONENTS:
            image_model = "Custom components"
            image_mode = "components"
        else:
            image_model = "Unknown"
            image_mode = str(img_config.mode.value) if img_config.mode else "unknown"

        # LLM
        if llm_config.mode == LLMMode.HF_DOWNLOAD:
            llm_model = llm_config.hf_repo or "Qwen/Qwen3-4B"
            llm_mode = "hf_download"
        elif llm_config.mode == LLMMode.GGUF:
            llm_model = llm_config.gguf_file or "(not configured)"
            llm_mode = "gguf"
        elif llm_config.mode == LLMMode.HF_LOCAL:
            llm_model = llm_config.hf_local_path or "(not configured)"
            llm_mode = "hf_local"
        elif llm_config.mode == LLMMode.Z_IMAGE:
            llm_model = "Z-Image Text Encoder"
            llm_mode = "z_image"
        else:
            llm_model = "Unknown"
            llm_mode = str(llm_config.mode.value) if llm_config.mode else "unknown"

        return ModelConfigResponse(
            image_model=image_model,
            image_mode=image_mode,
            llm_model=llm_model,
            llm_mode=llm_mode,
        )
    except Exception as e:
        logger.error(f"Error getting active model config: {e}")
        return ModelConfigResponse(
            image_model="Z-Image-Turbo",
            image_mode="Unknown",
            llm_model="Qwen3-4B",
            llm_mode="Unknown",
        )


@app.post("/api/settings/models", response_model=ModelSettingsResponse)
async def update_model_settings(request: ModelSettingsUpdate):
    """Update model configuration overrides.

    Accepts partial updates - only provided fields are updated.
    Pass null to clear a specific override.
    """
    from z_explorer.model_config import set_override_config, clear_override_config

    # Validate image_mode if provided
    if request.image_mode is not None and request.image_mode not in VALID_IMAGE_MODES:
        return ModelSettingsResponse(
            status="error",
            message=f"Invalid image_mode: {request.image_mode}. Valid modes: {VALID_IMAGE_MODES}",
            field="image_mode",
        )

    # Validate llm_mode if provided
    if request.llm_mode is not None and request.llm_mode not in VALID_LLM_MODES:
        return ModelSettingsResponse(
            status="error",
            message=f"Invalid llm_mode: {request.llm_mode}. Valid modes: {VALID_LLM_MODES}",
            field="llm_mode",
        )

    # Check if all values are None (clearing overrides)
    all_none = all(
        v is None
        for v in [
            request.image_mode,
            request.image_repo,
            request.image_path,
            request.llm_mode,
            request.llm_repo,
            request.llm_path,
        ]
    )

    if all_none:
        clear_override_config()
    else:
        # Apply non-None overrides
        set_override_config(
            image_mode=request.image_mode,
            image_repo=request.image_repo,
            image_path=request.image_path,
            llm_mode=request.llm_mode,
            llm_repo=request.llm_repo,
            llm_path=request.llm_path,
        )

    return ModelSettingsResponse(
        status="ok",
        active_config=_get_active_model_config(),
    )


@app.post("/api/settings/models/test", response_model=ModelTestResponse)
async def test_model_config(request: ModelTestRequest):
    """Test/validate a model configuration before applying.

    For hf_local/components: checks that path exists
    For hf_download: validates repo format (org/name)
    """
    if request.model_type == "image":
        valid_modes = VALID_IMAGE_MODES
    else:
        valid_modes = VALID_LLM_MODES

    if request.mode not in valid_modes:
        return ModelTestResponse(
            valid=False,
            message=f"Invalid mode: {request.mode}. Valid modes: {valid_modes}",
        )

    # Validate based on mode
    if request.mode in ("hf_local", "components"):
        # Check path exists
        if not request.path:
            return ModelTestResponse(
                valid=False,
                message="Path is required for hf_local/components mode",
            )

        path = Path(request.path)
        if not path.exists():
            return ModelTestResponse(
                valid=False,
                message=f"Path does not exist: {request.path}",
            )

        # For image hf_local, check for model_index.json
        if request.model_type == "image" and request.mode == "hf_local":
            if not (path / "model_index.json").exists():
                return ModelTestResponse(
                    valid=False,
                    message=f"Missing model_index.json in {request.path}",
                )

        return ModelTestResponse(
            valid=True,
            message=f"Path exists and appears valid: {request.path}",
        )

    elif request.mode in ("hf_download", "sdnq"):
        # Validate repo format (should be org/name)
        repo = request.repo
        if not repo:
            return ModelTestResponse(
                valid=True,
                message="Using default repository",
            )

        # Basic format check
        if "/" not in repo:
            return ModelTestResponse(
                valid=False,
                message=f"Invalid repo format: {repo}. Expected format: organization/model-name",
            )

        return ModelTestResponse(
            valid=True,
            message=f"Repository format valid: {repo}",
        )

    elif request.mode == "gguf":
        # GGUF requires path
        if not request.path:
            return ModelTestResponse(
                valid=False,
                message="Path is required for GGUF mode",
            )

        return ModelTestResponse(
            valid=True,
            message=f"GGUF path: {request.path}",
        )

    elif request.mode == "z_image":
        # Z-Image mode doesn't need additional config
        return ModelTestResponse(
            valid=True,
            message="Using Z-Image text encoder",
        )

    return ModelTestResponse(
        valid=True,
        message="Configuration appears valid",
    )


@app.post("/api/models/reload", response_model=ModelReloadResponse)
async def reload_models():
    """Reload models with current active configuration.

    Unloads current models, clears CUDA cache, then returns.
    Note: Models will be lazily loaded on next generation.
    """
    start_time = time.time()
    errors = []

    # Unload LLM
    try:
        from z_explorer.llm_provider import unload_model

        unload_model()
    except Exception as e:
        errors.append(f"LLM unload: {e}")

    # Unload Image model
    try:
        from z_explorer.image_generator import unload_pipeline

        unload_pipeline()
    except Exception as e:
        errors.append(f"Image model unload: {e}")

    # Clear CUDA cache
    try:
        import gc

        gc.collect()

        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
    except Exception as e:
        errors.append(f"CUDA cache: {e}")

    duration_ms = int((time.time() - start_time) * 1000)

    if errors:
        return ModelReloadResponse(
            status="error",
            duration_ms=duration_ms,
            message="; ".join(errors),
            rollback=False,
        )

    return ModelReloadResponse(
        status="ok",
        duration_ms=duration_ms,
        config=_get_active_model_config(),
    )


# ============================================================================
# Image Listing Endpoint
# ============================================================================


class ImageInfo(BaseModel):
    """Information about a generated image."""

    path: str
    name: str
    url: str
    modified: float
    prompt: Optional[str] = None


class ImagesResponse(BaseModel):
    """Response model for images listing."""

    images: list[ImageInfo]
    count: int


@app.get("/api/images", response_model=ImagesResponse)
async def list_images():
    """List all generated images, newest first."""
    output_dir = _get_output_dir()

    images = []
    for f in output_dir.glob("*.png"):
        # Try to read the prompt from the corresponding .txt file
        prompt = None
        prompt_file = f.with_suffix(".txt")
        if prompt_file.exists():
            try:
                prompt = prompt_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass

        images.append(
            ImageInfo(
                path=str(f),
                name=f.name,
                url=f"/output/{f.name}",
                modified=f.stat().st_mtime,
                prompt=prompt,
            )
        )

    # Sort by modification time, newest first
    images.sort(key=lambda x: x.modified, reverse=True)

    return ImagesResponse(images=images, count=len(images))


# ============================================================================
# Generation Endpoints with SSE
# ============================================================================


async def _generate_event_stream(request: GenerationRequest):
    """
    Shared event stream generator for image generation.

    Yields SSE events with JSON data for browser-friendly format.
    """
    logger.info(f"🎬 Starting SSE stream for prompt: {request.prompt[:50]}...")

    progress_queue: asyncio.Queue[ProgressEvent] = asyncio.Queue()
    result_holder: list[GenerationResult] = []
    error_holder: list[str] = []
    events_sent = 0
    events_queued = 0

    def on_progress(event: ProgressEvent):
        """Callback to queue progress events."""
        nonlocal events_queued
        try:
            progress_queue.put_nowait(event)
            events_queued += 1
            logger.debug(
                f"📤 [{events_queued}] Queued: stage={event.stage}, msg={event.message}, progress={event.progress}"
            )
        except Exception as e:
            logger.error(f"❌ Failed to queue progress event: {e}")

    def run_generation():
        """Run generation in thread pool."""
        logger.info("🔧 Generation thread started")
        try:
            result = generate(request, on_progress=on_progress)
            result_holder.append(result)
            logger.info(
                f"✅ Generation complete: {len(result.images)} images, prompts: {result.final_prompts}"
            )
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            error_holder.append(str(e))

    # Start generation in background thread
    loop = asyncio.get_event_loop()
    gen_task = loop.run_in_executor(None, run_generation)
    logger.debug("Generation task submitted to executor")

    def event_to_json(event: ProgressEvent) -> str:
        """Convert ProgressEvent to JSON for SSE."""
        path = event.data.get("path") if event.data else None
        return json.dumps(
            {
                "stage": event.stage,
                "message": event.message,
                "progress": event.progress,
                "path": path,
                "data": event.data,
            }
        )

    # Stream progress events while generation is running
    last_percent = -1
    poll_count = 0
    while not gen_task.done():
        try:
            event = await asyncio.wait_for(progress_queue.get(), timeout=0.2)
            current_percent = event.progress if event.progress is not None else 0

            events_sent += 1
            json_data = event_to_json(event)
            logger.debug(
                f"📨 [{events_sent}] Sending SSE: {event.stage} ({event.progress}%)"
            )
            yield {"data": json_data}
            last_percent = current_percent
            await asyncio.sleep(0)

        except asyncio.TimeoutError:
            poll_count += 1
            if poll_count % 10 == 0:
                logger.trace(
                    f"⏳ Polling... (queue size: {progress_queue.qsize()}, task done: {gen_task.done()})"
                )
            continue
        except Exception as e:
            logger.error(f"❌ Error in event loop: {e}")
            break

    logger.debug(
        f"🏁 Generation task done. Draining queue (size: {progress_queue.qsize()})"
    )

    # Drain remaining events
    drain_count = 0
    while not progress_queue.empty():
        try:
            event = progress_queue.get_nowait()
            drain_count += 1
            events_sent += 1
            logger.debug(f"📨 [DRAIN {drain_count}] Sending: {event.stage}")
            yield {"data": event_to_json(event)}
        except Exception as e:
            logger.error(f"❌ Error draining queue: {e}")
            break

    logger.info(
        f"📊 SSE Stats: queued={events_queued}, sent={events_sent}, drained={drain_count}"
    )

    # Send final result or error
    if error_holder:
        logger.error(f"❌ Sending error: {error_holder[0]}")
        yield {"data": json.dumps({"stage": "error", "message": error_holder[0]})}
    elif result_holder:
        result = result_holder[0]
        logger.info(f"✅ Sending complete event with {len(result.images)} images")
        yield {
            "data": json.dumps(
                {
                    "stage": "complete",
                    "message": f"Generated {len(result.images)} image(s)",
                    "images": result.images,
                    "final_prompts": result.final_prompts,
                }
            ),
        }
    else:
        yield {"data": json.dumps({"stage": "error", "message": "Unknown error"})}


@app.get("/api/generate/stream")
async def generate_images_stream(
    prompt: str,
    count: int = 1,
    width: int = 1024,
    height: int = 1024,
    seed: Optional[int] = None,
    enhance: bool = False,
    enhance_instruction: str = "",
):
    """
    Generate images via SSE stream (GET for browser EventSource).

    Query Parameters:
        prompt: The image prompt
        count: Number of images to generate (default: 1)
        width: Image width (default: 1024)
        height: Image height (default: 1024)
        seed: Random seed (optional)
        enhance: Whether to enhance the prompt (default: false)
        enhance_instruction: Optional enhancement instruction

    Returns Server-Sent Events with JSON data.
    """
    request = GenerationRequest(
        prompt=prompt,
        count=count,
        width=width,
        height=height,
        seed=seed,
        enhance=enhance,
        enhance_instruction=enhance_instruction,
    )
    return EventSourceResponse(
        _generate_event_stream(request),
        ping=1,  # Send keepalive ping every second to prevent buffering
    )


@app.post("/api/generate")
async def generate_images_post(request: GenerationRequest):
    """
    Generate images via SSE stream (POST for programmatic use).

    Request Body:
        prompt: The image prompt
        count: Number of images to generate (default: 1)
        width: Image width (default: 1024)
        height: Image height (default: 1024)
        seed: Random seed (optional)
        enhance: Whether to enhance the prompt (default: false)
        enhance_instruction: Optional enhancement instruction

    Returns Server-Sent Events with JSON data.
    """
    return EventSourceResponse(
        _generate_event_stream(request),
        ping=1,  # Send keepalive ping every second to prevent buffering
    )


# ============================================================================
# Server Entry Point
# ============================================================================


def serve(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):
    """Start the Z-Explorer API server.

    Args:
        host: Host to bind to (default: 127.0.0.1)
        port: Port to bind to (default: 8345)
    """
    import uvicorn

    print(f"[startup] Starting Z-Explorer server on http://{host}:{port}")
    print(f"[docs] API docs at http://{host}:{port}/docs")

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )


if __name__ == "__main__":
    serve()
