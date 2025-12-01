"""Local image generator using Z-Image-Turbo.

This module provides image generation using the Z-Image-Turbo model
via the diffusers library. Supports three loading modes:

1. HuggingFace Download - Download from HuggingFace Hub (default)
2. HuggingFace Local - Use a local clone of the HF repository
3. Components - Use individual safetensor files (ComfyUI-style)

No ComfyUI or external services required!
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from rich.console import Console
from PIL import Image

console = Console(stderr=True)

# Lazy load the pipeline
_pipeline = None


def _get_output_dir() -> Path:
    """Get the output directory for generated images."""
    output_dir = Path(os.getenv("LOCAL_OUTPUT_DIR", "./output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _unload_llm_if_needed():
    """Unload LLM to free GPU memory if loaded."""
    try:
        from z_explorer import llm_provider
        if llm_provider._model is not None:
            console.print("[dim]Unloading LLM to free GPU memory...[/dim]")
            llm_provider.unload_model()
    except ImportError:
        pass

def _load_pipeline_sdnq(model_path: str):
    """Load pipeline from SDNQ.
    
    Args:
        model_path: Path to model
    """
    import torch
    import diffusers
    from sdnq import SDNQConfig
    pipe = diffusers.ZImagePipeline.from_pretrained(model_path, torch_dtype=torch.bfloat16)
    pipe.enable_model_cpu_offload()
    return pipe


def _load_pipeline_hf(model_path: str, quantize: bool = True):
    """Load pipeline from HuggingFace (download or local clone).

    Args:
        model_path: HF repo name or local path
        quantize: Whether to use 4-bit quantization
    """
    import torch
    from diffusers import ZImagePipeline, PipelineQuantizationConfig

    console.print(f"[cyan]Loading Z-Image-Turbo from: {model_path}[/cyan]")

    if quantize:
        quant_config = PipelineQuantizationConfig(
            quant_backend="bitsandbytes_4bit",
            quant_kwargs={
                "load_in_4bit": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_compute_dtype": torch.bfloat16,
            },
        )
    else:
        quant_config = None

    pipeline = ZImagePipeline.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16,
        quantization_config=quant_config,
        low_cpu_mem_usage=True,
    )

    return pipeline


def _convert_comfy_to_diffusers_key(key: str) -> str:
    """Convert a ComfyUI safetensor key to diffusers format.

    ComfyUI uses different naming conventions than diffusers:
    - ComfyUI: .attention.k_norm.weight -> Diffusers: .attention.norm_k.weight
    - ComfyUI: .attention.q_norm.weight -> Diffusers: .attention.norm_q.weight
    - ComfyUI: .attention.out.weight -> Diffusers: .attention.to_out.0.weight
    - ComfyUI: final_layer. -> Diffusers: all_final_layer.2-1.
    - ComfyUI: x_embedder. -> Diffusers: all_x_embedder.2-1.

    Based on: https://huggingface.co/Comfy-Org/z_image_turbo/blob/main/z_image_convert_original_to_comfy.py
    """
    # Key conversions (ComfyUI -> Diffusers, reverse of the original script)
    conversions = [
        (".attention.k_norm.weight", ".attention.norm_k.weight"),
        (".attention.q_norm.weight", ".attention.norm_q.weight"),
        (".attention.out.weight", ".attention.to_out.0.weight"),
        (".attention.out.bias", ".attention.to_out.0.bias"),
        ("final_layer.", "all_final_layer.2-1."),
        ("x_embedder.", "all_x_embedder.2-1."),
    ]

    for comfy_pattern, diffusers_pattern in conversions:
        if comfy_pattern in key:
            key = key.replace(comfy_pattern, diffusers_pattern)

    return key


def _split_qkv_tensor(qkv_tensor, dim: int):
    """Split a concatenated QKV tensor into separate Q, K, V tensors.

    ComfyUI stores Q, K, V as a single concatenated tensor.
    Diffusers expects separate to_q, to_k, to_v weights.

    Args:
        qkv_tensor: Tensor of shape [3*dim, dim] containing [Q; K; V]
        dim: Model dimension (e.g., 3840 for Z-Image)

    Returns:
        Tuple of (q_tensor, k_tensor, v_tensor)
    """
    # QKV is concatenated along dimension 0: [Q, K, V]
    q = qkv_tensor[:dim]
    k = qkv_tensor[dim:2*dim]
    v = qkv_tensor[2*dim:]
    return q, k, v


def _load_pipeline_components(
    transformer_path: str,
    text_encoder_path: str,
    vae_path: str,
    quantize: bool = False,  # Note: quantization not supported in components mode
):
    """Load pipeline from individual safetensor components.

    This enables ComfyUI-style model management where components
    are stored as separate safetensor files.

    Handles key conversion from ComfyUI format to diffusers format:
    - Converts attention norm keys (k_norm -> norm_k, q_norm -> norm_q)
    - Splits concatenated QKV weights into separate Q, K, V
    - Converts layer naming conventions

    Args:
        transformer_path: Path to transformer safetensor
        text_encoder_path: Path to text encoder safetensor
        vae_path: Path to VAE safetensor
        quantize: Not used (quantization requires HF_DOWNLOAD mode)
    """
    import torch
    from safetensors import safe_open
    from safetensors.torch import load_file
    from accelerate import init_empty_weights
    from accelerate.utils import set_module_tensor_to_device
    from diffusers import (
        ZImagePipeline,
        FlowMatchEulerDiscreteScheduler,
        AutoencoderKL,
    )
    from diffusers.models.transformers.transformer_z_image import ZImageTransformer2DModel
    from transformers import AutoTokenizer, AutoModelForCausalLM, AutoConfig

    console.print("[cyan]Loading Z-Image-Turbo from components...[/cyan]")
    console.print(f"  [dim]Transformer: {transformer_path}[/dim]")
    console.print(f"  [dim]Text Encoder: {text_encoder_path}[/dim]")
    console.print(f"  [dim]VAE: {vae_path}[/dim]")

    # We need configs from HuggingFace for model architecture
    # These are small JSON files that define the model structure
    from z_explorer.model_config import DEFAULT_Z_IMAGE_REPO

    # Load scheduler (no weights needed, just config)
    console.print("  [dim]Loading scheduler...[/dim]")
    scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(
        DEFAULT_Z_IMAGE_REPO,
        subfolder="scheduler",
    )

    # Load VAE from local safetensor file
    # Use from_single_file() with FLUX/Z-Image VAE config (16 latent channels)
    # The config parameter tells diffusers the correct architecture
    console.print("  [dim]Loading VAE...[/dim]")
    vae = AutoencoderKL.from_single_file(
        vae_path,
        config=DEFAULT_Z_IMAGE_REPO,
        subfolder="vae",
        torch_dtype=torch.bfloat16,
    )

    # Load tokenizer (no weights, just config and vocab)
    console.print("  [dim]Loading tokenizer...[/dim]")
    tokenizer = AutoTokenizer.from_pretrained(
        DEFAULT_Z_IMAGE_REPO,
        subfolder="tokenizer",
        trust_remote_code=True,
    )

    # Load text encoder (Qwen) from local safetensor
    # Only download config (small JSON), not the 4GB weights!
    console.print("  [dim]Loading text encoder...[/dim]")

    # Get config only from HuggingFace (just JSON files, no weights)
    te_config = AutoConfig.from_pretrained(
        DEFAULT_Z_IMAGE_REPO,
        subfolder="text_encoder",
        trust_remote_code=True,
    )

    # Load weights from local safetensor file
    te_state = load_file(text_encoder_path)

    # Create model from config (no weights downloaded from HF!)
    # Note: from_config doesn't support direct quantization, but the pipeline
    # will handle memory efficiently with bfloat16
    text_encoder = AutoModelForCausalLM.from_config(
        te_config,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True,
    )
    text_encoder.load_state_dict(te_state, strict=False)

    # Load transformer from local safetensor file using diffusion-pipe pattern:
    # 1. Load config from HuggingFace (just JSON, ~10KB)
    # 2. Create empty model shell
    # 3. Load weights tensor-by-tensor from local file
    console.print("  [dim]Loading transformer...[/dim]")

    # Get transformer config from HuggingFace (just the JSON config file)
    transformer_config = ZImageTransformer2DModel.load_config(
        DEFAULT_Z_IMAGE_REPO,
        subfolder="transformer",
    )

    # Create empty model shell (no memory allocated for weights yet)
    with init_empty_weights():
        transformer = ZImageTransformer2DModel.from_config(transformer_config)

    # Load weights tensor-by-tensor from local safetensor file
    # This avoids loading everything into memory at once
    # ComfyUI uses different key naming than diffusers, so we convert
    model_dim = transformer_config.get("dim", 3840)  # Z-Image default

    with safe_open(transformer_path, framework="pt", device="cpu") as f:
        for key in f.keys():
            tensor = f.get_tensor(key)

            # Handle QKV split: ComfyUI concatenates Q, K, V into single tensor
            if ".attention.qkv.weight" in key:
                # Split QKV into separate Q, K, V tensors
                q, k, v = _split_qkv_tensor(tensor, model_dim)

                # Get the base key (e.g., "transformer_blocks.0.attention")
                base_key = key.replace(".qkv.weight", "")

                # Set Q, K, V separately
                for suffix, split_tensor in [(".to_q.weight", q), (".to_k.weight", k), (".to_v.weight", v)]:
                    diffusers_key = base_key + suffix
                    set_module_tensor_to_device(
                        transformer,
                        diffusers_key,
                        device='cpu',
                        dtype=torch.bfloat16,
                        value=split_tensor
                    )
            else:
                # Convert ComfyUI key to diffusers key
                diffusers_key = _convert_comfy_to_diffusers_key(key)

                # Convert to bfloat16 for memory efficiency
                set_module_tensor_to_device(
                    transformer,
                    diffusers_key,
                    device='cpu',
                    dtype=torch.bfloat16,
                    value=tensor
                )

    console.print("  [dim]Transformer loaded successfully[/dim]")

    # Assemble pipeline
    console.print("  [dim]Assembling pipeline...[/dim]")
    pipeline = ZImagePipeline(
        scheduler=scheduler,
        vae=vae,
        text_encoder=text_encoder,
        tokenizer=tokenizer,
        transformer=transformer,
    )

    return pipeline


def _load_pipeline():
    """Lazy load the Z-Image pipeline based on configuration.

    Automatically unloads the LLM to free GPU memory,
    since both models cannot fit in VRAM simultaneously.
    """
    global _pipeline

    if _pipeline is not None:
        return _pipeline

    # Unload LLM first to free GPU memory
    _unload_llm_if_needed()

    try:
        import torch
        from diffusers import ZImagePipeline
    except ImportError as e:
        # Check if diffusers is installed but missing ZImagePipeline
        try:
            import diffusers
            diffusers_version = getattr(diffusers, '__version__', 'unknown')
            raise ImportError(
                f"ZImagePipeline not found in diffusers {diffusers_version}.\n"
                "This model requires the latest diffusers from GitHub (not PyPI).\n\n"
                "If you installed via 'uvx z-explorer', you need to install from source instead:\n"
                "  uvx --from git+https://github.com/pyros-projects/z-Explorer z-explorer\n\n"
                "Or clone and run locally:\n"
                "  git clone https://github.com/pyros-projects/z-Explorer && cd z-Explorer\n"
                "  uv sync && uv run z-explorer"
            ) from e
        except ImportError:
            raise ImportError(
                "diffusers and torch are required but not installed.\n"
                "Install from source:\n"
                "  git clone https://github.com/pyros-projects/z-Explorer && cd z-Explorer\n"
                "  uv sync && uv run z-explorer"
            ) from e

    # Get configuration
    from z_explorer.model_config import get_image_model_config, LoadingMode

    config = get_image_model_config()

    # Validate configuration
    is_valid, errors = config.validate()
    if not is_valid:
        console.print("[red]Model configuration errors:[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise ValueError("Invalid model configuration. Run setup wizard to configure.")

    # Load based on mode
    if config.mode == LoadingMode.HF_DOWNLOAD:
        _pipeline = _load_pipeline_hf(config.hf_repo)
    elif config.mode == LoadingMode.SDNQ:
        _pipeline = _load_pipeline_sdnq(config.sdnq_model)
    elif config.mode == LoadingMode.HF_LOCAL:
        _pipeline = _load_pipeline_hf(config.hf_local_path)

    elif config.mode == LoadingMode.COMPONENTS:
        _pipeline = _load_pipeline_components(
            transformer_path=config.transformer_path,
            text_encoder_path=config.text_encoder_path,
            vae_path=config.vae_path,
        )

    # Move to GPU if available
    if torch.cuda.is_available():
        _pipeline.to("cuda")
        console.print(f"[green]Z-Image-Turbo loaded on CUDA[/green]")
    else:
        console.print("[yellow]CUDA not available, using CPU (will be slow)[/yellow]")
        _pipeline.to("cpu")

    return _pipeline


def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_steps: int = 9,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, Image.Image], None]] = None,
) -> tuple[Image.Image, str]:
    """Generate an image using Z-Image-Turbo.

    Args:
        prompt: The text prompt for image generation
        width: Output image width (default 1024)
        height: Output image height (default 1024)
        num_steps: Number of inference steps (default 9, actually 8 DiT forwards)
        seed: Random seed for reproducibility (None for random)
        output_path: Custom output path (auto-generated if None)
        progress_callback: Optional callback(step, total, latent_preview)

    Returns:
        Tuple of (PIL Image, output file path)
    """
    import torch

    pipe = _load_pipeline()

    # Set up generator with seed
    device = "cuda" if torch.cuda.is_available() else "cpu"
    if seed is None:
        seed = torch.randint(0, 2**32 - 1, (1,)).item()
    generator = torch.Generator(device).manual_seed(seed)

    console.print(f"[dim]Seed: {seed}[/dim]")
    console.print(f"[cyan]Generating {width}x{height} image...[/cyan]")

    # Set up step callback if progress_callback provided
    def step_callback(pipe, step, timestep, callback_kwargs):
        if progress_callback:
            progress_callback(step + 1, num_steps, None)
            # Longer sleep to ensure events are flushed to browser
            import time
            time.sleep(0.15)  # 150ms pause between steps
        return callback_kwargs

    # Generate image
    # Note: Z-Image-Turbo uses guidance_scale=0.0 (it's distilled)
    result = pipe(
        prompt=prompt,
        height=height,
        width=width,
        num_inference_steps=num_steps,
        guidance_scale=0.0,  # Must be 0 for Turbo model
        generator=generator,
        callback_on_step_end=step_callback if progress_callback else None,
    )

    image = result.images[0]

    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = _get_output_dir()
        output_path = str(output_dir / f"zimage_{timestamp}_{seed}.png")

    # Save image
    image.save(output_path)
    console.print(f"[green]Image saved to: {output_path}[/green]")

    # Save prompt to companion .txt file
    prompt_path = Path(output_path).with_suffix('.txt')
    try:
        prompt_path.write_text(prompt, encoding='utf-8')
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save prompt: {e}[/yellow]")

    return image, output_path


def generate_image_with_preview(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_steps: int = 9,
    seed: Optional[int] = None,
    output_path: Optional[str] = None,
) -> tuple[Image.Image, str]:
    """Generate an image with Rich live preview in terminal.

    Same as generate_image but shows progress in terminal.
    """
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

    import torch

    pipe = _load_pipeline()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if seed is None:
        seed = torch.randint(0, 2**32 - 1, (1,)).item()
    generator = torch.Generator(device).manual_seed(seed)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task(f"[cyan]Generating image (seed: {seed})...", total=num_steps)

        def callback(pipe, step, timestep, callback_kwargs):
            progress.update(task, completed=step + 1)
            return callback_kwargs

        result = pipe(
            prompt=prompt,
            height=height,
            width=width,
            num_inference_steps=num_steps,
            guidance_scale=0.0,
            generator=generator,
            callback_on_step_end=callback,
        )

    image = result.images[0]

    # Determine output path
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = _get_output_dir()
        output_path = str(output_dir / f"zimage_{timestamp}_{seed}.png")

    image.save(output_path)
    console.print(f"[green]Image saved to: {output_path}[/green]")

    # Save prompt to companion .txt file
    prompt_path = Path(output_path).with_suffix('.txt')
    try:
        prompt_path.write_text(prompt, encoding='utf-8')
    except Exception as e:
        console.print(f"[yellow]Warning: Could not save prompt: {e}[/yellow]")

    return image, output_path


def unload_pipeline():
    """Unload the pipeline to free GPU memory."""
    global _pipeline

    if _pipeline is not None:
        import gc
        import torch

        del _pipeline
        _pipeline = None

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        console.print("[dim]Z-Image pipeline unloaded[/dim]")


def get_gpu_memory_info() -> dict:
    """Get GPU memory information."""
    try:
        import torch
        if torch.cuda.is_available():
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            device_name = torch.cuda.get_device_name(0)
            return {
                "device_name": device_name,
                "allocated_gb": round(allocated, 2),
                "reserved_gb": round(reserved, 2),
                "total_gb": round(total, 2),
                "free_gb": round(total - reserved, 2),
            }
    except Exception:
        pass
    return {"error": "CUDA not available"}
