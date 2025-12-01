"""First-run setup wizard for model configuration.

This wizard guides users through configuring their model sources with three options:
1. Quick Start (Beginner) - Downloads optimized quantized models automatically
2. Custom Setup - Configure your own model paths and options
3. Full Quality - Download full precision models (requires more VRAM)

After setup, models are downloaded and verified before first use.
"""

import sys
from pathlib import Path
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from z_explorer.model_config import (
    LoadingMode,
    LLMMode,
    save_config,
    get_image_model_config,
    get_llm_config,
    DEFAULT_Z_IMAGE_REPO,
    DEFAULT_SDNQ_MODEL,
    DEFAULT_LLM_REPO,
    DEFAULT_LLM_REPO_QUANTIZED,
)

console = Console()


# =============================================================================
# Preset Configurations
# =============================================================================

PRESETS = {
    "quick_start": {
        "name": "Quick Start (Recommended for beginners)",
        "description": "Downloads optimized quantized models. Low VRAM (~12GB), fast inference.",
        "image_mode": LoadingMode.SDNQ,
        "image_sdnq_model": DEFAULT_SDNQ_MODEL,
        "llm_mode": LLMMode.HF_DOWNLOAD,
        "llm_repo": DEFAULT_LLM_REPO_QUANTIZED,
    },
    "full_quality": {
        "name": "Full Quality",
        "description": "Downloads full precision models. Best quality, requires more VRAM (~24GB).",
        "image_mode": LoadingMode.HF_DOWNLOAD,
        "image_hf_repo": DEFAULT_Z_IMAGE_REPO,
        "llm_mode": LLMMode.Z_IMAGE,  # Use Z-Image's text encoder
        "llm_repo": None,
    },
    "custom": {
        "name": "Custom Setup",
        "description": "Configure your own model paths and options.",
    },
}


# =============================================================================
# UI Helpers
# =============================================================================


def print_welcome():
    """Print the welcome banner."""
    welcome_text = Text()
    welcome_text.append("Welcome to ", style="bold")
    welcome_text.append("Z-Explorer", style="bold cyan")
    welcome_text.append(" Setup!\n\n", style="bold")
    welcome_text.append(
        "This wizard will help you configure your model sources.\n"
        "Your choices will be saved to a .env file for future runs."
    )

    console.print(Panel(welcome_text, title="Setup Wizard", border_style="cyan"))
    console.print()


def print_preset_info():
    """Print information about presets."""
    console.print("[bold]Choose your setup mode:[/bold]\n")

    for key, preset in PRESETS.items():
        icon = "🚀" if key == "quick_start" else "💪" if key == "full_quality" else "🔧"
        console.print(f"  {icon} [cyan]{preset['name']}[/cyan]")
        console.print(f"     [dim]{preset['description']}[/dim]\n")


# =============================================================================
# Validation Helpers
# =============================================================================


def validate_path(path: str) -> bool:
    """Validate that a path exists."""
    return Path(path).exists()


def validate_safetensor(path: str) -> bool:
    """Validate that a safetensor file exists."""
    p = Path(path)
    return p.exists() and p.suffix == ".safetensors"


def validate_hf_directory(path: str) -> bool:
    """Validate that a path is a HuggingFace model directory."""
    p = Path(path)
    if not p.exists():
        return False
    # Check for model_index.json (pipeline) or config.json (model)
    return (p / "model_index.json").exists() or (p / "config.json").exists()


# =============================================================================
# Setup Steps
# =============================================================================


def ask_preset() -> str:
    """Ask user which preset to use.

    Returns:
        Preset key: 'quick_start', 'full_quality', or 'custom'
    """
    print_preset_info()

    choice = questionary.select(
        "Select setup mode:",
        choices=[
            questionary.Choice(
                "🚀 Quick Start (Recommended for beginners)", value="quick_start"
            ),
            questionary.Choice("🔧 Custom Setup", value="custom"),
            questionary.Choice("💪 Full Quality", value="full_quality"),
        ],
    ).ask()

    if choice is None:
        console.print("[red]Setup cancelled.[/red]")
        sys.exit(1)

    return choice


def ask_custom_image_model() -> tuple[LoadingMode, dict]:
    """Ask user how they want to load the image model (custom setup).

    Returns:
        Tuple of (LoadingMode, config dict with paths)
    """
    console.print("\n[bold]Image Generation Model (Z-Image-Turbo)[/bold]")
    console.print(f"Default: {DEFAULT_Z_IMAGE_REPO}\n")

    choice = questionary.select(
        "How would you like to load the image model?",
        choices=[
            questionary.Choice(
                "Download from HuggingFace (full precision, ~15GB)", value="hf_download"
            ),
            questionary.Choice(
                "Download SDNQ quantized model (recommended, ~6GB)", value="sdnq"
            ),
            questionary.Choice(
                "Use local HuggingFace clone (offline mode)", value="hf_local"
            ),
            questionary.Choice(
                "Use separate component files (ComfyUI-style)", value="components"
            ),
        ],
    ).ask()

    if choice is None:
        console.print("[red]Setup cancelled.[/red]")
        sys.exit(1)

    config = {}

    if choice == "hf_download":
        mode = LoadingMode.HF_DOWNLOAD
        console.print(f"[green]Will download from {DEFAULT_Z_IMAGE_REPO}[/green]")
        console.print("[dim]Note: First run will download ~15GB of model files[/dim]\n")

    elif choice == "sdnq":
        mode = LoadingMode.SDNQ
        config["sdnq_model"] = DEFAULT_SDNQ_MODEL
        console.print(f"[green]Will download SDNQ model: {DEFAULT_SDNQ_MODEL}[/green]")
        console.print("[dim]Note: First run will download ~6GB of model files[/dim]\n")

    elif choice == "hf_local":
        mode = LoadingMode.HF_LOCAL
        path = questionary.path(
            "Path to local HuggingFace model directory:",
            validate=lambda p: validate_hf_directory(p)
            or "Not a valid HuggingFace model directory",
        ).ask()

        if path is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)

        config["hf_local"] = str(Path(path).resolve())
        console.print(f"[green]Will use: {config['hf_local']}[/green]\n")

    elif choice == "components":
        mode = LoadingMode.COMPONENTS
        console.print("\n[dim]Enter paths to your safetensor files:[/dim]\n")

        # Transformer
        transformer = questionary.path(
            "Transformer model (.safetensors):",
            validate=lambda p: validate_safetensor(p)
            or "File must be a .safetensors file",
        ).ask()
        if transformer is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["transformer"] = str(Path(transformer).resolve())

        # Text encoder
        text_encoder = questionary.path(
            "Text encoder (.safetensors):",
            validate=lambda p: validate_safetensor(p)
            or "File must be a .safetensors file",
        ).ask()
        if text_encoder is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["text_encoder"] = str(Path(text_encoder).resolve())

        # VAE
        vae = questionary.path(
            "VAE (.safetensors):",
            validate=lambda p: validate_safetensor(p)
            or "File must be a .safetensors file",
        ).ask()
        if vae is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["vae"] = str(Path(vae).resolve())

        console.print("\n[green]Component paths configured![/green]")
        console.print(
            "[dim]Note: Model architecture configs will be downloaded from HuggingFace[/dim]\n"
        )

    return mode, config


def ask_custom_llm() -> tuple[LLMMode, dict]:
    """Ask user how they want to load the LLM (custom setup).

    Returns:
        Tuple of (LLMMode, config dict)
    """
    console.print("\n[bold]LLM for Prompt Enhancement[/bold]")
    console.print(f"Default: {DEFAULT_LLM_REPO}\n")

    choice = questionary.select(
        "How would you like to load the LLM?",
        choices=[
            questionary.Choice(
                "Use Z-Image's text encoder (no extra download, but slower)",
                value="z_image",
            ),
            questionary.Choice(
                "Download BNB 4-bit quantized model (fast, recommended)",
                value="hf_download_bnb",
            ),
            questionary.Choice(
                "Download from HuggingFace (custom repo)", value="hf_download"
            ),
            questionary.Choice("Use local model path", value="hf_local"),
            questionary.Choice("Use GGUF file (CPU-friendly)", value="gguf"),
        ],
    ).ask()

    if choice is None:
        console.print("[red]Setup cancelled.[/red]")
        sys.exit(1)

    config = {}

    if choice == "z_image":
        mode = LLMMode.Z_IMAGE
        console.print("[green]Will use Z-Image's text encoder[/green]")
        console.print(
            "[dim]Note: This uses 'thinking' mode which is slower for variable generation[/dim]\n"
        )

    elif choice == "hf_download_bnb":
        mode = LLMMode.HF_DOWNLOAD
        config["repo"] = DEFAULT_LLM_REPO_QUANTIZED
        console.print(f"[green]Will download: {DEFAULT_LLM_REPO_QUANTIZED}[/green]")
        console.print("[dim]Note: BNB 4-bit quantized for fast inference[/dim]\n")

    elif choice == "hf_download":
        mode = LLMMode.HF_DOWNLOAD
        repo = questionary.text(
            "HuggingFace repo name:",
            default=DEFAULT_LLM_REPO,
        ).ask()
        if repo is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["repo"] = repo
        console.print(f"[green]Will download from: {repo}[/green]\n")

    elif choice == "hf_local":
        mode = LLMMode.HF_LOCAL
        path = questionary.path(
            "Path to local model directory:",
            validate=lambda p: validate_path(p) or "Path does not exist",
        ).ask()
        if path is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["path"] = str(Path(path).resolve())
        console.print(f"[green]Will use: {config['path']}[/green]\n")

    elif choice == "gguf":
        mode = LLMMode.GGUF
        path = questionary.path(
            "Path to GGUF file or HF repo:",
        ).ask()
        if path is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["path"] = str(Path(path).resolve()) if Path(path).exists() else path

        gguf_file = questionary.text(
            "GGUF filename (e.g., model-Q4_K_M.gguf):",
        ).ask()
        if gguf_file is None:
            console.print("[red]Setup cancelled.[/red]")
            sys.exit(1)
        config["gguf_file"] = gguf_file
        console.print(
            f"[green]Will use GGUF: {config['path']}/{config['gguf_file']}[/green]\n"
        )

    return mode, config


# =============================================================================
# Model Download & Verification
# =============================================================================


def download_models(
    image_mode: LoadingMode, image_config: dict, llm_mode: LLMMode, llm_config: dict
) -> bool:
    """Download models that need downloading.

    Returns:
        True if all downloads successful
    """
    console.print("\n[bold cyan]Downloading models...[/bold cyan]\n")

    downloads_needed = []

    # Check what needs downloading
    if image_mode == LoadingMode.HF_DOWNLOAD:
        downloads_needed.append(("Image model (Z-Image-Turbo)", DEFAULT_Z_IMAGE_REPO))
    elif image_mode == LoadingMode.SDNQ:
        downloads_needed.append(
            ("Image model (SDNQ)", image_config.get("sdnq_model", DEFAULT_SDNQ_MODEL))
        )

    if llm_mode == LLMMode.HF_DOWNLOAD:
        repo = llm_config.get("repo", DEFAULT_LLM_REPO)
        downloads_needed.append(("LLM model", repo))

    if not downloads_needed:
        console.print("[green]No downloads needed - using local files.[/green]\n")
        return True

    # Show what will be downloaded
    console.print("[dim]The following models will be downloaded:[/dim]")
    for name, repo in downloads_needed:
        console.print(f"  - {name}: [cyan]{repo}[/cyan]")
    console.print()

    # Confirm download
    confirm = questionary.confirm(
        "Start download now?",
        default=True,
    ).ask()

    if not confirm:
        console.print(
            "[yellow]Download skipped. Models will download on first use.[/yellow]"
        )
        return True  # Not a failure, just deferred

    # Perform downloads
    try:
        from huggingface_hub import snapshot_download

        for name, repo in downloads_needed:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(f"[cyan]Downloading {name}...", total=None)

                try:
                    # Use snapshot_download for caching
                    snapshot_download(
                        repo,
                        local_files_only=False,
                    )
                    progress.update(
                        task, description=f"[green]✓ {name} downloaded[/green]"
                    )
                except Exception as e:
                    progress.update(
                        task, description=f"[red]✗ {name} failed: {e}[/red]"
                    )
                    raise

        console.print("\n[green]All models downloaded successfully![/green]\n")
        return True

    except Exception as e:
        console.print(f"\n[red]Download failed: {e}[/red]\n")
        return False


def verify_pipeline() -> tuple[bool, Optional[str]]:
    """Verify that the pipeline can be created with current config.

    Returns:
        Tuple of (success, error_message)
    """
    console.print("[bold cyan]Verifying configuration...[/bold cyan]\n")

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Verify image model config
            task = progress.add_task(
                "[cyan]Checking image model configuration...", total=None
            )
            img_config = get_image_model_config()
            is_valid, errors = img_config.validate()
            if not is_valid:
                return False, f"Image model config errors: {', '.join(errors)}"
            progress.update(
                task, description="[green]✓ Image model configuration valid[/green]"
            )

            # Verify LLM config
            task2 = progress.add_task("[cyan]Checking LLM configuration...", total=None)
            llm_config = get_llm_config()
            is_valid, errors = llm_config.validate()
            if not is_valid:
                return False, f"LLM config errors: {', '.join(errors)}"
            progress.update(
                task2, description="[green]✓ LLM configuration valid[/green]"
            )

            # Try to import the pipeline class (doesn't load weights)
            task3 = progress.add_task(
                "[cyan]Checking diffusers installation...", total=None
            )
            try:
                from diffusers import ZImagePipeline  # noqa: F401

                progress.update(
                    task3,
                    description="[green]✓ Diffusers ZImagePipeline available[/green]",
                )
            except ImportError as e:
                return False, f"Diffusers not properly installed: {e}"

        console.print("\n[green]Configuration verified successfully![/green]\n")
        return True, None

    except Exception as e:
        return False, str(e)


def handle_verification_failure(error: str) -> str:
    """Handle a verification failure.

    Returns:
        'continue', 'redo', or 'exit'
    """
    console.print(f"\n[red]Verification failed:[/red] {error}\n")

    choice = questionary.select(
        "What would you like to do?",
        choices=[
            questionary.Choice(
                "Continue anyway (may fail at runtime)", value="continue"
            ),
            questionary.Choice("Redo setup", value="redo"),
            questionary.Choice("Exit", value="exit"),
        ],
    ).ask()

    return choice or "exit"


# =============================================================================
# Main Wizard Flow
# =============================================================================


def confirm_and_save(
    image_mode: LoadingMode, image_config: dict, llm_mode: LLMMode, llm_config: dict
) -> bool:
    """Show summary and confirm save.

    Returns:
        True if saved successfully
    """
    console.print("\n" + "=" * 50)
    console.print("[bold]Configuration Summary[/bold]\n")

    # Image model summary
    console.print("[cyan]Image Model:[/cyan]")
    if image_mode == LoadingMode.HF_DOWNLOAD:
        console.print("  Mode: Download from HuggingFace")
        console.print(f"  Repo: {DEFAULT_Z_IMAGE_REPO}")
    elif image_mode == LoadingMode.SDNQ:
        console.print("  Mode: SDNQ Quantized")
        console.print(f"  Model: {image_config.get('sdnq_model', DEFAULT_SDNQ_MODEL)}")
    elif image_mode == LoadingMode.HF_LOCAL:
        console.print("  Mode: Local HuggingFace clone")
        console.print(f"  Path: {image_config.get('hf_local')}")
    elif image_mode == LoadingMode.COMPONENTS:
        console.print("  Mode: Component files")
        console.print(f"  Transformer: {image_config.get('transformer')}")
        console.print(f"  Text Encoder: {image_config.get('text_encoder')}")
        console.print(f"  VAE: {image_config.get('vae')}")

    # LLM summary
    console.print("\n[cyan]LLM:[/cyan]")
    if llm_mode == LLMMode.Z_IMAGE:
        console.print("  Mode: Z-Image text encoder")
        console.print("  [dim](Uses Z-Image's built-in Qwen)[/dim]")
    elif llm_mode == LLMMode.HF_DOWNLOAD:
        console.print("  Mode: Download from HuggingFace")
        console.print(f"  Repo: {llm_config.get('repo', DEFAULT_LLM_REPO)}")
    elif llm_mode == LLMMode.HF_LOCAL:
        console.print("  Mode: Local path")
        console.print(f"  Path: {llm_config.get('path')}")
    elif llm_mode == LLMMode.GGUF:
        console.print("  Mode: GGUF file")
        console.print(f"  Path: {llm_config.get('path')}")
        console.print(f"  File: {llm_config.get('gguf_file')}")

    console.print()

    # Confirm
    confirm = questionary.confirm(
        "Save this configuration?",
        default=True,
    ).ask()

    if not confirm:
        console.print("[yellow]Configuration not saved.[/yellow]")
        return False

    # Save to .env
    env_path = save_config(
        image_mode=image_mode,
        image_hf_local=image_config.get("hf_local"),
        image_transformer=image_config.get("transformer"),
        image_text_encoder=image_config.get("text_encoder"),
        image_vae=image_config.get("vae"),
        image_sdnq_model=image_config.get("sdnq_model"),
        llm_mode=llm_mode,
        llm_repo=llm_config.get("repo"),
        llm_path=llm_config.get("path"),
        llm_gguf_file=llm_config.get("gguf_file"),
    )

    console.print(f"\n[green]Configuration saved to: {env_path}[/green]")
    console.print("[dim]You can edit this file manually or run setup again.[/dim]\n")

    return True


def run_wizard() -> bool:
    """Run the complete setup wizard.

    Returns:
        True if setup completed successfully
    """
    while True:
        print_welcome()

        # Step 1: Ask for preset
        preset_key = ask_preset()

        if preset_key == "custom":
            # Custom setup
            image_mode, image_config = ask_custom_image_model()
            llm_mode, llm_config = ask_custom_llm()
        else:
            # Use preset
            preset = PRESETS[preset_key]
            console.print(f"\n[green]Using preset: {preset['name']}[/green]\n")

            image_mode = preset["image_mode"]
            image_config = {}
            if "image_sdnq_model" in preset:
                image_config["sdnq_model"] = preset["image_sdnq_model"]

            llm_mode = preset["llm_mode"]
            llm_config = {}
            if preset.get("llm_repo"):
                llm_config["repo"] = preset["llm_repo"]

        # Step 2: Confirm and save
        if not confirm_and_save(image_mode, image_config, llm_mode, llm_config):
            continue  # Redo setup

        # Step 3: Download models
        download_success = download_models(
            image_mode, image_config, llm_mode, llm_config
        )

        if not download_success:
            choice = handle_verification_failure("Model download failed")
            if choice == "redo":
                continue
            elif choice == "exit":
                sys.exit(1)
            # else: continue anyway

        # Step 4: Verify configuration
        verify_success, verify_error = verify_pipeline()

        if not verify_success:
            choice = handle_verification_failure(verify_error)
            if choice == "redo":
                continue
            elif choice == "exit":
                sys.exit(1)
            # else: continue anyway

        # Success!
        console.print(
            "[bold green]Setup complete! You're ready to generate images.[/bold green]\n"
        )
        return True


def run_wizard_if_needed() -> bool:
    """Run setup wizard if not configured, otherwise skip.

    Returns:
        True if wizard ran, False if skipped (already configured)
    """
    from z_explorer.model_config import is_configured

    if is_configured():
        return False

    console.print(
        "[yellow]No model configuration found. Starting setup wizard...[/yellow]\n"
    )
    return run_wizard()


if __name__ == "__main__":
    # Allow running wizard directly
    run_wizard()
