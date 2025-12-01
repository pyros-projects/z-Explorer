# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Z-Explorer is a local AI image generation tool that combines Z-Image-Turbo (image generation) with Qwen3-4B (LLM for prompt enhancement and variable generation). Everything runs locally - no cloud APIs required.

## Common Commands

### Development

```bash
# Install dependencies (required - uses git dependencies)
uv sync

# Run the application (web UI mode - default)
uv run z-explorer

# Run in CLI mode (expert/terminal mode)
uv run z-explorer --cli

# Run setup wizard
uv run z-explorer --setup

# Show current model configuration
uv run z-explorer --show-config
```

### Testing

```bash
# Run all tests with coverage
uv run pytest

# Run a specific test file
uv run pytest tests/test_server/test_endpoints.py

# Run a specific test
uv run pytest tests/test_cli.py::test_parse_batch_params -v

# Run with verbose output
uv run pytest -v
```

### GUI Development

```bash
# From src/z_explorer/gui/
npm install
npm run dev          # Start Vite dev server (port 5173)
npm run build        # Build for production
npm run check        # TypeScript/Svelte type checking
npm run test         # Run Vitest tests
npm run test:watch   # Watch mode
```

### Linting

```bash
uv run ruff check .
uv run ruff format .
```

## Architecture

### Two-Phase Generation Pipeline

The core innovation is a two-phase approach that manages GPU memory efficiently:

1. **Phase 1 (LLM)**: Generate/enhance all prompts using Qwen3-4B
   - Variable substitution (`__animal__` → random value)
   - Prompt enhancement (using `>` operator)
   - LLM unloaded after this phase

2. **Phase 2 (Image)**: Generate images using Z-Image-Turbo
   - Diffusion model loaded after LLM is unloaded
   - Both models cannot fit in VRAM simultaneously

This logic lives in `src/z_explorer/core/generator.py` - the single source of truth for generation.

### Key Modules

| Module | Purpose |
|--------|---------|
| `cli.py` | Entry point, argument parsing, interactive CLI mode |
| `server.py` | FastAPI server with SSE for real-time progress streaming |
| `core/generator.py` | Unified generation workflow (Phase 1 + Phase 2) |
| `image_generator.py` | Z-Image-Turbo pipeline loading and image generation |
| `llm_provider.py` | Qwen3-4B loading, text generation, prompt enhancement |
| `model_config.py` | Configuration management for model sources |
| `setup_wizard.py` | Interactive first-run configuration |
| `services/download.py` | Model download with progress tracking |

### Model Loading Modes

**Image Model** (`Z_IMAGE_MODE`):
- `hf_download` - Download from HuggingFace (~24GB VRAM)
- `sdnq` - SDNQ quantized (~12GB VRAM, recommended)
- `hf_local` - Local HuggingFace clone
- `components` - ComfyUI-style safetensor files

**LLM** (`LLM_MODE`):
- `hf_download` - Download from HuggingFace (supports BNB quantized)
- `z_image` - Use Z-Image's built-in text encoder
- `hf_local` - Local model path
- `gguf` - GGUF quantized file

### Frontend Architecture

Svelte 4 app in `src/z_explorer/gui/`:
- `App.svelte` - Main component, SSE connection, state management
- `FakeCLI.svelte` - Terminal-style input with autocomplete
- `Gallery.svelte` - Image display with multiple layout modes
- `Settings.svelte` - Runtime configuration dialog
- `Setup.svelte` - First-run model download wizard

The GUI connects to the FastAPI backend via SSE (`/api/generate/stream`) for real-time progress updates during generation.

### API Endpoints

Key endpoints in `server.py`:
- `GET /api/generate/stream` - SSE stream for image generation with progress
- `GET /api/variables` - List prompt variables
- `GET /api/images` - List generated images
- `POST /api/settings/models` - Runtime model configuration override
- `POST /api/unload` - Free GPU memory

## Prompt Syntax

```
__variable__           Random value substitution
__variable:5__         Specific index
prompt > instruction   LLM enhancement
prompt : x10,w1920,h1080   Batch parameters
```

## Configuration

Configuration is stored in `.env` file. Key variables:
- `Z_IMAGE_MODE` / `Z_IMAGE_SDNQ` / `Z_IMAGE_HF` - Image model config
- `LLM_MODE` / `LLM_REPO` - LLM config
- `LOCAL_OUTPUT_DIR` - Output directory (default: `./output`)

See `docs/CONFIGURATION.md` for full details.

## Memory Management

The codebase automatically manages GPU memory:
- Loading image model → unloads LLM first
- Loading LLM → unloads image model first
- `/api/unload` endpoint to manually free all memory

## Dependencies

Uses `uv` package manager with git dependencies (diffusers from GitHub). Do not use `pip install` or `uvx` - always use `uv sync` to get correct versions.
