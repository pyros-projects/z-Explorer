# Implementation Plan: Future Creative Features

**Status:** Draft
**Date:** 2025-12-03
**Target:** `z-Explorer` Extended Architecture

---

## 1. Executive Summary

This plan details the technical implementation for the 10 "Power Without Spaghetti" features identified in the brainstorming session. These features move Z-Explorer beyond simple text-to-image into a full creative suite.

**Key Technical Additions:**
1.  **Vision Encoders:** IP-Adapter (for Style/Character consistency).
2.  **ControlNets:** For structure guidance (Remix).
3.  **Segmentation:** FastSAM or CLIPSeg (for Semantic Editing).
4.  **State Management:** History trees and global context.

---

## 2. Feature Implementation Details

### Group A: The "Vision" Features (IP-Adapter)
*Requires adding image-based conditioning to the pipeline.*

#### 1. 🧬 "Vibe Snatching" (Style Transfer)
*   **Tech:** IP-Adapter (Image Prompt Adapter).
*   **Implementation:**
    *   Load `IP-Adapter-Plus` (better for style).
    *   Add a drag-and-drop zone in UI to upload reference image.
    *   Backend: Pass image to IP-Adapter image encoder.
    *   Pipeline: Inject embeddings into cross-attention layers.
    *   **Syntax:** `prompt :: [image_path]` -> Parser extracts path, loads image, activates IP-Adapter.

#### 2. 🎭 "The Cast List" (Consistent Characters)
*   **Tech:** IP-Adapter + JSON Database.
*   **Implementation:**
    *   **Storage:** `characters.json` stores `{name: {seed: int, embedding: tensor_path, ref_image: path}}`.
    *   **Definition:** When user runs `char:alice = ...`, generate an image, save its seed, and optionally save the generated image as a "reference" for IP-Adapter.
    *   **Usage:** When "alice" is detected in prompt, auto-load her reference image into IP-Adapter (FaceID version preferred for characters) and set the base seed.

#### 3. 🎬 "The Director's Cut" (Storyboarding)
*   **Tech:** Pipeline Loop + Cast List.
*   **Implementation:**
    *   **Parser:** Split prompt by `->`.
    *   **Logic:**
        1.  Detect shared subjects (e.g., "Alice").
        2.  Lock "Alice's" features (using Cast List logic).
        3.  Generate Image 1.
        4.  Generate Image 2 (using Image 1 as context/reference if needed).
    *   **Output:** Stitch images into a single strip using Pillow.

---

### Group B: The "Control" Features (ControlNet/Seg)
*Requires auxiliary models for structural guidance.*

#### 4. 🪄 "Semantic Editing" (No-Brush Inpaint)
*   **Tech:** FastSAM (Fast Segment Anything) or CLIPSeg.
*   **Implementation:**
    *   **Command:** `fix(hands)`.
    *   **Pipeline:**
        1.  Pass current image + "hands" text to CLIPSeg.
        2.  Get heatmap -> Threshold -> Binary Mask.
        3.  Dilate mask slightly (to cover edges).
        4.  Run Inpainting Pipeline (VAE Encode masked image + mask).
    *   **Optimization:** Keep segmentation model unloaded until needed (lazy load).

#### 5. 🔄 "The Remix Button" (Variation)
*   **Tech:** ControlNet (Canny or Depth).
*   **Implementation:**
    *   **Command:** `remix(image_id, "new prompt")`.
    *   **Pipeline:**
        1.  Load source image.
        2.  Run Canny Edge Detector (opencv).
        3.  Pass edge map to ControlNet.
        4.  Generate with new prompt + ControlNet guidance.
    *   **UI:** "Remix" button on every gallery image.

---

### Group C: The "Engine" Features (Core Logic)
*Requires changes to `generator.py` and `server.py`.*

#### 6. 🎥 "The Dream Stream" (Real-Time)
*   **Tech:** LCM (Latent Consistency Model) or SDXL Turbo + WebSocket/MJPEG.
*   **Implementation:**
    *   **Model:** Must use a Turbo/LCM model (1-4 steps).
    *   **Server:** New endpoint `/api/stream/ws`.
    *   **Loop:**
        *   While connection open:
            *   Get current prompt buffer.
            *   Generate (1 step).
            *   Push JPEG frame to socket.
    *   **Optimization:** Keep VAE in float16, maybe use TinyVAE.

#### 7. 🗺️ "Latent Cartography" (Map)
*   **Tech:** Grid Generation.
*   **Implementation:**
    *   **Command:** `map(seed)`.
    *   **Logic:**
        *   Center = `seed`.
        *   Neighbors = `seed + 1`, `seed - 1`, or `seed` with slightly perturbed noise.
        *   Generate 3x3 grid.
    *   **UI:** Clickable grid where each cell becomes the new center.

#### 8. 🌍 "The Style Thief" (Global Context)
*   **Tech:** Global Variable Store.
*   **Implementation:**
    *   **Store:** Simple dictionary in `server.py` state.
    *   **Logic:** Before parsing any prompt, prepend `global_style` string.
    *   **UI:** "Active Style" chip that can be cleared.

#### 9. 🧱 "Texture Baker" (Seamless Mode)
*   **Tech:** Model Patching.
*   **Implementation:**
    *   **Hack:** Patch `torch.nn.Conv2d` to use `padding_mode='circular'` before generation, restore to `'zeros'` after.
    *   **Alternative:** Use `AsymmetricTiling` script logic (modifying UNet attention).
    *   **Post-Process:** Generate Normal/Roughness maps using a lightweight estimator (like `modnet` or simple Sobel filters for normals).

#### 10. ⏪ "Time Travel" (History)
*   **Tech:** Tree Data Structure.
*   **Implementation:**
    *   **Data:** Each generation record needs `parent_id`.
    *   **UI:** Visualization of the tree (D3.js or Svelte Flow).
    *   **Action:** Clicking a node restores its state (prompt, seed, settings) to the active input.

---

## 3. Architecture Impact

### New Dependencies
*   `controlnet_aux` (for Canny/Depth preprocessors)
*   `ip_adapter` (library or custom implementation)
*   `transformers` (already present, but need CLIPSeg/FastSAM)
*   `opencv-python` (for image processing)

### Model Management
These features require *more* VRAM.
*   **Strategy:** Aggressive offloading.
    *   Segmentation model only loads for `fix()`.
    *   ControlNet only loads for `remix()`.
    *   IP-Adapter weights are small (~100MB), can stay in RAM, move to VRAM on demand.

### Roadmap
1.  **Phase 1 (Core):** Time Travel, Style Thief, Latent Cartography (No new models needed).
2.  **Phase 2 (Vision):** Vibe Snatching, Cast List (IP-Adapter).
3.  **Phase 3 (Control):** Remix, Semantic Editing (ControlNet/Seg).
4.  **Phase 4 (Real-time):** Dream Stream (Requires backend overhaul for WebSockets).
