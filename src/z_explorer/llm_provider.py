"""Local LLM provider for text generation.

This module provides a local LLM for:
- Prompt enhancement
- Prompt variable generation

The LLM can be configured independently from the image model:
- z_image: Use Z-Image's text encoder (thinking Qwen - slower but no extra download)
- hf_local: Local HuggingFace model
- hf_download: Download from HuggingFace Hub (supports BNB quantized models!)
- gguf: Load from GGUF file (CPU-friendly quantized)

Set LLM_MODE and LLM_PATH/LLM_REPO environment variables to configure.

Supports any HuggingFace-compatible model including:
- Qwen (default)
- Ministral 3B (Aratako/Ministral-3-3B-Instruct-2512-TextOnly)
- BNB 4-bit quantized models (e.g., unsloth/Qwen3-4B-Instruct-2507-bnb-4bit)
- GGUF quantized models
- Any other transformers-compatible LLM
"""

import json

from rich.console import Console

console = Console(stderr=True)

# Lazy imports to avoid loading heavy libraries unless needed
_model = None
_tokenizer = None
_is_ministral_fp8 = False  # Track if we loaded a Ministral FP8 text-only model


def _is_ministral_fp8_model(model_name: str) -> bool:
    """Check if the model is a Ministral FP8 model that needs dequantization.

    Matches models like:
    - Aratako/Ministral-3-3B-Instruct-2512-TextOnly
    - Any model with 'ministral' in the name
    """
    name_lower = model_name.lower()
    return "ministral" in name_lower


def _load_ministral_fp8_model(repo: str):
    """Load a Ministral text-only FP8 model with Auto classes.

    Ministral models are stored in FP8 format and need to be dequantized
    to bfloat16 on load using FineGrainedFP8Config.
    """
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, FineGrainedFP8Config

    console.print(f"[cyan]Loading Ministral FP8 model: {repo}[/cyan]")

    tokenizer = AutoTokenizer.from_pretrained(repo, trust_remote_code=True)
    model = AutoModelForCausalLM.from_pretrained(
        repo,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        quantization_config=FineGrainedFP8Config(dequantize=True),
        trust_remote_code=True,
    )

    return model, tokenizer


def _load_model():
    """Lazy load the LLM model and tokenizer.

    Uses configuration from get_llm_config() which is independent
    from the image model configuration.
    """
    global _model, _tokenizer, _is_ministral_fp8

    if _model is not None:
        return _model, _tokenizer

    # Unload image generator first to free GPU memory
    try:
        from z_explorer import image_generator

        if image_generator._pipeline is not None:
            console.print("[dim]Unloading image model to free GPU memory...[/dim]")
            image_generator.unload_pipeline()
    except ImportError:
        pass

    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        raise ImportError(
            "Local mode requires transformers and torch. Install with: uv sync"
        )

    # Get independent LLM config
    from z_explorer.model_config import (
        LLMMode,
        get_image_model_config,
        get_llm_config,
    )

    config = get_llm_config()

    # Validate config
    is_valid, errors = config.validate()
    if not is_valid:
        console.print("[red]LLM configuration errors:[/red]")
        for err in errors:
            console.print(f"  - {err}")
        raise ValueError(
            "Invalid LLM configuration. Set LLM_MODE and LLM_PATH/LLM_REPO."
        )

    # Load based on mode
    if config.mode == LLMMode.Z_IMAGE:
        # Use Z-Image's text encoder (same as image model)
        # This requires checking the image model config
        img_config = get_image_model_config()
        _model, _tokenizer = _load_from_z_image(img_config)

    elif config.mode == LLMMode.HF_DOWNLOAD:
        # Download from HuggingFace Hub (supports BNB quantized models!)
        if _is_ministral_fp8_model(config.hf_repo):
            # Use Ministral FP8 loading (text-only, Auto classes with dequantization)
            _is_ministral_fp8 = True
            _model, _tokenizer = _load_ministral_fp8_model(config.hf_repo)
        else:
            console.print(
                f"[cyan]Loading LLM from HuggingFace: {config.hf_repo}[/cyan]"
            )

            _tokenizer = AutoTokenizer.from_pretrained(
                config.hf_repo,
                trust_remote_code=True,
            )
            _model = AutoModelForCausalLM.from_pretrained(
                config.hf_repo,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )

    elif config.mode == LLMMode.HF_LOCAL:
        # Load from local path
        if _is_ministral_fp8_model(config.hf_local_path):
            # Use Ministral FP8 loading (text-only, Auto classes with dequantization)
            _is_ministral_fp8 = True
            _model, _tokenizer = _load_ministral_fp8_model(config.hf_local_path)
        else:
            console.print(
                f"[cyan]Loading LLM from local path: {config.hf_local_path}[/cyan]"
            )

            _tokenizer = AutoTokenizer.from_pretrained(
                config.hf_local_path,
                trust_remote_code=True,
            )
            _model = AutoModelForCausalLM.from_pretrained(
                config.hf_local_path,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )

    elif config.mode == LLMMode.GGUF:
        # Load from GGUF file
        console.print(
            f"[cyan]Loading LLM from GGUF: {config.gguf_path}/{config.gguf_file}[/cyan]"
        )

        # GGUF loading uses gguf_file parameter
        _tokenizer = AutoTokenizer.from_pretrained(
            config.gguf_path,
            gguf_file=config.gguf_file,
            trust_remote_code=True,
        )
        _model = AutoModelForCausalLM.from_pretrained(
            config.gguf_path,
            gguf_file=config.gguf_file,
            device_map="auto",
            trust_remote_code=True,
        )

    else:
        raise ValueError(f"Unknown LLM mode: {config.mode}")

    console.print("[green]✓ LLM loaded successfully[/green]")
    return _model, _tokenizer


def _load_from_z_image(img_config):
    """Load LLM from Z-Image's text encoder based on image config."""
    import torch
    from transformers import AutoConfig, AutoModelForCausalLM, AutoTokenizer

    from z_explorer.model_config import DEFAULT_Z_IMAGE_REPO, LoadingMode

    if img_config.mode == LoadingMode.COMPONENTS:
        # Load from local safetensor file
        from safetensors.torch import load_file

        if not img_config.text_encoder_path:
            raise ValueError(
                "Z_IMAGE mode requires Z_IMAGE_TEXT_ENCODER for COMPONENTS mode"
            )

        console.print(
            f"[cyan]Loading LLM from Z-Image text encoder: {img_config.text_encoder_path}[/cyan]"
        )

        # Get config from HuggingFace (small JSON files)
        model_config = AutoConfig.from_pretrained(
            DEFAULT_Z_IMAGE_REPO,
            subfolder="text_encoder",
            trust_remote_code=True,
        )

        tokenizer = AutoTokenizer.from_pretrained(
            DEFAULT_Z_IMAGE_REPO,
            subfolder="tokenizer",
            trust_remote_code=True,
        )

        # Load weights from local file
        state_dict = load_file(img_config.text_encoder_path)

        model = AutoModelForCausalLM.from_config(
            model_config,
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        )
        model.load_state_dict(state_dict, strict=False)

        if torch.cuda.is_available():
            model = model.to("cuda")

    elif img_config.mode == LoadingMode.HF_LOCAL:
        # Load from local HuggingFace clone
        model_path = f"{img_config.hf_local_path}/text_encoder"
        tokenizer_path = f"{img_config.hf_local_path}/tokenizer"
        console.print(f"[cyan]Loading LLM from Z-Image HF clone: {model_path}[/cyan]")

        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_path, trust_remote_code=True
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    elif img_config.mode == LoadingMode.SDNQ:
        # Load from SDNQ model
        # IMPORTANT: Import SDNQConfig to register 'sdnq' quantization type with transformers
        from sdnq import (
            SDNQConfig,  # noqa: F401 - import registers quantization backend
        )

        console.print(f"[cyan]Loading LLM from SDNQ: {img_config.sdnq_model}[/cyan]")

        tokenizer = AutoTokenizer.from_pretrained(
            img_config.sdnq_model,
            subfolder="tokenizer",
            trust_remote_code=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            img_config.sdnq_model,
            subfolder="text_encoder",
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    else:
        # HF_DOWNLOAD - download from Z-Image repo
        console.print(
            f"[cyan]Loading LLM from Z-Image HF: {DEFAULT_Z_IMAGE_REPO}/text_encoder[/cyan]"
        )

        tokenizer = AutoTokenizer.from_pretrained(
            DEFAULT_Z_IMAGE_REPO,
            subfolder="tokenizer",
            trust_remote_code=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            DEFAULT_Z_IMAGE_REPO,
            subfolder="text_encoder",
            torch_dtype=torch.bfloat16,
            device_map="auto",
            trust_remote_code=True,
        )

    return model, tokenizer


def generate_text(
    prompt: str,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.8,
    top_k: int = 20,
) -> str:
    """Generate text using the local LLM.

    Uses Qwen3-recommended parameters for non-thinking mode:
    - temperature=0.7, top_p=0.8, top_k=20

    Args:
        prompt: The user prompt/instruction
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.7 recommended for Qwen3)
        top_p: Top-p sampling parameter (0.8 recommended for Qwen3)
        top_k: Top-k sampling parameter (20 recommended for Qwen3)

    Returns:
        Generated text response
    """
    import torch

    model, tokenizer = _load_model()

    messages = [{"role": "user", "content": prompt}]

    # Standard model inference (Qwen, Ministral, etc.)
    text = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    # Remove token_type_ids if present (Ministral FP8 models don't accept it)
    if _is_ministral_fp8 and "token_type_ids" in inputs:
        del inputs["token_type_ids"]

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    response = tokenizer.decode(
        outputs[0][inputs.input_ids.shape[1] :], skip_special_tokens=True
    )
    return response.strip()


def enhance_prompt(user_prompt: str, instruction: str = "") -> str:
    """Enhance a prompt for better image generation.

    Args:
        user_prompt: The original user prompt
        instruction: Optional enhancement instructions

    Returns:
        Enhanced prompt optimized for image generation
    """
    system_prompt = """You are an expert prompt engineer for image generation models.
Your task is to enhance the user's prompt to create more detailed, vivid, and visually
compelling descriptions that will produce stunning images.

Rules:
- Add specific details about lighting, atmosphere, style, and composition
- Maintain the core intent of the original prompt
- Keep the enhanced prompt concise but descriptive
- Output ONLY the enhanced prompt, nothing else"""

    full_prompt = f"""{system_prompt}

Original prompt: {user_prompt}
{f"Additional instructions: {instruction}" if instruction else ""}

Enhanced prompt:"""

    return generate_text(full_prompt, max_tokens=1024, temperature=0.7)


def _generate_with_outlines(prompt: str, count: int) -> list[str] | None:
    """Try to generate a JSON array using outlines for guaranteed structure.

    Returns None if outlines is not available or fails.
    """
    try:
        from outlines import generate, models

        # Get the already-loaded model and tokenizer
        model, tokenizer = _load_model()

        # Wrap in outlines
        outlines_model = models.Transformers(model, tokenizer)

        # Create a generator that forces a JSON array of strings
        generator = generate.json(outlines_model, list[str])

        # Generate with structure guarantee
        result = generator(prompt)

        if isinstance(result, list) and result:
            console.print(
                "[green]✓ Used outlines for guaranteed JSON structure[/green]"
            )
            return result

    except ImportError:
        # outlines not installed - that's fine, fall back to regular generation
        pass
    except Exception as e:
        console.print(
            f"[yellow]Outlines failed ({e}), falling back to regular generation[/yellow]"
        )

    return None


def generate_prompt_variable_values(
    variable_name: str, context_prompt: str, count: int = 20
) -> list[str]:
    """Generate values for a prompt variable using local LLM.

    The variable name itself controls what kind of values are generated.
    Name your variable descriptively to get the output you want:

    Simple values:
        __cat_breed__           → "Persian", "Siamese", "Maine Coon"
        __color__               → "crimson", "azure", "golden"
        __art_style__           → "impressionist", "cyberpunk", "watercolor"

    Detailed descriptions:
        __detailed_scene__      → Full scene descriptions
        __50_word_description__ → ~50 word descriptions
        __dramatic_lighting_scene__ → Scenes with dramatic lighting focus

    The LLM interprets the variable name directly - no magic rules.

    If `outlines` is installed, uses constrained generation for guaranteed
    valid JSON output. Otherwise falls back to regular generation + parsing.

    Args:
        variable_name: Name of the variable - this IS the instruction to the LLM
        context_prompt: The prompt where this variable will be used (for context)
        count: Number of values to generate

    Returns:
        List of generated values
    """
    # Convert underscores to spaces for natural language interpretation
    readable_name = variable_name.replace("_", " ").strip()

    prompt = f"""Generate exactly {count} values for: "{readable_name}"

Context: This will be substituted into the prompt "{context_prompt}"

The variable name tells you what to generate. Examples:
- "cat breed" → ["Scottish Fold", "Persian", "Maine Coon"]
- "detailed scene" → ["A moonlit forest with ancient oaks and a winding stream reflecting stars", "A bustling Tokyo alley at night with neon signs and rain-slicked pavement", "An abandoned lighthouse on a cliff during a violent storm"]
- "color" → ["crimson", "midnight blue", "emerald green"]

Interpret "{readable_name}" literally. Generate what it asks for.

Return ONLY a JSON array of {count} strings. No objects, no nested structures, just plain strings in an array.

JSON array:"""

    # Try outlines first (guaranteed JSON structure)
    result = _generate_with_outlines(prompt, count)
    if result:
        return result[: count + 10]

    # Fallback: regular generation + parsing
    response = generate_text(prompt, max_tokens=4096, temperature=0.7)

    # Extract JSON array from response
    try:
        start = response.find("[")
        end = response.rfind("]") + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            values = json.loads(json_str)
            if isinstance(values, list) and values:
                # Ensure all values are strings (some models return dicts)
                string_values = []
                for v in values:
                    if isinstance(v, str):
                        string_values.append(v)
                    elif isinstance(v, dict):
                        # Extract the longest string value from dict
                        # (models sometimes return {"time": "x", "location": "long description"})
                        str_vals = [val for val in v.values() if isinstance(val, str)]
                        if str_vals:
                            # Pick the longest one - usually the actual content
                            string_values.append(max(str_vals, key=len))
                        else:
                            string_values.append(str(v))
                    else:
                        string_values.append(str(v))
                return string_values[: count + 10]
    except json.JSONDecodeError:
        pass

    # Fallback: parse line by line
    console.print(
        "[yellow]Warning: Could not parse JSON, attempting line parsing[/yellow]"
    )
    lines = [
        line.strip().strip('"').strip("'").strip(",")
        for line in response.split("\n")
        if line.strip()
        and not line.strip().startswith("[")
        and not line.strip().startswith("]")
    ]

    if lines:
        return lines[: count + 10]

    console.print("[red]Warning: Failed to generate prompt variable values[/red]")
    return []


def unload_model():
    """Unload the model to free GPU memory."""
    global _model, _tokenizer, _is_ministral_fp8

    if _model is not None:
        import gc

        import torch

        del _model
        del _tokenizer
        _model = None
        _tokenizer = None
        _is_ministral_fp8 = False

        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        console.print("[dim]LLM model unloaded[/dim]")
