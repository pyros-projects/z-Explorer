"""Model download service with progress tracking.

Provides download functionality with real-time progress updates
that can be streamed to the web UI via SSE.
"""

from dataclasses import dataclass, field
from typing import Optional, Callable

from rich.console import Console
from huggingface_hub import snapshot_download, HfApi

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
            "speed_mbps": round(self.speed_bps / 1024 / 1024, 2)
            if self.speed_bps
            else 0,
            "eta_seconds": round(self.eta_seconds) if self.eta_seconds else None,
            "error": self.error,
        }


@dataclass
class DownloadState:
    """State for tracking all downloads."""

    models_to_download: list[tuple[str, str]] = field(
        default_factory=list
    )  # (name, repo_id)
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
        # files_metadata=True is required to get file sizes!
        repo_info = api.repo_info(repo_id, files_metadata=True)

        # Get file sizes from siblings
        total_bytes = 0
        file_count = 0

        if hasattr(repo_info, "siblings") and repo_info.siblings:
            for sibling in repo_info.siblings:
                size = getattr(sibling, "size", None) or 0
                total_bytes += size
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
    import threading
    import huggingface_hub.file_download as hf_download

    progress = DownloadProgress(
        model_name=model_name,
        repo_id=repo_id,
        status="pending",
    )

    start_time = time.time()
    last_update_time = [start_time]  # Use list to allow mutation in nested function
    cumulative_bytes = [0]  # Track bytes ourselves (self.n isn't reliable)
    current_file_total = [0]  # Track current file's total size

    def emit_progress():
        if on_progress:
            on_progress(progress)

    # Get the actual tqdm class used by huggingface_hub
    original_tqdm_class = hf_download.tqdm
    original_update = original_tqdm_class.update

    def patched_tqdm_update(self, n=1):
        result = original_update(self, n)

        # Only track byte-level progress (n > 1000 bytes, total > 10KB)
        if hasattr(self, "total") and self.total and self.total > 10000 and n > 1000:
            cumulative_bytes[0] += n
            current_file_total[0] = self.total

            current_time = time.time()

            # Update progress
            progress.bytes_done = cumulative_bytes[0]
            # Use current file total if we don't have overall total
            if progress.bytes_total == 0:
                progress.bytes_total = self.total

            # Get current file from description
            if hasattr(self, "desc") and self.desc:
                progress.current_file = self.desc

            # Calculate speed and ETA based on current file
            elapsed = current_time - start_time
            if elapsed > 0 and cumulative_bytes[0] > 0:
                progress.speed_bps = cumulative_bytes[0] / elapsed
                # ETA for current file
                remaining = self.total - (
                    cumulative_bytes[0] % self.total if self.total else 0
                )
                if progress.speed_bps > 0:
                    progress.eta_seconds = remaining / progress.speed_bps

            # Rate limit updates to every 100ms
            if current_time - last_update_time[0] > 0.1:
                emit_progress()
                last_update_time[0] = current_time

        return result

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

        # Apply monkey-patch to huggingface_hub's tqdm
        original_tqdm_class.update = patched_tqdm_update

        download_complete = threading.Event()
        download_error = [None]  # Use list to allow mutation in thread

        def do_download():
            try:
                snapshot_download(
                    repo_id,
                    local_files_only=False,
                )
            except Exception as e:
                download_error[0] = str(e)
            finally:
                download_complete.set()

        # Start download in background
        download_thread = threading.Thread(target=do_download)
        download_thread.start()

        # Wait for completion, emitting periodic updates if no tqdm updates come
        dots = 0
        while not download_complete.is_set():
            download_complete.wait(timeout=0.5)
            # If no tqdm updates happened, show activity indicator
            if time.time() - last_update_time[0] > 0.4:
                dots = (dots + 1) % 4
                if progress.bytes_done == 0:  # No real progress yet
                    progress.current_file = f"Downloading{'.' * (dots + 1)}"
                    emit_progress()

        download_thread.join()

        # Restore original tqdm
        original_tqdm_class.update = original_update

        if download_error[0]:
            progress.status = "error"
            progress.error = download_error[0]
            emit_progress()
            return False

        progress.status = "complete"
        progress.bytes_done = progress.bytes_total
        progress.files_done = progress.files_total
        emit_progress()
        return True

    except Exception as e:
        # Ensure tqdm is restored even on error
        try:
            original_tqdm_class.update = original_update
        except NameError:
            pass
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

    # Image model - use repo_id as name for model-agnostic display
    if img_config.mode == LoadingMode.HF_DOWNLOAD:
        repo_id = img_config.hf_repo or DEFAULT_Z_IMAGE_REPO
        models.append((repo_id, repo_id))
    elif img_config.mode == LoadingMode.SDNQ:
        repo_id = img_config.sdnq_model or DEFAULT_SDNQ_MODEL
        models.append((repo_id, repo_id))

    # LLM - use repo_id as name for model-agnostic display
    if llm_config.mode == LLMMode.HF_DOWNLOAD:
        repo_id = llm_config.hf_repo or DEFAULT_LLM_REPO
        models.append((repo_id, repo_id))

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
    from huggingface_hub import scan_cache_dir

    models = get_models_to_download()
    result = {}

    try:
        # Get all cached repos - this is robust and doesn't depend on specific files
        cache_info = scan_cache_dir()
        cached_repos = {repo.repo_id for repo in cache_info.repos}
    except Exception:
        # If cache scan fails, assume nothing is cached
        cached_repos = set()

    for model_name, repo_id in models:
        result[model_name] = repo_id in cached_repos

    return result
