# Z-Explorer Configuration Guide

This guide covers all configuration options for Z-Explorer, including model loading strategies, environment variables, and setup presets.

## Table of Contents

- [Quick Start](#quick-start)
- [Setup Wizard](#setup-wizard)
- [Configuration Presets](#configuration-presets)
- [Environment Variables](#environment-variables)
  - [Image Model Configuration](#image-model-configuration)
  - [LLM Configuration](#llm-configuration)
- [Loading Modes](#loading-modes)
  - [Image Model Modes](#image-model-modes)
  - [LLM Modes](#llm-modes)
- [Advanced Configuration](#advanced-configuration)
- [Runtime Model Override](#runtime-model-override-settings-dialog)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

For most users, the setup wizard will guide you through configuration:

```bash
# First run will automatically start the setup wizard
z-explorer

# Or run the wizard manually
z-explorer --setup
```

Choose **"Quick Start (Recommended for beginners)"** to get started with optimized quantized models that work well on consumer GPUs (12GB+ VRAM).

---

## Setup Wizard

The setup wizard offers three modes:

### 1. Quick Start (Recommended for beginners)

- **Image Model**: SDNQ quantized (~6GB download, ~12GB VRAM)
- **LLM**: BNB 4-bit quantized Qwen (~4GB download, fast inference)
- **Best for**: Users with 12GB+ VRAM GPUs

### 2. Custom Setup

Configure each component individually:
- Choose image model source (HF download, SDNQ, local, or ComfyUI components)
- Choose LLM source (Z-Image built-in, HF download, local, or GGUF)

### 3. Full Quality

- **Image Model**: Full precision Z-Image-Turbo (~15GB download, ~24GB VRAM)
- **LLM**: Uses Z-Image's built-in text encoder (no extra download)
- **Best for**: Users with 24GB+ VRAM GPUs wanting maximum quality

---

## Configuration Presets

### Quick Start Preset

```bash
# .env file
Z_IMAGE_MODE=sdnq
Z_IMAGE_SDNQ=Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32
LLM_MODE=hf_download
LLM_REPO=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
```

### Full Quality Preset

```bash
# .env file
Z_IMAGE_MODE=hf_download
LLM_MODE=z_image
```

### ComfyUI Components Preset

```bash
# .env file
Z_IMAGE_MODE=components
Z_IMAGE_TRANSFORMER=/path/to/z_image_turbo_bf16.safetensors
Z_IMAGE_TEXT_ENCODER=/path/to/qwen_3_4b.safetensors
Z_IMAGE_VAE=/path/to/ae.safetensors
LLM_MODE=z_image  # Uses the text encoder above
```

---

## Environment Variables

All configuration is stored in a `.env` file in your working directory.

### Image Model Configuration

| Variable | Description | Values |
|----------|-------------|--------|
| `Z_IMAGE_MODE` | Loading strategy for image model | `hf_download`, `hf_local`, `components`, `sdnq` |
| `Z_IMAGE_HF` | Path to local HuggingFace clone | Local directory path |
| `Z_IMAGE_TRANSFORMER` | Path to transformer safetensor | `.safetensors` file path |
| `Z_IMAGE_TEXT_ENCODER` | Path to text encoder safetensor | `.safetensors` file path |
| `Z_IMAGE_VAE` | Path to VAE safetensor | `.safetensors` file path |
| `Z_IMAGE_SDNQ` | SDNQ model repository | HuggingFace repo ID |
| `Z_IMAGE_PATH` | Legacy: HF repo or local path | Deprecated, use specific vars |

### LLM Configuration

| Variable | Description | Values |
|----------|-------------|--------|
| `LLM_MODE` | Loading strategy for LLM | `z_image`, `hf_download`, `hf_local`, `gguf` |
| `LLM_REPO` | HuggingFace repository for LLM | HuggingFace repo ID |
| `LLM_PATH` | Path to local model or GGUF | Directory or file path |
| `LLM_GGUF_FILE` | GGUF filename (for gguf mode) | Filename (e.g., `model-Q4_K_M.gguf`) |

### Other Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `LOCAL_OUTPUT_DIR` | Directory for generated images | `./output` |

---

## Loading Modes

### Image Model Modes

#### `hf_download` - Download from HuggingFace

Downloads the full precision model from HuggingFace Hub.

```bash
Z_IMAGE_MODE=hf_download
# Uses default: Tongyi-MAI/Z-Image-Turbo
```

**Requirements**: ~15GB download, ~24GB VRAM
**Best for**: Maximum quality, high-end GPUs

#### `sdnq` - SDNQ Quantized Model

Downloads a quantized model optimized for lower VRAM usage.

```bash
Z_IMAGE_MODE=sdnq
Z_IMAGE_SDNQ=Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32
```

**Requirements**: ~6GB download, ~12GB VRAM
**Best for**: Consumer GPUs (RTX 3080, 4070, etc.)

#### `hf_local` - Local HuggingFace Clone

Use a local copy of the HuggingFace repository (for offline use).

```bash
Z_IMAGE_MODE=hf_local
Z_IMAGE_HF=/path/to/Z-Image-Turbo
```

**Requirements**: Pre-downloaded model directory with `model_index.json`
**Best for**: Offline environments, air-gapped systems

#### `components` - ComfyUI-Style Components

Load individual safetensor files (compatible with ComfyUI model management).

```bash
Z_IMAGE_MODE=components
Z_IMAGE_TRANSFORMER=/models/diffusion_models/z_image_turbo_bf16.safetensors
Z_IMAGE_TEXT_ENCODER=/models/text_encoders/qwen_3_4b.safetensors
Z_IMAGE_VAE=/models/vae/ae.safetensors
```

**Requirements**: Individual safetensor files in ComfyUI format
**Best for**: Users with existing ComfyUI model libraries

**Note**: Z-Explorer automatically converts ComfyUI key naming to diffusers format.

### LLM Modes

#### `z_image` - Use Z-Image's Text Encoder

Uses the same Qwen model that's part of Z-Image (no extra download).

```bash
LLM_MODE=z_image
```

**Pros**: No extra download needed
**Cons**: Uses "thinking" mode, slower for variable generation
**Best for**: Minimal setup, occasional use

#### `hf_download` - Download from HuggingFace

Downloads a separate LLM from HuggingFace Hub. Supports BNB quantized models!

```bash
LLM_MODE=hf_download
LLM_REPO=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit  # Recommended
# or
LLM_REPO=Qwen/Qwen3-4B  # Full precision
```

**Recommended Models**:
- `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit` - BNB 4-bit, fast inference
- `Qwen/Qwen3-4B` - Full precision
- Any HuggingFace-compatible causal LLM

**Best for**: Fast variable generation, batch processing

#### `hf_local` - Local Model Path

Use a locally downloaded HuggingFace model.

```bash
LLM_MODE=hf_local
LLM_PATH=/path/to/local/model
```

**Best for**: Offline environments, custom models

#### `gguf` - GGUF File (CPU-Friendly)

Load a GGUF quantized model (works well on CPU, lower VRAM).

```bash
LLM_MODE=gguf
LLM_PATH=/path/to/gguf/files  # or HuggingFace repo ID
LLM_GGUF_FILE=model-Q4_K_M.gguf
```

**Note**: Transformers dequantizes GGUF to FP32, so memory savings are limited compared to llama.cpp.

**Best for**: CPU inference, very low VRAM situations

---

## Advanced Configuration

### Memory Management

Z-Explorer automatically manages GPU memory:
- When loading the image model, the LLM is unloaded
- When loading the LLM, the image model is unloaded
- Use the `/api/unload` endpoint to manually free memory

### Custom Model Repositories

You can use any compatible HuggingFace repository:

```bash
# Custom Z-Image variant
Z_IMAGE_MODE=hf_download
Z_IMAGE_PATH=your-org/custom-z-image

# Custom LLM
LLM_MODE=hf_download
LLM_REPO=mistralai/Mistral-7B-Instruct-v0.2
```

### Combining Local and Remote

Mix local and remote sources:

```bash
# Local image model, remote LLM
Z_IMAGE_MODE=hf_local
Z_IMAGE_HF=/local/models/Z-Image-Turbo
LLM_MODE=hf_download
LLM_REPO=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
```

---

## Runtime Model Override (Settings Dialog)

Z-Explorer includes a Settings dialog (accessible via `/settings` in the UI) that allows you to temporarily override model configurations **without modifying your `.env` file**.

### How It Works

1. **Open Settings**: Type `/settings` in the CLI or click the settings icon
2. **Navigate to Models Tab**: Select the "Models" tab in the Settings dialog
3. **Configure Models**: Choose loading modes and enter paths/repos for:
   - **Image Model**: HuggingFace Download, Local HF Clone, SDNQ Quantized, or Components
   - **LLM**: HuggingFace Download, Local HF Clone, GGUF, or use Z-Image's built-in encoder
4. **Test Connection**: Click "Test Connection" to verify your configuration before applying
5. **Save & Reload**: Click "Save & Reload Models" to apply changes

### Key Features

- **Session-Only Changes**: Overrides persist only until the server restarts. Your `.env` file remains unchanged.
- **Connection Testing**: Validate that model paths/repos are accessible before committing to a reload
- **Non-Destructive**: If something goes wrong, simply restart the server to return to your `.env` configuration

### Use Cases

- **Experimentation**: Try different models without permanent config changes
- **A/B Testing**: Compare model outputs by switching between configurations
- **Development**: Test various loading modes during development
- **Quick Switching**: Temporarily use a different quantization for a specific task

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/settings/models` | GET | Get current model configuration |
| `/api/settings/models` | POST | Update model configuration and trigger reload |
| `/api/settings/models/test` | POST | Test if a configuration is valid |
| `/api/models/reload` | POST | Reload models with current configuration |

### Example: Switching Models via API

```bash
# Test a new configuration
curl -X POST http://localhost:8345/api/settings/models/test \
  -H "Content-Type: application/json" \
  -d '{"model_type": "image", "mode": "sdnq", "repo": "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32"}'

# Apply the configuration
curl -X POST http://localhost:8345/api/settings/models \
  -H "Content-Type: application/json" \
  -d '{
    "image_mode": "sdnq",
    "image_repo": "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32",
    "llm_mode": "hf_download",
    "llm_repo": "unsloth/Qwen3-4B-Instruct-2507-bnb-4bit"
  }'
```

---

## Troubleshooting

### Common Issues

#### "ZImagePipeline not found"

Your diffusers version is too old. Z-Explorer requires the latest diffusers from GitHub:

```bash
pip install git+https://github.com/huggingface/diffusers
```

#### "CUDA out of memory"

Try a lower VRAM configuration:

```bash
Z_IMAGE_MODE=sdnq
LLM_MODE=hf_download
LLM_REPO=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
```

#### "Missing key in state_dict" (ComfyUI components)

Ensure you're using the correct safetensor files:
- Transformer: `z_image_turbo_bf16.safetensors` (from `diffusion_models/`)
- Text Encoder: `qwen_3_4b.safetensors` (from `text_encoders/`)
- VAE: `ae.safetensors` (same as FLUX VAE)

#### "LLM configuration errors"

Check your LLM environment variables:

```bash
z-explorer --show-config
```

### Resetting Configuration

Delete your `.env` file to reset and re-run the setup wizard:

```bash
rm .env
z-explorer
```

### Debug Mode

Check current configuration:

```bash
z-explorer --show-config
```

---

## Model Sources

### Official Repositories

| Model | Repository | Size |
|-------|------------|------|
| Z-Image-Turbo | `Tongyi-MAI/Z-Image-Turbo` | ~24GB |
| Z-Image SDNQ | `Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32` | ~6GB |
| ComfyUI Split | `Comfy-Org/z_image_turbo` | ~12GB |
| Qwen3-4B (BNB) | `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit` | ~4GB |
| Qwen3-4B | `Qwen/Qwen3-4B` | ~8GB |

### ComfyUI File Locations

If using ComfyUI-style components, place files in:

```
ComfyUI/models/
├── diffusion_models/
│   └── z_image_turbo_bf16.safetensors
├── text_encoders/
│   └── qwen_3_4b.safetensors
└── vae/
    └── ae.safetensors
```

---

## API Reference

### Configuration Functions

```python
from z_explorer.model_config import (
    get_image_model_config,  # Get current image model config
    get_llm_config,          # Get current LLM config
    save_config,             # Save configuration to .env
    print_config,            # Print current config (debug)
    is_configured,           # Check if configured
)

# Example
config = get_image_model_config()
print(f"Mode: {config.mode}")
print(f"Valid: {config.validate()}")
```

### Setup Wizard

```python
from z_explorer.setup_wizard import (
    run_wizard,           # Run full setup wizard
    run_wizard_if_needed, # Run only if not configured
)

# Programmatic setup
run_wizard()
```

---

## Support

- **GitHub Issues**: https://github.com/pyros-projects/z-Explorer/issues
- **Documentation**: https://github.com/pyros-projects/z-Explorer/docs

For questions about Z-Image model itself, see the [official repository](https://github.com/Tongyi-MAI/Z-Image).
