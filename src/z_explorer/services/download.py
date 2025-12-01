"""Model download service with progress tracking.

Provides download functionality with real-time progress updates
that can be streamed to the web UI via SSE.
"""

import os
import asyncio
from dataclasses import dataclass, field
from typing import Optional, Callable
from pathlib import Path

from rich.console import Console
from huggingface_hub import snapshot_download, HfApi
from huggingface_hub.utils import tqdm as hf_tqdm

console = Console(stderr=True)


@dataclass
class DownloadProgress:
    """Progress update for a download."""
    model_name: str
    repo_id: str
    status: str  # "pending", "downloading", "complete", "error"
    current_file: Optional[str] = None
    files_done: int = 0
    files_total: int = 0
    bytes_done: int = 0
    bytes_total: int = 0
    speed_bps: float = 0
    eta_seconds: Optional[float] = None
    error: Optional[str] = None
    
    @property
    def progress_percent(self) -> float:
        if self.bytes_total > 0:
            return (self.bytes_done / self.bytes_total) * 100
        elif self.files_total > 0:
            return (self.files_done / self.files_total) * 100
        return 0
    
    def to_dict(self) -> dict:
        return {
            "model_name": self.model_name,
            "repo_id": self.repo_id,
            "status": self.status,
            "current_file": self.current_file,
            "files_done": self.files_done,
            "files_total": self.files_total,
            "bytes_done": self.bytes_done,
            "bytes_total": self.bytes_total,
            "progress_percent": round(self.progress_percent, 1),
            "speed_mbps": round(self.speed_bps / 1024 / 1024, 2) if self.speed_bps else 0,
            "eta_seconds": round(self.eta_seconds) if self.eta_seconds else None,
            "error": self.error,
        }


@dataclass  
class DownloadState:
    """State for tracking all downloads."""
    models_to_download: list[tuple[str, str]] = field(default_factory=list)  # (name, repo_id)
    current_model_index: int = 0
    current_progress: Optional[DownloadProgress] = None
    is_complete: bool = False
    has_error: bool = False


# Global download state (for SSE streaming)
_download_state: Optional[DownloadState] = None
_progress_callback: Optional[Callable[[DownloadProgress], None]] = None


def get_repo_size(repo_id: str) -> tuple[int, int]:
    """Get total size and file count of a repo.
    
    Returns:
        Tuple of (total_bytes, file_count)
    """
    try:
        api = HfApi()
        repo_info = api.repo_info(repo_id)
        
        # Get file sizes from siblings
        total_bytes = 0
        file_count = 0
        
        if hasattr(repo_info, 'siblings') and repo_info.siblings:
            for sibling in repo_info.siblings:
                if hasattr(sibling, 'size') and sibling.size:
                    total_bytes += sibling.size
                file_count += 1
                
        return total_bytes, file_count
    except Exception as e:
        console.print(f"[yellow]Could not get repo size: {e}[/yellow]")
        return 0, 0


def download_model_with_progress(
    model_name: str,
    repo_id: str,
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
) -> bool:
    """Download a model with progress tracking.
    
    Args:
        model_name: Human-readable name for the model
        repo_id: HuggingFace repo ID
        on_progress: Callback for progress updates
        
    Returns:
        True if download succeeded
    """
    import time
    
    progress = DownloadProgress(
        model_name=model_name,
        repo_id=repo_id,
        status="pending",
    )
    
    def emit_progress():
        if on_progress:
            on_progress(progress)
    
    try:
        # Get repo info for total size
        progress.status = "checking"
        progress.current_file = "Checking repository..."
        emit_progress()
        
        total_bytes, file_count = get_repo_size(repo_id)
        progress.bytes_total = total_bytes
        progress.files_total = file_count
        
        progress.status = "downloading"
        emit_progress()
        
        # Track download progress
        start_time = time.time()
        last_update_time = start_time
        
        # Custom tqdm class to capture progress
        class ProgressTracker(hf_tqdm):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._last_n = 0
                
            def update(self, n=1):
                super().update(n)
                nonlocal progress, last_update_time
                
                current_time = time.time()
                
                # Update progress
                if hasattr(self, 'total') and self.total:
                    progress.bytes_done = self.n
                    progress.bytes_total = self.total
                    
                    # Calculate speed and ETA
                    elapsed = current_time - start_time
                    if elapsed > 0 and self.n > 0:
                        progress.speed_bps = self.n / elapsed
                        remaining_bytes = self.total - self.n
                        if progress.speed_bps > 0:
                            progress.eta_seconds = remaining_bytes / progress.speed_bps
                
                # Get current file from description if available
                if hasattr(self, 'desc') and self.desc:
                    progress.current_file = self.desc
                
                # Rate limit updates to every 100ms
                if current_time - last_update_time > 0.1:
                    emit_progress()
                    last_update_time = current_time
        
        # Download with progress tracking
        # Note: snapshot_download doesn't directly support custom tqdm,
        # but we can use environment variables and the default tqdm behavior
        
        # For now, use a simpler approach - periodic polling
        import threading
        
        download_complete = threading.Event()
        download_error = None
        
        def do_download():
            nonlocal download_error
            try:
                snapshot_download(
                    repo_id,
                    local_files_only=False,
                )
            except Exception as e:
                download_error = str(e)
            finally:
                download_complete.set()
        
        # Start download in background
        download_thread = threading.Thread(target=do_download)
        download_thread.start()
        
        # Poll for progress (simplified - just show activity)
        dots = 0
        while not download_complete.is_set():
            dots = (dots + 1) % 4
            progress.current_file = f"Downloading{'.' * dots}"
            emit_progress()
            download_complete.wait(timeout=0.5)
        
        download_thread.join()
        
        if download_error:
            progress.status = "error"
            progress.error = download_error
            emit_progress()
            return False
        
        progress.status = "complete"
        progress.bytes_done = progress.bytes_total
        progress.files_done = progress.files_total
        emit_progress()
        return True
        
    except Exception as e:
        progress.status = "error"
        progress.error = str(e)
        emit_progress()
        return False


def get_models_to_download() -> list[tuple[str, str]]:
    """Get list of models that need to be downloaded based on current config.
    
    Returns:
        List of (model_name, repo_id) tuples
    """
    from z_explorer.model_config import (
        get_image_model_config,
        get_llm_config,
        LoadingMode,
        LLMMode,
        DEFAULT_Z_IMAGE_REPO,
        DEFAULT_SDNQ_MODEL,
        DEFAULT_LLM_REPO,
    )
    
    models = []
    
    img_config = get_image_model_config()
    llm_config = get_llm_config()
    
    # Image model
    if img_config.mode == LoadingMode.HF_DOWNLOAD:
        models.append(("Z-Image-Turbo", img_config.hf_repo or DEFAULT_Z_IMAGE_REPO))
    elif img_config.mode == LoadingMode.SDNQ:
        models.append(("Z-Image-Turbo (SDNQ)", img_config.sdnq_model or DEFAULT_SDNQ_MODEL))
    
    # LLM
    if llm_config.mode == LLMMode.HF_DOWNLOAD:
        models.append(("LLM (Qwen)", llm_config.hf_repo or DEFAULT_LLM_REPO))
    
    return models


def download_all_models(
    on_progress: Optional[Callable[[DownloadProgress], None]] = None,
) -> bool:
    """Download all configured models with progress tracking.
    
    Args:
        on_progress: Callback for progress updates
        
    Returns:
        True if all downloads succeeded
    """
    models = get_models_to_download()
    
    if not models:
        return True
    
    all_success = True
    
    for model_name, repo_id in models:
        success = download_model_with_progress(
            model_name=model_name,
            repo_id=repo_id,
            on_progress=on_progress,
        )
        if not success:
            all_success = False
            break
    
    return all_success


def check_models_downloaded() -> dict[str, bool]:
    """Check which models are already downloaded.
    
    Returns:
        Dict of model_name -> is_downloaded
    """
    from huggingface_hub import try_to_load_from_cache
    
    models = get_models_to_download()
    result = {}
    
    for model_name, repo_id in models:
        try:
            # Try to find the model in cache
            cached = try_to_load_from_cache(repo_id, "config.json")
            result[model_name] = cached is not None
        except Exception:
            result[model_name] = False
    
    return result

