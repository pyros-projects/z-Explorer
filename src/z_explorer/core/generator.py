"""Unified generation workflow for Z-Explorer.

This module contains the core generation logic used by both CLI and Server modes.
The `generate()` function is the single source of truth for image generation.
"""

import random
import re
from typing import Optional, Callable

from loguru import logger

from z_explorer.core.types import (
    GenerationRequest,
    GenerationResult,
    ProgressEvent,
)

# Type alias for progress callback
ProgressCallback = Callable[[ProgressEvent], None]


def _emit(
    on_progress: Optional[ProgressCallback],
    stage: str,
    message: str,
    progress: Optional[int] = None,
    data: Optional[dict] = None,
) -> None:
    """Emit a progress event if callback is provided."""
    logger.debug(f"📣 Emitting: stage={stage}, msg={message}, progress={progress}")
    if on_progress:
        on_progress(ProgressEvent(
            stage=stage,
            message=message,
            progress=progress,
            data=data,
        ))
    else:
        logger.warning("⚠️ No progress callback provided!")


def _substitute_variables(
    prompt: str,
    prompt_vars: dict,
    on_progress: Optional[ProgressCallback] = None,
    generate_missing: bool = True,
) -> str:
    """Substitute __variable__ patterns in prompt.
    
    Args:
        prompt: The prompt with __variable__ patterns
        prompt_vars: Dict of variable name -> PromptVars object
        on_progress: Optional progress callback
        generate_missing: If True, generate missing variables using LLM
        
    Returns:
        Prompt with all variables substituted
    """
    logger.info(f"[vars] Substituting variables in: {prompt}")
    logger.debug(f"[vars] Available variables: {list(prompt_vars.keys())}")
    
    pattern = r'(__[a-zA-Z0-9_\-/]+__)'
    matches = re.findall(pattern, prompt)
    
    logger.debug(f"[vars] Found matches: {matches}")
    
    if not matches:
        logger.debug("[vars] No variables to substitute")
        return prompt
    
    substituted = prompt
    
    for match in matches:
        if match in prompt_vars:
            # Variable exists - pick random value
            var = prompt_vars[match]
            if var.values:
                replacement = random.choice(var.values)
                substituted = substituted.replace(match, replacement, 1)
                _emit(on_progress, "substituting", f"Substituted {match} → {replacement}")
        elif generate_missing:
            # Variable doesn't exist - generate it
            raw_name = match.strip('_')
            _emit(on_progress, "var_missing", f"Missing variable: {match}")
            
            try:
                from z_explorer.llm_provider import generate_prompt_variable_values
                from z_explorer.models.prompt_vars import save_prompt_var, load_prompt_vars
                
                _emit(on_progress, "var_generating", f"Generating values for {match}...")
                values = generate_prompt_variable_values(raw_name, prompt, count=20)
                
                if values:
                    _emit(on_progress, "var_saved", f"Generated {len(values)} values for {match}")
                    save_prompt_var(
                        variable_name=raw_name,
                        description=f"Auto-generated values for {raw_name}",
                        values=values,
                    )
                    
                    # Pick random value
                    replacement = random.choice(values)
                    substituted = substituted.replace(match, replacement, 1)
                    _emit(on_progress, "substituting", f"Substituted {match} → {replacement}")
                    
                    # Reload prompt_vars
                    prompt_vars.update(load_prompt_vars())
            except Exception as e:
                _emit(on_progress, "error", f"Failed to generate variable {match}: {e}")
    
    return substituted


def _enhance_prompt(
    prompt: str,
    instruction: str = "",
    on_progress: Optional[ProgressCallback] = None,
) -> str:
    """Enhance a prompt using the LLM.
    
    Args:
        prompt: The base prompt to enhance
        instruction: Optional enhancement instruction
        on_progress: Optional progress callback
        
    Returns:
        Enhanced prompt
    """
    _emit(on_progress, "enhancing", f"Enhancing prompt...")
    
    try:
        from z_explorer.llm_provider import enhance_prompt
        
        enhanced = enhance_prompt(prompt, instruction)
        # Show the full enhanced result
        _emit(on_progress, "enhanced", enhanced)
        return enhanced
    except Exception as e:
        _emit(on_progress, "error", f"Enhancement failed: {e}")
        return prompt


def generate(
    request: GenerationRequest,
    on_progress: Optional[ProgressCallback] = None,
) -> GenerationResult:
    """Main generation workflow - the single source of truth.
    
    This function implements the two-phase generation approach:
    1. Phase 1 (LLM): Generate all prompts with variable substitution and enhancement
    2. Phase 2 (Image): Generate all images from the prepared prompts
    
    Args:
        request: Generation parameters
        on_progress: Optional callback for progress updates
        
    Returns:
        GenerationResult with image paths and metadata
    """
    logger.info("=" * 60)
    logger.info(f"[generate] GENERATE START: prompt={request.prompt[:50]}...")
    logger.info(f"   count={request.count}, size={request.width}x{request.height}")
    logger.info(f"   enhance={request.enhance}, seed={request.seed}")
    logger.info(f"   on_progress callback: {'YES' if on_progress else 'NO'}")
    logger.info("=" * 60)
    
    _emit(on_progress, "starting", "Initializing generation pipeline...", 5)
    
    result = GenerationResult(success=False)
    
    try:
        # Load prompt variables
        from z_explorer.models.prompt_vars import load_prompt_vars
        logger.debug("[vars] Loading prompt variables...")
        prompt_vars = load_prompt_vars()
        logger.info(f"[vars] Loaded {len(prompt_vars)} variables: {list(prompt_vars.keys())}")
        _emit(on_progress, "loading_vars", f"Loaded {len(prompt_vars)} variables", 10)
        
        # Parse enhancement from prompt (> syntax)
        base_prompt = request.prompt
        enhancement_instruction = request.enhancement_instruction
        has_enhancement = request.enhance
        
        if " > " in request.prompt:
            parts = request.prompt.split(" > ", 1)
            base_prompt = parts[0].strip()
            enhancement_instruction = parts[1].strip() if len(parts) > 1 else ""
            has_enhancement = True
            logger.debug(f"📝 Parsed enhancement: base={base_prompt}, instruction={enhancement_instruction}")
        
        # ========================================
        # PHASE 1: Generate all prompts (LLM phase)
        # ========================================
        logger.info("🔷 PHASE 1: Generating prompts...")
        _emit(on_progress, "phase1_complete", f"Phase 1: Generating {request.count} prompt(s)...", 15)
        
        generated_prompts = []
        
        for i in range(request.count):
            # Substitute variables (fresh random values each time)
            current_prompt = _substitute_variables(
                base_prompt,
                prompt_vars,
                on_progress=on_progress,
                generate_missing=True,
            )
            
            # Reload prompt_vars in case new ones were generated
            if i == 0:
                prompt_vars = load_prompt_vars()
            
            # Apply enhancement if requested
            if has_enhancement:
                full_prompt = current_prompt
                if enhancement_instruction:
                    full_prompt = f"{current_prompt}\n\nEnhancement instruction: {enhancement_instruction}"
                current_prompt = _enhance_prompt(
                    full_prompt,
                    enhancement_instruction,
                    on_progress=on_progress,
                )
            
            generated_prompts.append(current_prompt)
        
        result.final_prompts = generated_prompts
        
        # Unload LLM to free GPU memory before image generation
        if request.count > 1 or has_enhancement:
            try:
                from z_explorer.llm_provider import unload_model
                unload_model()
                _emit(on_progress, "llm_unloaded", "LLM unloaded to free GPU memory", 35)
            except Exception:
                pass
        
        # ========================================
        # PHASE 2: Generate all images (Image phase)
        # ========================================
        _emit(on_progress, "loading_image_model", "Phase 2: Loading image model...", 40)
        
        from z_explorer.image_generator import generate_image
        
        for i, prompt in enumerate(generated_prompts):
            # Calculate base progress for this image (40-95% range split among images)
            base_pct = 40 + int((i / request.count) * 55)
            per_image_range = 55 // max(request.count, 1)
            
            # Show the full final prompt being used
            _emit(
                on_progress,
                "final_prompt",
                prompt,
                base_pct,
                {"prompt": prompt, "index": i + 1, "total": request.count},
            )
            
            _emit(
                on_progress,
                "generating_image",
                f"Generating image {i + 1}/{request.count}...",
                base_pct,
                {"prompt": prompt[:100]},
            )
            
            # Determine seed
            seed = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)
            
            try:
                # Progress callback for step-by-step updates during diffusion
                def step_progress(step: int, total: int, preview):
                    step_pct = base_pct + int((step / total) * per_image_range)
                    _emit(
                        on_progress,
                        "diffusion_step",
                        f"Image {i + 1}/{request.count}: step {step}/{total}",
                        step_pct,
                    )
                
                image, path = generate_image(
                    prompt,
                    width=request.width,
                    height=request.height,
                    seed=seed,
                    progress_callback=step_progress,
                )
                
                # Save prompt to a text file alongside the image
                prompt_path = path.rsplit('.', 1)[0] + '.txt'
                try:
                    with open(prompt_path, 'w', encoding='utf-8') as f:
                        f.write(prompt)
                    logger.info(f"📝 Saved prompt to: {prompt_path}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to save prompt file: {e}")
                
                result.images.append(path)
                result.seeds_used.append(seed)
                _emit(
                    on_progress,
                    "image_saved",
                    f"💾 Saved: {path}",
                    base_pct + per_image_range,
                    {"path": path, "seed": seed, "prompt": prompt},
                )
            except Exception as e:
                result.errors.append(f"Image {i + 1} failed: {e}")
                _emit(on_progress, "error", f"Image {i + 1} failed: {e}")
        
        # ========================================
        # DONE
        # ========================================
        result.success = len(result.images) > 0
        _emit(
            on_progress,
            "complete",
            f"Generated {len(result.images)} image(s)!",
            100,
            {"total": len(result.images)},
        )
        
    except Exception as e:
        result.errors.append(str(e))
        _emit(on_progress, "error", f"Generation failed: {e}")
    
    return result

