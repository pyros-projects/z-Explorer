"""Model configuration and loading strategy management.

This module handles flexible model loading from three sources:
1. HuggingFace Hub download (default for new users)
2. Local HuggingFace clone (for offline use)
3. ComfyUI-style components (individual safetensor files)

Configuration is stored in environment variables (via .env file).
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv, set_key
from rich.console import Console

console = Console(stderr=True)

# Load .env file if it exists
load_dotenv()

# Runtime override storage (for UI-based model switching)
_override_config: dict | None = None


class LoadingMode(str, Enum):
    """Image model loading strategy."""
    HF_DOWNLOAD = "hf_download"  # Download from HuggingFace Hub
    HF_LOCAL = "hf_local"        # Use local HuggingFace clone
    COMPONENTS = "components"    # Use individual safetensor files
    SDNQ = "sdnq"                # Use SDNQ quantized model


class LLMMode(str, Enum):
    """LLM loading strategy - independent from image model.

    Supports any HuggingFace-compatible LLM (Qwen, Llama, etc.)
    """
    Z_IMAGE = "z_image"          # Use Z-Image's text encoder (thinking Qwen - slower)
    HF_LOCAL = "hf_local"        # Local HuggingFace clone
    HF_DOWNLOAD = "hf_download"  # Download from HuggingFace Hub
    GGUF = "gguf"                # Load from GGUF file


# Default HuggingFace repositories
DEFAULT_Z_IMAGE_REPO = "Tongyi-MAI/Z-Image-Turbo"
DEFAULT_SDNQ_MODEL = "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32"
# Fast LLM options for variable generation
DEFAULT_LLM_REPO = "Qwen/Qwen3-4B"
# BNB 4-bit quantized LLM for low VRAM (beginner-friendly)
DEFAULT_LLM_REPO_QUANTIZED = "unsloth/Qwen3-4B-Instruct-2507-bnb-4bit"


@dataclass
class ImageModelConfig:
    """Configuration for the image generation model."""
    mode: LoadingMode

    # For HF_DOWNLOAD mode
    hf_repo: str = DEFAULT_Z_IMAGE_REPO
    # For SDNQ mode
    sdnq_model: str = DEFAULT_SDNQ_MODEL
    # For HF_LOCAL mode
    hf_local_path: Optional[str] = None

    # For COMPONENTS mode
    transformer_path: Optional[str] = None
    text_encoder_path: Optional[str] = None
    vae_path: Optional[str] = None

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the configuration.

        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []

        if self.mode == LoadingMode.HF_DOWNLOAD:
            # No validation needed - will download on first use
            pass

        elif self.mode == LoadingMode.SDNQ:
            # No validation needed - will download on first use
            pass

        elif self.mode == LoadingMode.HF_LOCAL:
            if not self.hf_local_path:
                errors.append("HF_LOCAL mode requires Z_IMAGE_HF path")
            elif not Path(self.hf_local_path).exists():
                errors.append(f"Z_IMAGE_HF path does not exist: {self.hf_local_path}")
            else:
                # Check for required files in HF directory
                hf_path = Path(self.hf_local_path)
                required = ["model_index.json"]
                for req in required:
                    if not (hf_path / req).exists():
                        errors.append(f"Missing {req} in {self.hf_local_path}")

        elif self.mode == LoadingMode.COMPONENTS:
            if not self.transformer_path:
                errors.append("COMPONENTS mode requires Z_IMAGE_TRANSFORMER path")
            elif not Path(self.transformer_path).exists():
                errors.append(f"Transformer not found: {self.transformer_path}")

            if not self.text_encoder_path:
                errors.append("COMPONENTS mode requires Z_IMAGE_TEXT_ENCODER path")
            elif not Path(self.text_encoder_path).exists():
                errors.append(f"Text encoder not found: {self.text_encoder_path}")

            if not self.vae_path:
                errors.append("COMPONENTS mode requires Z_IMAGE_VAE path")
            elif not Path(self.vae_path).exists():
                errors.append(f"VAE not found: {self.vae_path}")

        return len(errors) == 0, errors


@dataclass
class LLMConfig:
    """Configuration for the LLM - independent from image model.

    Supports any HuggingFace-compatible model (Qwen, Llama, Mistral, etc.)
    including BNB quantized models from unsloth.
    """
    mode: LLMMode

    # For HF_DOWNLOAD mode
    hf_repo: str = DEFAULT_LLM_REPO

    # For HF_LOCAL mode
    hf_local_path: Optional[str] = None

    # For GGUF mode
    gguf_path: Optional[str] = None
    gguf_file: Optional[str] = None  # Filename within repo or path

    def validate(self) -> tuple[bool, list[str]]:
        """Validate the configuration."""
        errors = []

        if self.mode == LLMMode.Z_IMAGE:
            # Uses Z-Image's text encoder - validated by ImageModelConfig
            pass

        elif self.mode == LLMMode.HF_DOWNLOAD:
            # No validation needed - will download on first use
            pass

        elif self.mode == LLMMode.HF_LOCAL:
            if not self.hf_local_path:
                errors.append("LLM_MODE=hf_local requires LLM_PATH")
            elif not Path(self.hf_local_path).exists():
                errors.append(f"LLM_PATH does not exist: {self.hf_local_path}")

        elif self.mode == LLMMode.GGUF:
            if not self.gguf_path:
                errors.append("LLM_MODE=gguf requires LLM_PATH (repo or local path)")
            elif not self.gguf_file:
                errors.append("LLM_MODE=gguf requires LLM_GGUF_FILE")
            # If local path, check it exists
            elif Path(self.gguf_path).exists() and self.gguf_file:
                full_path = Path(self.gguf_path) / self.gguf_file
                if not full_path.exists():
                    errors.append(f"GGUF file not found: {full_path}")

        return len(errors) == 0, errors


def get_image_model_config() -> ImageModelConfig:
    """Get image model configuration from environment variables.

    Environment variables:
        Z_IMAGE_MODE: Loading mode (hf_download, hf_local, components, sdnq)
        Z_IMAGE_HF: Path to local HuggingFace clone
        Z_IMAGE_TRANSFORMER: Path to transformer safetensor
        Z_IMAGE_TEXT_ENCODER: Path to text encoder safetensor
        Z_IMAGE_VAE: Path to VAE safetensor
        Z_IMAGE_SDNQ: SDNQ model repo (default: Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32)
        Z_IMAGE_PATH: Legacy - treated as HF repo or local path
    """
    # Determine mode
    mode_str = os.getenv("Z_IMAGE_MODE", "").lower()

    # Legacy support: if Z_IMAGE_PATH is set, use it
    legacy_path = os.getenv("Z_IMAGE_PATH")

    # Check for component paths
    transformer = os.getenv("Z_IMAGE_TRANSFORMER")
    text_encoder = os.getenv("Z_IMAGE_TEXT_ENCODER")
    vae = os.getenv("Z_IMAGE_VAE")
    hf_local = os.getenv("Z_IMAGE_HF")
    sdnq_model = os.getenv("Z_IMAGE_SDNQ", DEFAULT_SDNQ_MODEL)

    # Auto-detect mode if not explicitly set
    if not mode_str:
        if transformer and text_encoder and vae:
            mode_str = LoadingMode.COMPONENTS
        elif hf_local:
            mode_str = LoadingMode.HF_LOCAL
        elif legacy_path:
            # Could be HF repo name or local path
            if Path(legacy_path).exists():
                mode_str = LoadingMode.HF_LOCAL
                hf_local = legacy_path
            else:
                mode_str = LoadingMode.HF_DOWNLOAD
        else:
            mode_str = LoadingMode.HF_DOWNLOAD

    # Parse mode
    try:
        mode = LoadingMode(mode_str)
    except ValueError:
        console.print(f"[yellow]Invalid Z_IMAGE_MODE '{mode_str}', defaulting to hf_download[/yellow]")
        mode = LoadingMode.HF_DOWNLOAD

    return ImageModelConfig(
        mode=mode,
        hf_repo=legacy_path if legacy_path and not Path(legacy_path).exists() else DEFAULT_Z_IMAGE_REPO,
        sdnq_model=sdnq_model,
        hf_local_path=hf_local,
        transformer_path=transformer,
        text_encoder_path=text_encoder.strip() if text_encoder else None,  # Strip whitespace
        vae_path=vae,
    )


def get_llm_config() -> LLMConfig:
    """Get LLM configuration from environment variables.

    Supports any HuggingFace-compatible LLM including BNB quantized models.

    Environment variables:
        LLM_MODE: Loading mode (z_image, hf_local, hf_download, gguf)
        LLM_PATH: Path to local model or HF repo name
        LLM_REPO: HuggingFace repo (default: Qwen/Qwen3-4B)
        LLM_GGUF_FILE: GGUF filename (for gguf mode)

    If LLM_MODE is not set, defaults to z_image (uses Z-Image's text encoder).
    """
    mode_str = os.getenv("LLM_MODE", "").lower()
    llm_path = os.getenv("LLM_PATH")
    llm_repo = os.getenv("LLM_REPO", DEFAULT_LLM_REPO)
    gguf_file = os.getenv("LLM_GGUF_FILE")

    # Auto-detect mode if not explicitly set
    if not mode_str:
        if llm_path:
            # Check if it's a GGUF file
            if gguf_file or (llm_path and llm_path.endswith(".gguf")):
                mode_str = LLMMode.GGUF
            elif Path(llm_path).exists():
                mode_str = LLMMode.HF_LOCAL
            else:
                # Assume it's a HF repo name
                mode_str = LLMMode.HF_DOWNLOAD
                llm_repo = llm_path
        else:
            # Default: use Z-Image's text encoder
            mode_str = LLMMode.Z_IMAGE

    # Parse mode
    try:
        mode = LLMMode(mode_str)
    except ValueError:
        console.print(f"[yellow]Invalid LLM_MODE '{mode_str}', defaulting to z_image[/yellow]")
        mode = LLMMode.Z_IMAGE

    return LLMConfig(
        mode=mode,
        hf_repo=llm_repo,
        hf_local_path=llm_path if mode == LLMMode.HF_LOCAL else None,
        gguf_path=llm_path if mode == LLMMode.GGUF else None,
        gguf_file=gguf_file,
    )


def is_configured() -> bool:
    """Check if models are configured (not first run).

    Returns True if either:
    - Z_IMAGE_MODE or LLM_MODE is explicitly set
    - Any model path environment variable is set
    """
    indicators = [
        "Z_IMAGE_MODE",
        "Z_IMAGE_HF",
        "Z_IMAGE_TRANSFORMER",
        "Z_IMAGE_PATH",
        "LLM_MODE",
        "LLM_PATH",
        "LLM_REPO",
    ]
    return any(os.getenv(var) for var in indicators)


def get_env_file_path() -> Path:
    """Get the path to the .env file."""
    # Check for .env in current directory first, then home directory
    cwd_env = Path.cwd() / ".env"
    if cwd_env.exists():
        return cwd_env

    # Default to current directory
    return cwd_env


def save_config(
    image_mode: LoadingMode,
    image_hf_local: Optional[str] = None,
    image_transformer: Optional[str] = None,
    image_text_encoder: Optional[str] = None,
    image_vae: Optional[str] = None,
    image_sdnq_model: Optional[str] = None,
    llm_mode: Optional[LLMMode] = None,
    llm_repo: Optional[str] = None,
    llm_path: Optional[str] = None,
    llm_gguf_file: Optional[str] = None,
) -> Path:
    """Save configuration to .env file.

    Args:
        image_mode: Image model loading mode
        image_hf_local: Path for HF_LOCAL mode
        image_transformer: Path for COMPONENTS mode
        image_text_encoder: Path for COMPONENTS mode
        image_vae: Path for COMPONENTS mode
        image_sdnq_model: SDNQ model repo for SDNQ mode
        llm_mode: LLM loading mode (optional, defaults to z_image)
        llm_repo: HuggingFace repo for LLM
        llm_path: Local path for LLM
        llm_gguf_file: GGUF filename for LLM

    Returns:
        Path to the saved .env file
    """
    env_path = get_env_file_path()

    # Create file if it doesn't exist
    if not env_path.exists():
        env_path.touch()

    # Save image model config
    set_key(str(env_path), "Z_IMAGE_MODE", image_mode.value)

    if image_mode == LoadingMode.HF_LOCAL and image_hf_local:
        set_key(str(env_path), "Z_IMAGE_HF", image_hf_local)

    elif image_mode == LoadingMode.SDNQ:
        if image_sdnq_model:
            set_key(str(env_path), "Z_IMAGE_SDNQ", image_sdnq_model)

    elif image_mode == LoadingMode.COMPONENTS:
        if image_transformer:
            set_key(str(env_path), "Z_IMAGE_TRANSFORMER", image_transformer)
        if image_text_encoder:
            set_key(str(env_path), "Z_IMAGE_TEXT_ENCODER", image_text_encoder)
        if image_vae:
            set_key(str(env_path), "Z_IMAGE_VAE", image_vae)

    # Save LLM config
    if llm_mode:
        set_key(str(env_path), "LLM_MODE", llm_mode.value)

        if llm_mode == LLMMode.HF_DOWNLOAD and llm_repo:
            set_key(str(env_path), "LLM_REPO", llm_repo)

        elif llm_mode == LLMMode.HF_LOCAL and llm_path:
            set_key(str(env_path), "LLM_PATH", llm_path)

        elif llm_mode == LLMMode.GGUF:
            if llm_path:
                set_key(str(env_path), "LLM_PATH", llm_path)
            if llm_gguf_file:
                set_key(str(env_path), "LLM_GGUF_FILE", llm_gguf_file)

    # Reload environment
    load_dotenv(env_path, override=True)

    return env_path


# ============================================================================
# Runtime Override Functions (for UI-based model switching)
# ============================================================================


def set_override_config(
    image_mode: str | None = None,
    image_repo: str | None = None,
    image_path: str | None = None,
    llm_mode: str | None = None,
    llm_repo: str | None = None,
    llm_path: str | None = None,
) -> None:
    """Set runtime override configuration.

    These overrides take precedence over .env settings until cleared.
    Pass None to keep current value, or explicit value to override.
    """
    global _override_config

    if _override_config is None:
        _override_config = {}

    if image_mode is not None:
        _override_config["image_mode"] = image_mode
    if image_repo is not None:
        _override_config["image_repo"] = image_repo
    if image_path is not None:
        _override_config["image_path"] = image_path
    if llm_mode is not None:
        _override_config["llm_mode"] = llm_mode
    if llm_repo is not None:
        _override_config["llm_repo"] = llm_repo
    if llm_path is not None:
        _override_config["llm_path"] = llm_path


def clear_override_config() -> None:
    """Clear all runtime overrides, reverting to .env configuration."""
    global _override_config
    _override_config = None


def get_override_config() -> dict | None:
    """Get current override configuration."""
    return _override_config


def get_active_image_config() -> ImageModelConfig:
    """Get active image model configuration (overrides take precedence).

    Returns:
        ImageModelConfig with overrides applied if set, otherwise from .env
    """
    global _override_config

    # If no overrides, return standard config
    if not _override_config:
        return get_image_model_config()

    # Build config with overrides
    override_mode = _override_config.get("image_mode")
    override_repo = _override_config.get("image_repo")
    override_path = _override_config.get("image_path")

    # Start with env-based config
    base_config = get_image_model_config()

    # Apply overrides
    if override_mode:
        try:
            mode = LoadingMode(override_mode)
        except ValueError:
            mode = base_config.mode
    else:
        mode = base_config.mode

    return ImageModelConfig(
        mode=mode,
        hf_repo=override_repo if override_repo else base_config.hf_repo,
        sdnq_model=base_config.sdnq_model,
        hf_local_path=override_path if override_path else base_config.hf_local_path,
        transformer_path=base_config.transformer_path,
        text_encoder_path=base_config.text_encoder_path,
        vae_path=base_config.vae_path,
    )


def get_active_llm_config() -> LLMConfig:
    """Get active LLM configuration (overrides take precedence).

    Returns:
        LLMConfig with overrides applied if set, otherwise from .env
    """
    global _override_config

    # If no overrides, return standard config
    if not _override_config:
        return get_llm_config()

    # Build config with overrides
    override_mode = _override_config.get("llm_mode")
    override_repo = _override_config.get("llm_repo")
    override_path = _override_config.get("llm_path")

    # Start with env-based config
    base_config = get_llm_config()

    # Apply overrides
    if override_mode:
        try:
            mode = LLMMode(override_mode)
        except ValueError:
            mode = base_config.mode
    else:
        mode = base_config.mode

    return LLMConfig(
        mode=mode,
        hf_repo=override_repo if override_repo else base_config.hf_repo,
        hf_local_path=override_path if override_path else base_config.hf_local_path,
        gguf_path=base_config.gguf_path,
        gguf_file=base_config.gguf_file,
    )


def print_config():
    """Print current configuration for debugging."""
    img_config = get_image_model_config()
    llm_config = get_llm_config()

    console.print("\n[bold]Image Model Configuration:[/bold]")
    console.print(f"  Mode: [cyan]{img_config.mode.value}[/cyan]")

    if img_config.mode == LoadingMode.HF_DOWNLOAD:
        console.print(f"  HF Repo: {img_config.hf_repo}")
    elif img_config.mode == LoadingMode.SDNQ:
        console.print(f"  SDNQ Model: {img_config.sdnq_model}")
    elif img_config.mode == LoadingMode.HF_LOCAL:
        console.print(f"  Local Path: {img_config.hf_local_path}")
    elif img_config.mode == LoadingMode.COMPONENTS:
        console.print(f"  Transformer: {img_config.transformer_path}")
        console.print(f"  Text Encoder: {img_config.text_encoder_path}")
        console.print(f"  VAE: {img_config.vae_path}")

    console.print("\n[bold]LLM Configuration:[/bold]")
    console.print(f"  Mode: [cyan]{llm_config.mode.value}[/cyan]")

    if llm_config.mode == LLMMode.Z_IMAGE:
        console.print("  [dim]Using Z-Image's text encoder (thinking Qwen - slower)[/dim]")
    elif llm_config.mode == LLMMode.HF_DOWNLOAD:
        console.print(f"  HF Repo: {llm_config.hf_repo}")
    elif llm_config.mode == LLMMode.HF_LOCAL:
        console.print(f"  Local Path: {llm_config.hf_local_path}")
    elif llm_config.mode == LLMMode.GGUF:
        console.print(f"  GGUF Path: {llm_config.gguf_path}")
        console.print(f"  GGUF File: {llm_config.gguf_file}")

    # Validate both
    img_valid, img_errors = img_config.validate()
    llm_valid, llm_errors = llm_config.validate()

    all_errors = img_errors + llm_errors
    if all_errors:
        console.print("\n[red]Configuration Errors:[/red]")
        for err in all_errors:
            console.print(f"  - {err}")
    else:
        console.print("\n[green]Configuration valid![/green]")
