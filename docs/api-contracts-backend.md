# API Contracts - Backend

**Generated:** 2025-12-02
**Part:** Backend (`src/z_explorer/`)
**Server:** FastAPI with Uvicorn (ASGI)
**Base URL:** `http://localhost:7680` (default)

## API Overview

The z-Explorer backend exposes a RESTful API with Server-Sent Events (SSE) for real-time generation progress. All endpoints are prefixed with `/api/` except the root and GUI serving endpoints.

## Endpoints

### Health & Status

#### `GET /api/health`
**Purpose:** Health check endpoint
**Response:** `{ "status": "ok" }`
**Use Case:** Monitoring, readiness checks

#### `GET /api/gpu`
**Purpose:** Get GPU availability and VRAM status
**Response Model:** `GpuInfo`
```json
{
  "available": boolean,
  "device_name": string,
  "vram_total": number,
  "vram_free": number
}
```

### Variables & Configuration

#### `GET /api/variables`
**Purpose:** List available prompt variables
**Response Model:** `VariablesResponse`
```json
{
  "variables": ["__animal__", "__art_style__", ...]
}
```
**Use Case:** GUI autocomplete, prompt building

#### `GET /api/config`
**Purpose:** Get current model configuration
**Response Model:** `ModelConfigResponse`
```json
{
  "image_model": {
    "mode": string,
    "repo": string
  },
  "llm": {
    "mode": string,
    "repo": string
  }
}
```

### Setup & Download

#### `GET /api/setup/status`
**Purpose:** Check model download status
**Response Model:** `SetupStatusResponse`
```json
{
  "image_model_ready": boolean,
  "llm_ready": boolean,
  "needs_setup": boolean
}
```

#### `GET /api/setup/download`
**Purpose:** SSE stream for model download progress
**Response:** Server-Sent Events stream
**Events:**
- `progress`: Download progress updates
- `complete`: Download finished
- `error`: Download failed

### Model Management

#### `POST /api/unload`
**Purpose:** Unload models from GPU to free memory
**Response Model:** `UnloadResponse`
```json
{
  "success": boolean,
  "message": string
}
```

#### `POST /api/settings/models`
**Purpose:** Update model configuration at runtime
**Request Body:**
```json
{
  "image_mode": string,
  "image_repo": string,
  "llm_mode": string,
  "llm_repo": string
}
```
**Response Model:** `ModelSettingsResponse`

#### `POST /api/settings/models/test`
**Purpose:** Test model configuration without saving
**Response Model:** `ModelTestResponse`

#### `POST /api/settings/models/check-cache`
**Purpose:** Check if models are cached locally
**Response Model:** `ModelCacheCheckResponse`
```json
{
  "image_model_cached": boolean,
  "llm_cached": boolean
}
```

#### `GET /api/settings/models/download`
**Purpose:** SSE stream for model download with settings override
**Response:** Server-Sent Events stream

#### `POST /api/models/reload`
**Purpose:** Reload models with current configuration
**Response Model:** `ModelReloadResponse`

### Image Management

#### `GET /api/images`
**Purpose:** List generated images
**Response Model:** `ImagesResponse`
```json
{
  "images": [
    {
      "filename": string,
      "path": string,
      "url": string,
      "timestamp": number
    }
  ]
}
```

### Generation Endpoints

#### `GET /api/generate/stream`
**Purpose:** Generate images with real-time progress via SSE
**Query Parameters:**
- `prompt`: Image generation prompt (required)
- Additional generation parameters (width, height, steps, etc.)

**Response:** Server-Sent Events stream
**Events:**
- `phase1_start`: LLM phase starting
- `phase1_progress`: LLM processing
- `phase1_complete`: LLM phase done
- `phase2_start`: Image generation starting
- `phase2_progress`: Diffusion progress
- `image_generated`: Single image complete
- `batch_complete`: All images done
- `error`: Generation failed

**Example SSE Flow:**
```
event: phase1_start
data: {"message": "Processing prompts with LLM..."}

event: phase1_complete
data: {"enhanced_prompts": ["..."], "count": 1}

event: phase2_start
data: {"message": "Loading image model..."}

event: phase2_progress
data: {"step": 5, "total_steps": 20, "progress": 0.25}

event: image_generated
data: {"path": "output/image_001.png", "index": 0}

event: batch_complete
data: {"images": [...], "total": 1}
```

#### `POST /api/generate`
**Purpose:** Generate images without SSE stream
**Request Body:** Generation parameters
**Response:** Generation results (non-streaming)

### Static Files

#### `GET /`
**Purpose:** Serve GUI index.html
**Response:** HTML page

#### `GET /output/{filename}`
**Purpose:** Serve generated images
**Response:** Image file (PNG)

## Authentication

Currently no authentication is required. All endpoints are accessible without credentials. This is suitable for local-only deployment.

## Error Handling

All endpoints return standard HTTP status codes:
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `500 Internal Server Error`: Server-side error

Error responses include:
```json
{
  "detail": "Error message"
}
```

## Integration with GUI

The GUI integrates with these endpoints:
- **SSE Connection:** `/api/generate/stream` for real-time generation
- **Variables:** `/api/variables` for prompt autocomplete
- **Images:** `/api/images` for gallery display
- **Settings:** `/api/settings/models` for configuration
- **Setup:** `/api/setup/download` for first-run setup

See [Integration Architecture](./integration-architecture.md) for detailed integration patterns.
