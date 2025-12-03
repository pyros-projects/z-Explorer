# Z-Explorer Backend/CLI Architecture

## Executive Summary

Z-Explorer is a local AI image generation tool that runs entirely offline, combining Z-Image-Turbo (diffusion model) with Qwen3-4B (LLM) for prompt enhancement and variable generation. The backend is a service-oriented Python application built on FastAPI with a sophisticated two-phase generation pipeline that manages GPU memory constraints by never loading both models simultaneously.

**Key Innovation:** Two-phase pipeline that unloads the LLM before loading the image model, enabling operation on GPUs with limited VRAM (~12GB with quantization).

**Version:** 0.4.40
**Python Version:** 3.12
**Package Manager:** uv (required for git dependencies)

---

## Technology Stack

### Core Dependencies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Web Framework** | FastAPI + Uvicorn | REST API with SSE streaming |
| **Deep Learning** | PyTorch 2.0+ | Model inference |
| **Image Generation** | diffusers (git) | Z-Image-Turbo pipeline |
| **LLM** | transformers (git) | Qwen3-4B + any HF-compatible LLM |
| **Quantization** | bitsandbytes, SDNQ | 4-bit and uint4 quantization |
| **CLI** | Rich, Questionary | Interactive terminal UI |
| **Configuration** | python-dotenv, Pydantic | Settings management |
| **Logging** | loguru | Structured logging |
| **Testing** | pytest, pytest-asyncio | Unit and integration tests |

### Git Dependencies (Require `uv sync`)

```python
"sdnq @ git+https://github.com/Disty0/sdnq"
"diffusers @ git+https://github.com/huggingface/diffusers"
"transformers @ git+https://github.com/huggingface/transformers"
```

**Why git dependencies?** Z-Image-Turbo is a bleeding-edge model requiring latest diffusers API that isn't yet in PyPI releases.

---

## Architecture Pattern

**Service-Oriented Architecture with CLI Interface**

```
┌─────────────────────────────────────────────────────────────┐
│                          CLI Entry Point                      │
│                         (cli.py:main)                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  CLI Mode   │  │  Server Mode │  │  Setup Wizard    │   │
│  │  --cli      │  │  (default)   │  │  --setup         │   │
│  └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘   │
└─────────┼─────────────────┼────────────────────┼─────────────┘
          │                 │                    │
          ▼                 ▼                    ▼
    ┌─────────────┐   ┌──────────────┐   ┌───────────────┐
    │ Interactive │   │ FastAPI      │   │ Model Config  │
    │ Loop        │   │ Server       │   │ Wizard        │
    │ (Rich UI)   │   │ (REST+SSE)   │   │ (Questionary) │
    └─────┬───────┘   └──────┬───────┘   └───────┬───────┘
          │                  │                    │
          └──────────────────┼────────────────────┘
                             ▼
                    ┌─────────────────┐
                    │  Core Generator │
                    │  (generator.py) │
                    └────────┬────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
    ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
    │ LLM Provider │  │ Image       │  │ Model Config │
    │              │  │ Generator   │  │              │
    └──────────────┘  └─────────────┘  └──────────────┘
```

---

## Key Components

### 1. Entry Point: `cli.py`

**Purpose:** Command-line interface and application entry point

**Key Functions:**
- `main()` - Argument parsing and mode selection
- `start_web_mode()` - Launch FastAPI server + browser
- `start_cli_mode()` - Launch interactive terminal mode
- `interactive_loop()` - CLI REPL with autocomplete

**Modes:**
```bash
z-explorer              # Default: Web UI mode (server + browser)
z-explorer --cli        # Interactive CLI mode (expert users)
z-explorer --setup      # Configuration wizard
z-explorer --show-config # Display current configuration
```

**Features:**
- Autocomplete for commands and prompt variables
- Batch parameter parsing (`prompt : x10,h832,w1216`)
- Enhancement syntax (`prompt > enhancement instruction`)
- Command system (`/help`, `/vars`, `/gpu`, `/unload`, etc.)

---

### 2. API Server: `server.py`

**Purpose:** REST API with Server-Sent Events for real-time progress

**Default Configuration:**
```python
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8345
```

**Key Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Health check + version |
| `/api/gpu` | GET | GPU memory status |
| `/api/generate/stream` | GET | SSE stream for image generation |
| `/api/generate` | POST | Programmatic generation (SSE) |
| `/api/variables` | GET | List prompt variables |
| `/api/images` | GET | List generated images |
| `/api/unload` | POST | Free GPU memory |
| `/api/config` | GET | Current model configuration |
| `/api/settings/models` | POST | Runtime model config override |
| `/api/models/reload` | POST | Reload models with new config |
| `/api/setup/status` | GET | Check setup/download status |
| `/api/setup/download` | GET | Download models (SSE progress) |

**SSE Progress Streaming:**

Server emits JSON events over SSE:
```json
{
  "stage": "diffusion_step",
  "message": "Image 1/10: step 5/9",
  "progress": 75,
  "data": {"step": 5, "total": 9}
}
```

**CORS Configuration:** Allow all origins (local desktop app)

---

### 3. Core Generator: `core/generator.py`

**Purpose:** Single source of truth for image generation workflow

**Main Function:**
```python
def generate(
    request: GenerationRequest,
    on_progress: Optional[ProgressCallback] = None,
) -> GenerationResult
```

**Two-Phase Generation Pipeline:**

```
┌─────────────────────────────────────────────────────────────┐
│                       PHASE 1: LLM                           │
│                   (Prompt Preparation)                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Load prompt variables from library                        │
│ 2. For each image (count times):                             │
│    a. Substitute __variables__ with random values            │
│    b. Generate missing variables using LLM                   │
│    c. Apply enhancement if requested (> syntax)              │
│ 3. Result: List of final prompts ready for generation        │
│ 4. Unload LLM to free GPU memory                             │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     PHASE 2: Image Model                      │
│                   (Image Generation)                          │
├─────────────────────────────────────────────────────────────┤
│ 1. Load Z-Image-Turbo pipeline                               │
│ 2. For each prompt:                                           │
│    a. Generate image with diffusion (9 steps)                │
│    b. Save image to output directory                         │
│    c. Save prompt to .txt file alongside image               │
│    d. Emit progress events with image path                   │
│ 3. Result: List of image paths + metadata                    │
└─────────────────────────────────────────────────────────────┘
```

**Key Design Decision:** Phase 1 completes entirely before Phase 2 begins. This ensures:
- Predictable memory usage
- All prompts available before image generation starts
- LLM unloaded before diffusion model loads

**Progress Events:** 31 distinct stage types (see `core/types.py`) including:
- `starting`, `loading_vars`, `substituting`
- `var_missing`, `var_generating`, `var_saved`
- `enhancing`, `enhanced`, `final_prompt`
- `llm_unloaded`, `loading_image_model`
- `generating_image`, `diffusion_step`, `image_saved`
- `complete`, `error`

---

### 4. Image Generator: `image_generator.py`

**Purpose:** Z-Image-Turbo pipeline management and image generation

**Model Loading Modes:**

| Mode | Description | VRAM | Configuration |
|------|-------------|------|---------------|
| `hf_download` | Download from HuggingFace Hub | ~24GB | `Z_IMAGE_MODE=hf_download` |
| `sdnq` | SDNQ quantized model (uint4) | ~12GB | `Z_IMAGE_MODE=sdnq` (recommended) |
| `hf_local` | Local HuggingFace clone | ~24GB | `Z_IMAGE_MODE=hf_local`, `Z_IMAGE_HF=/path` |
| `components` | Individual safetensor files | ~24GB | `Z_IMAGE_MODE=components`, paths for transformer/VAE/text_encoder |

**Key Functions:**

```python
def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_steps: int = 9,
    seed: Optional[int] = None,
    progress_callback: Optional[Callable] = None,
) -> tuple[Image.Image, str]
```

**Pipeline Loading Strategy:**
- Lazy loading (global `_pipeline` variable)
- Automatically unloads LLM before loading
- CUDA device management (GPU if available, CPU fallback)

**ComfyUI Components Support:**
- Converts ComfyUI key naming to diffusers format
- Splits concatenated QKV tensors into separate Q, K, V
- Loads safetensor files tensor-by-tensor to avoid memory spikes
- Fetches small config JSON files from HuggingFace (no weights)

**Memory Management:**
```python
def unload_pipeline():
    """Unload pipeline and clear CUDA cache"""
    del _pipeline
    gc.collect()
    torch.cuda.empty_cache()
```

---

### 5. LLM Provider: `llm_provider.py`

**Purpose:** Local LLM for prompt enhancement and variable generation

**LLM Modes:**

| Mode | Description | Configuration |
|------|-------------|---------------|
| `z_image` | Use Z-Image's text encoder | `LLM_MODE=z_image` (default) |
| `hf_download` | Download from HuggingFace | `LLM_MODE=hf_download`, `LLM_REPO=...` |
| `hf_local` | Local model path | `LLM_MODE=hf_local`, `LLM_PATH=...` |
| `gguf` | GGUF quantized file | `LLM_MODE=gguf`, `LLM_PATH=...`, `LLM_GGUF_FILE=...` |

**Supported LLMs:**
- Qwen3-4B (default, 4B parameters)
- Ministral 3B (FP8 text-only with dequantization)
- Any HuggingFace-compatible LLM
- BNB 4-bit quantized models (e.g., `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit`)

**Key Functions:**

```python
def enhance_prompt(user_prompt: str, instruction: str = "") -> str:
    """Enhance prompt for better image generation"""

def generate_prompt_variable_values(
    variable_name: str,
    context_prompt: str,
    count: int = 20
) -> list[str]:
    """Generate values for missing prompt variables"""
```

**Generation Parameters:** (Qwen3-recommended)
- `temperature=0.7`
- `top_p=0.8`
- `top_k=20`

**Special Support:**
- Ministral FP8 models (auto-detects and uses `FineGrainedFP8Config`)
- Outlines integration (constrained generation for guaranteed JSON structure)
- Automatic JSON parsing fallback for variable generation

---

### 6. Model Configuration: `model_config.py`

**Purpose:** Flexible model source configuration

**Configuration Storage:** `.env` file in project root

**Runtime Override System:**
```python
# UI can override config without modifying .env
set_override_config(
    image_mode="sdnq",
    llm_mode="hf_download",
    llm_repo="Qwen/Qwen3-4B"
)
clear_override_config()  # Revert to .env
```

**Configuration Classes:**

```python
@dataclass
class ImageModelConfig:
    mode: LoadingMode
    hf_repo: str = "Tongyi-MAI/Z-Image-Turbo"
    sdnq_model: str = "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32"
    hf_local_path: Optional[str] = None
    transformer_path: Optional[str] = None
    text_encoder_path: Optional[str] = None
    vae_path: Optional[str] = None

@dataclass
class LLMConfig:
    mode: LLMMode
    hf_repo: str = "Qwen/Qwen3-4B"
    hf_local_path: Optional[str] = None
    gguf_path: Optional[str] = None
    gguf_file: Optional[str] = None
```

**Validation:**
- Checks file existence for local paths
- Verifies required files for each mode
- Returns detailed error messages

---

### 7. Shared Types: `core/types.py`

**Purpose:** Pydantic models for type safety across CLI and Server

```python
class GenerationRequest(BaseModel):
    prompt: str
    count: int = 1
    width: int = 1024
    height: int = 1024
    seed: Optional[int] = None
    enhance: bool = False
    enhancement_instruction: str = ""

class ProgressEvent(BaseModel):
    stage: ProgressStage  # Literal type with 31+ stages
    message: str
    progress: Optional[int] = None  # 0-100
    data: Optional[dict] = None

class GenerationResult(BaseModel):
    success: bool
    images: list[str]
    final_prompts: list[str]
    errors: list[str]
    seeds_used: list[int]

class GpuInfo(BaseModel):
    available: bool
    device_name: Optional[str]
    allocated_gb: Optional[float]
    reserved_gb: Optional[float]
    total_gb: Optional[float]
    free_gb: Optional[float]
    error: Optional[str]
```

---

## Data Flow

### Request Flow (Server Mode)

```
Browser/GUI
    │
    ▼
GET /api/generate/stream?prompt=...&count=1&width=1024&height=1024
    │
    ▼
FastAPI handler (_generate_event_stream)
    │
    ├─→ Create GenerationRequest
    ├─→ Run generate() in ThreadPoolExecutor
    └─→ Stream ProgressEvents as SSE
         │
         ▼
core.generator.generate(request, on_progress=callback)
    │
    ├─→ Phase 1: LLM
    │    ├─→ load_prompt_vars()
    │    ├─→ _substitute_variables() [may call LLM]
    │    ├─→ _enhance_prompt() [if requested]
    │    └─→ unload_model()
    │
    ├─→ Phase 2: Image
    │    ├─→ generate_image() for each prompt
    │    └─→ save image + prompt.txt
    │
    └─→ Return GenerationResult
         │
         ▼
SSE: {"stage": "complete", "images": [...], "final_prompts": [...]}
```

### Request Flow (CLI Mode)

```
User Input: "a __animal__ in space : x3,h512,w512"
    │
    ▼
parse_batch_params()
    │
    ├─→ prompt: "a __animal__ in space"
    └─→ params: {count: 3, height: 512, width: 512}
    │
    ▼
core.generator.generate(...)
    │
    └─→ [Same two-phase pipeline as server mode]
    │
    ▼
Rich progress display in terminal
    │
    └─→ Image preview (term-image)
```

---

## GPU Memory Management

### Memory Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Initial State (Clean)                      │
│                      GPU: 0GB allocated                       │
└──────────────────────────┬────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Phase 1: LLM Loading                        │
│           Qwen3-4B: ~4GB (BNB 4-bit) or ~8GB (bf16)          │
├─────────────────────────────────────────────────────────────┤
│ • Variable substitution                                      │
│ • Missing variable generation                                │
│ • Prompt enhancement                                         │
└──────────────────────────┬────────────────────────────────────┘
                           │
                           ▼
                    [MEMORY FENCE]
                  Unload LLM + clear cache
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│               Phase 2: Image Model Loading                   │
│    Z-Image-Turbo: ~12GB (SDNQ) or ~24GB (bf16)              │
├─────────────────────────────────────────────────────────────┤
│ • Image generation (9 diffusion steps)                       │
│ • Save images + prompts                                      │
└──────────────────────────┬────────────────────────────────────┘
                           │
                           ▼
                    [Optional Unload]
                  /api/unload or /unload command
```

### Automatic Unloading

**LLM → Image:** `image_generator.py:_load_pipeline()` calls `llm_provider.unload_model()`

**Image → LLM:** `llm_provider.py:_load_model()` calls `image_generator.unload_pipeline()`

**Manual Unload:** `/api/unload` endpoint or `/unload` CLI command

---

## API Design

### REST Principles

- **Resource-oriented URLs:** `/api/images`, `/api/variables`
- **Standard HTTP methods:** GET for queries, POST for actions
- **JSON request/response:** All data serialized as JSON
- **Pydantic validation:** Type-safe request/response models
- **Error handling:** HTTP status codes + error messages

### SSE Streaming

**Why SSE over WebSockets?**
- Simpler client (native EventSource API)
- Automatic reconnection
- Better for one-way streaming (server → client)
- Integrates with HTTP infrastructure (proxies, load balancers)

**SSE Message Format:**
```
data: {"stage": "diffusion_step", "message": "...", "progress": 50}\n\n
```

**Keepalive:** 1-second ping to prevent buffering

---

## Model Loading Strategies

### SDNQ Quantization (Recommended)

**Advantages:**
- Cross-platform (works on Windows/Linux/Mac)
- ~12GB VRAM (vs ~24GB for full precision)
- Minimal quality loss
- Fast loading

**Implementation:**
```python
from sdnq import SDNQConfig  # Registers 'sdnq' quantization type
pipe = diffusers.ZImagePipeline.from_pretrained(
    "Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32",
    torch_dtype=torch.bfloat16
)
```

### HuggingFace Download

**Advantages:**
- Automatic model downloading
- Caching in `~/.cache/huggingface/hub`
- Support for private/gated models

**Implementation:**
```python
pipe = ZImagePipeline.from_pretrained(
    "Tongyi-MAI/Z-Image-Turbo",
    torch_dtype=torch.bfloat16,
    quantization_config=PipelineQuantizationConfig(...)  # Optional BNB 4-bit
)
```

### Components Mode (ComfyUI Interop)

**Advantages:**
- Use existing ComfyUI model files
- Share models between ComfyUI and z-Explorer
- No duplicate downloads

**Implementation:**
- Converts ComfyUI key naming conventions
- Splits concatenated QKV tensors
- Uses accelerate for tensor-by-tensor loading

---

## Testing Strategy

### Test Structure

```
tests/
├── test_cli.py              # CLI argument parsing
├── test_core_generator.py   # Generation workflow
├── test_image_generator.py  # Image model interface
├── test_llm_provider.py     # LLM interface
├── test_model_config.py     # Configuration validation
└── test_server/
    ├── test_endpoints.py    # API endpoints
    └── test_sse.py          # SSE streaming
```

### Test Tools

- **pytest:** Test runner
- **pytest-asyncio:** Async test support
- **pytest-cov:** Coverage reporting
- **Mocking:** Mock model loading (avoid downloading models in tests)

### Coverage Target

Target: 80% (not yet enforced, Phase 5 goal)

Current focus: Critical path tests (generation workflow, API endpoints)

---

## Configuration Management

### Environment Variables

**Image Model:**
```bash
Z_IMAGE_MODE=sdnq|hf_download|hf_local|components
Z_IMAGE_SDNQ=Disty0/Z-Image-Turbo-SDNQ-uint4-svd-r32  # SDNQ repo
Z_IMAGE_HF=/path/to/local/clone                        # HF local path
Z_IMAGE_TRANSFORMER=/path/to/transformer.safetensors   # Components
Z_IMAGE_TEXT_ENCODER=/path/to/text_encoder.safetensors
Z_IMAGE_VAE=/path/to/vae.safetensors
```

**LLM:**
```bash
LLM_MODE=z_image|hf_download|hf_local|gguf
LLM_REPO=Qwen/Qwen3-4B                  # HF repo
LLM_PATH=/path/to/local/model           # Local path or GGUF repo
LLM_GGUF_FILE=model-q4_0.gguf           # GGUF filename
```

**Output:**
```bash
LOCAL_OUTPUT_DIR=./output               # Image output directory
```

### First-Run Setup

1. **No .env file:** Runs setup wizard (`setup_wizard.py`)
2. **User selects configuration preset:**
   - Quick Start (SDNQ + BNB quantized LLM, ~12GB)
   - Full Download (HF download, ~24GB)
   - Custom (advanced options)
3. **Wizard creates .env file**
4. **Application starts**

### Runtime Override (GUI)

Settings dialog can override config without modifying .env:

```python
# POST /api/settings/models
{
  "image_mode": "sdnq",
  "llm_mode": "hf_download",
  "llm_repo": "Qwen/Qwen3-4B"
}

# Models reload with new config
# POST /api/models/reload
```

---

## Logging

### loguru Configuration

**Console (stderr):**
```
<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}
```

**File (logs/server_YYYY-MM-DD.log):**
- Rotation: 1 day
- Retention: 7 days
- Level: DEBUG

**Key Log Points:**
- Model loading/unloading
- Generation start/complete
- Phase transitions
- Memory management events
- API requests/responses

---

## Error Handling

### Model Loading Errors

- Missing dependencies → Clear error message with install instructions
- Configuration errors → Detailed validation messages
- File not found → Path and required files listed

### Generation Errors

- Prompt too long → Truncate or reject
- Out of memory → Attempt to unload and retry
- Model crash → Capture error, unload models, return error response

### API Errors

- 400 Bad Request → Validation errors (Pydantic)
- 404 Not Found → Invalid endpoint or resource
- 500 Internal Server Error → Unexpected errors (logged)

---

## Security Considerations

### Local-First Design

- No external API calls (except HuggingFace downloads)
- No telemetry or analytics
- No authentication required (local-only server)
- CORS: Allow all origins (safe for local desktop app)

### Model Trust

- Models downloaded from trusted sources (HuggingFace)
- Git dependencies pinned to specific repositories
- No code execution from untrusted sources

### File System Access

- Output directory configurable via environment
- File operations restricted to output directory
- No arbitrary file path access from API

---

## Performance Considerations

### Inference Speed

**Image Generation:**
- Z-Image-Turbo: 9 diffusion steps (~2-5 seconds on RTX 4090)
- Turbo model requires `guidance_scale=0.0`

**LLM Text Generation:**
- Qwen3-4B: ~100-200 tokens/second (RTX 4090)
- Variable generation: ~20 values in 2-3 seconds
- Prompt enhancement: 1-2 seconds

### Batch Processing

- **Phase 1:** All prompts prepared sequentially (LLM loaded once)
- **Phase 2:** Images generated sequentially (diffusion pipeline)
- **Memory trade-off:** Could parallelize with multiple GPUs, but single-GPU design prioritizes accessibility

### Model Caching

- **HuggingFace cache:** `~/.cache/huggingface/hub`
- **Pipeline cache:** Global variable (lazy loading)
- **Prompt variables:** Loaded once at startup, cached in memory

---

## Future Enhancements

### Planned Features

1. **Multi-GPU support** (parallel image generation)
2. **ControlNet integration** (image-to-image)
3. **LoRA support** (fine-tuned models)
4. **Video generation** (frame-by-frame)
5. **Custom schedulers** (DPM++, DDIM, etc.)

### Technical Debt

1. **Test coverage** (target: 80%)
2. **Type hints** (some dynamic loading lacks hints)
3. **Documentation** (API reference, contribution guide)
4. **Error recovery** (automatic retry on OOM)

---

## Brownfield Development Notes

### Critical Constraints

1. **Two-phase pipeline is non-negotiable:** Both models cannot load simultaneously on most consumer GPUs
2. **Git dependencies required:** PyPI versions lack Z-Image-Turbo support
3. **Python 3.12 required:** Uses modern type hints and Pydantic v2

### Extension Points

1. **New LLM support:** Add mode to `LLMConfig`, implement in `llm_provider.py`
2. **New image model:** Add mode to `ImageModelConfig`, implement in `image_generator.py`
3. **New API endpoints:** Add to `server.py`, update OpenAPI docs
4. **New CLI commands:** Add to `cli.py:handleCommand`

### Code Organization Principles

- **Single source of truth:** `core/generator.py` for generation logic
- **Shared types:** `core/types.py` for cross-module contracts
- **Lazy loading:** Models loaded on first use, not at import
- **Dependency injection:** Callbacks for progress tracking

---

## References

- **Project Repository:** https://github.com/pyros-projects/z-Explorer
- **Z-Image-Turbo:** https://huggingface.co/Tongyi-MAI/Z-Image-Turbo
- **SDNQ Quantization:** https://github.com/Disty0/sdnq
- **Qwen3-4B:** https://huggingface.co/Qwen/Qwen3-4B
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **diffusers Library:** https://huggingface.co/docs/diffusers

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
**For AI Agents:** This document provides comprehensive context for brownfield PRD work on z-Explorer backend/CLI components.
