# Implementation Plan: Prompt Manipulation Operators (Latent Syntax)

**Status:** Draft
**Date:** 2025-12-03
**Target:** `z-Explorer` Core Architecture

---

## 1. Executive Summary

This document outlines the technical roadmap for implementing the "Latent Syntax" operators (`%`, `|`, `+`, `@`, etc.) in Z-Explorer.

The goal is to transform the application from a simple **Text-to-Image** tool into a **Latent Space Synthesizer**, allowing users to manipulate the generative process using a command-line-like syntax within the prompt itself.

### The Core Shift
We are moving from:
`String Prompt` → `Pipeline` → `Image`

To:
`String Prompt` → `Parser (AST)` → `Embedding Engine (Tensor Math)` → `Custom Pipeline` → `Image`

---

## 2. Architecture Overview

### 2.1 New Components

1.  **`src/z_explorer/core/prompt_parser.py`**
    *   **Responsibility:** Parses the raw prompt string into a structured object (AST).
    *   **Logic:** Identifies operators, splits segments, and extracts parameters (seeds, weights, steps).
    *   **Output:** `PromptGraph` or `Operation` objects.

2.  **`src/z_explorer/core/embedding_engine.py`**
    *   **Responsibility:** Handles the "Latent Math".
    *   **Logic:** Interacts with the Text Encoders (CLIP/T5/Qwen) to generate raw embeddings. Performs addition, subtraction, interpolation (`%`), and scaling (`*`) on the tensors.
    *   **Output:** `torch.Tensor` (prompt_embeds, pooled_prompt_embeds).

3.  **`src/z_explorer/core/scheduler_controller.py`**
    *   **Responsibility:** Handles temporal operations (`|`, `@`).
    *   **Logic:** Manages the state during the denoising loop. Determines *which* embedding to use for the current timestep.

### 2.2 Pipeline Modifications (`image_generator.py`)
The existing `generate_image` function relies on the standard `pipe(prompt=...)` call. This is insufficient for our needs.
*   **Change:** We must switch to passing `prompt_embeds` and `pooled_prompt_embeds` directly.
*   **Change:** We must implement a custom denoising loop or use advanced callback injection to support per-step embedding swapping (for `|` and `@`).

---

## 3. Phased Implementation Roadmap

### Phase 1: Foundation & Determinism (MVP)
**Goal:** Establish the parsing infrastructure and implement the simplest operator.

*   **1.1 Implement `PromptParser`**
    *   Create a parser that can handle the basic syntax structure.
    *   Support: `prompt #seed` (Seed Control).
    *   Support: `prompt : params` (Existing batch params, moved to parser).
*   **1.2 Update `generator.py`**
    *   Integrate the parser into the main generation flow.
    *   Ensure seeds are correctly extracted and applied.

**Deliverable:** Users can pin seeds using `#1234` syntax. Codebase has a clean `prompt_parser.py`.

### Phase 2: The Alternator & Scheduler (Temporal Ops)
**Goal:** Implement operators that manipulate the *process* (Denoising Loop).

*   **2.1 Custom Pipeline Control**
    *   Refactor `image_generator.py` to expose the denoising loop or use `callback_on_step_end` more aggressively.
*   **2.2 Implement `|` (Alternating Prompt)**
    *   Parser support: `cat | dog`.
    *   Logic: Pre-compute embeddings for both "cat" and "dog". In the callback, swap the conditioning tensor based on `step % 2`.
*   **2.3 Implement `@` (Temporal Scheduling)**
    *   Parser support: `cat @0-50% dog @50-100%`.
    *   Logic: In the callback, check current step percentage and switch embeddings accordingly.

**Deliverable:** Users can create hybrid concepts using `|` and control composition vs. detail using `@`.

### Phase 3: Latent Math (Tensor Ops)
**Goal:** Implement operators that manipulate the *representation* (Embeddings).

*   **3.1 Implement `EmbeddingEngine`**
    *   Create a module that holds the Text Encoders (loaded from the pipeline or separately).
    *   Implement `get_embeddings(text)` -> Tensor.
*   **3.2 Implement `+` / `-` (Blend/Subtract)**
    *   Parser support: `cat + dog`, `cat - stripes`.
    *   Logic: `Embed(A) + Embed(B)` or `Embed(A) - Embed(B)`.
    *   *Note:* Must handle both CLIP and T5 embeddings if using SDXL/Flux-based models (Z-Image-Turbo uses Qwen/CLIP hybrid, need to verify exact tensor shapes).
*   **3.3 Implement `%` (Interpolation)**
    *   Parser support: `cat % dog : 10`.
    *   Logic: This is a "Meta-Operator". It generates *multiple* generation requests.
    *   The `generator.py` must expand this single request into a list of 10 requests, each with a pre-calculated blended embedding: `Embed(A) * (1-t) + Embed(B) * t`.

**Deliverable:** Users can blend concepts mathematically and generate interpolation animations.

---

## 4. Technical Deep Dive

### 4.1 The Parser Strategy
We should avoid complex regex. A simple token-based parser or a lightweight grammar is preferred.

**Proposed Structure:**
```python
@dataclass
class PromptSegment:
    text: str
    weight: float = 1.0
    schedule_start: float = 0.0
    schedule_end: float = 1.0
    seed: Optional[int] = None

@dataclass
class ParsedPrompt:
    segments: List[PromptSegment]
    operations: List[Operation] # e.g., InterpolateOp
```

### 4.2 The Embedding Math
Z-Image-Turbo uses a specific text encoder setup. We need to ensure we are operating on the correct hidden states.

*   **Weighted Average:** `result = e1 * w1 + e2 * w2`
*   **Normalization:** After math operations, we might need to re-normalize the embedding vectors to maintain the expected magnitude for the UNet/Transformer, though usually, the model handles unnormalized inputs okay.

### 4.3 The "Walk" Operator (`%`)
This is unique because it changes the *output count*.
*   Input: `Request(prompt="a % b : 5", count=1)`
*   Logic: The parser identifies this as a "Generator Expansion".
*   Output: `[Request(embed=e1), Request(embed=e1.25), ..., Request(embed=e2)]` (5 distinct jobs).

---

## 5. Risk Assessment

1.  **VRAM Usage:** Holding multiple sets of embeddings (for `|` or `@`) increases VRAM usage slightly, but it's negligible compared to the model weights.
2.  **Model Compatibility:** If we switch base models (e.g., to Flux or SD3), the embedding math logic (`EmbeddingEngine`) will need to be updated to match the new text encoder architecture.
3.  **Parser Complexity:** As syntax grows (`(a + b) | (c % d)`), a simple parser might break. We should define strict limits on nesting for V1.

## 6. Testing Strategy

1.  **Unit Tests (`tests/core/test_parser.py`)**:
    *   Verify `cat #123` extracts seed 123.
    *   Verify `cat | dog` creates two segments.
    *   Verify `cat % dog : 5` creates an interpolation op.
2.  **Visual Verification**:
    *   `#`: Run same prompt+seed twice, ensure bit-exact output.
    *   `|`: Generate `cat | dog` and compare to `cat` and `dog`. Should look like a mix.
    *   `%`: Generate a walk. Stack images in a GIF. Should be smooth.

---

## 7. Next Steps

1.  Approve this plan.
2.  Begin **Phase 1**: Create `src/z_explorer/core/prompt_parser.py`.
