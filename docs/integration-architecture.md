# Integration Architecture

**Generated:** 2025-12-02
**Project Type:** Multi-part Monolith
**Integration Pattern:** Embedded Frontend with REST + SSE

## Integration Overview

z-Explorer integrates its Backend and GUI parts through a server-side rendering approach where the FastAPI backend serves the built Svelte GUI and provides API endpoints for dynamic functionality.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                        │
├─────────────────────────────────────────────────────────────┤
│  Svelte GUI (http://localhost:7680/)                       │
│  ┌────────────┐  ┌──────────┐  ┌──────────┐              │
│  │  FakeCLI   │  │ Gallery  │  │ Settings │              │
│  └──────┬─────┘  └────┬─────┘  └────┬─────┘              │
│         │             │              │                      │
│         └─────────────┴──────────────┘                     │
│                       │                                     │
│                  API Client Layer                           │
│                       │                                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        │ HTTP/SSE
                        ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Server (Port 7680)                     │
├─────────────────────────────────────────────────────────────┤
│  Static File Serving    │    REST API    │    SSE Stream   │
│  (/gui/dist/)          │   (/api/*)    │  (/api/generate) │
└───────────┬─────────────┴────────┬───────┴───────┬──────────┘
            │                      │                │
            ▼                      ▼                ▼
   ┌───────────────┐      ┌──────────────┐  ┌─────────────┐
   │  GUI Assets   │      │  Endpoints   │  │ SSE Handler │
   └───────────────┘      └──────┬───────┘  └──────┬──────┘
                                  │                 │
                                  ▼                 ▼
                          ┌───────────────────────────────┐
                          │   Core Generation Pipeline     │
                          │   (core/generator.py)         │
                          ├───────────────────────────────┤
                          │  Phase 1: LLM Processing      │
                          │  Phase 2: Image Generation    │
                          └───────────────────────────────┘
```

## Integration Points

### 1. Static GUI Serving

**From:** Backend (`server.py`)
**To:** GUI (`gui/dist/`)
**Type:** Static file serving
**Protocol:** HTTP

The FastAPI server serves the built Svelte application:

```python
# server.py
from fastapi.responses import FileResponse

@app.get("/", include_in_schema=False)
async def serve_gui():
    return FileResponse(gui_index_path)
```

**Build Process:**
1. GUI built with `npm run build` → `gui/dist/`
2. `dist/` bundled into Python package via `pyproject.toml`
3. Backend serves `dist/index.html` at root path

### 2. REST API Communication

**From:** GUI (Svelte components)
**To:** Backend (`/api/*` endpoints)
**Type:** REST API calls
**Protocol:** HTTP (fetch API)

**Example GUI → Backend Call:**

```typescript
// GUI: src/lib/services/settingsService.ts
async function updateModelSettings(settings: ModelSettings) {
  const response = await fetch('/api/settings/models', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(settings)
  });
  return response.json();
}
```

**Key API Integrations:**

| GUI Component | Backend Endpoint | Purpose |
|---------------|------------------|---------|
| FakeCLI | `/api/variables` | Autocomplete variables |
| FakeCLI | `/api/generate/stream` | Generate images (SSE) |
| Gallery | `/api/images` | List generated images |
| Gallery | `/output/{filename}` | Display images |
| Settings | `/api/settings/models` | Update config |
| Setup | `/api/setup/download` | Model download (SSE) |

### 3. Server-Sent Events (SSE) Stream

**From:** Backend (`/api/generate/stream`, `/api/setup/download`)
**To:** GUI (EventSource API)
**Type:** Real-time streaming
**Protocol:** SSE over HTTP

**Example SSE Integration:**

```typescript
// GUI: App.svelte
const eventSource = new EventSource(`/api/generate/stream?prompt=${prompt}`);

eventSource.addEventListener('phase1_start', (e) => {
  // LLM phase starting
});

eventSource.addEventListener('phase2_progress', (e) => {
  const data = JSON.parse(e.data);
  progress = data.progress * 100;
});

eventSource.addEventListener('image_generated', (e) => {
  const data = JSON.parse(e.data);
  images.push(data.path);
});

eventSource.addEventListener('batch_complete', (e) => {
  eventSource.close();
  // Generation complete
});
```

**SSE Events Flow:**

```
GUI                          Backend
 │                             │
 ├─ EventSource created ──────►│
 │                             │
 │◄── phase1_start ────────────┤ (LLM processing)
 │◄── phase1_complete ─────────┤
 │                             │
 │◄── phase2_start ────────────┤ (Image generation)
 │◄── phase2_progress ─────────┤ (20%, 40%, 60%...)
 │◄── image_generated ─────────┤ (Image ready)
 │◄── batch_complete ──────────┤ (All done)
 │                             │
 ├─ Close EventSource          │
```

### 4. Image Display Integration

**From:** GUI (Gallery component)
**To:** Backend (`/output/{filename}`)
**Type:** Static file serving
**Protocol:** HTTP

Generated images are served directly by the backend:

```typescript
// GUI: Gallery.svelte
<img src="/output/{filename}" alt="Generated image" />
```

## Data Flow

### Image Generation Flow

```
User Input (GUI)
  │
  ▼
FakeCLI Component
  │
  ├─ Parse prompt
  ├─ Extract parameters (width, height, steps)
  │
  ▼
API Call: /api/generate/stream (SSE)
  │
  ▼
Backend: server.py
  │
  ├─ Validate parameters
  ├─ Emit: phase1_start
  │
  ▼
Core Generator (core/generator.py)
  │
  ├─ Phase 1: LLM Processing
  │   ├─ Load Qwen3-4B
  │   ├─ Enhance prompts
  │   ├─ Unload LLM
  │   └─ Emit: phase1_complete
  │
  ├─ Phase 2: Image Generation
  │   ├─ Load Z-Image-Turbo
  │   ├─ Generate images
  │   ├─ Save to output/
  │   └─ Emit: image_generated
  │
  ▼
GUI: EventSource Handler
  │
  ├─ Update progress bar
  ├─ Add images to gallery
  └─ Display complete
```

## Shared State Management

### Backend State
- **GPU Memory:** Tracks loaded models (LLM vs Image)
- **Model Config:** Current model configuration
- **Output Directory:** Generated images location

### GUI State
- **Svelte Stores:** Settings persistence
- **Component State:** Gallery layout, selected images
- **Session State:** Current generation progress

### Synchronization
- **Settings:** GUI → Backend via `/api/settings/models`
- **Images:** Backend → GUI via `/api/images` polling
- **Progress:** Backend → GUI via SSE events

## Security Considerations

**Current State:** No authentication (local-only deployment)

**Future Considerations:**
- Add API key authentication for remote access
- CORS configuration for cross-origin requests
- Rate limiting for API endpoints

## Deployment Integration

The multi-part structure is deployed as a single unit:

1. **Build GUI:** `cd gui && npm run build`
2. **Package:** GUI dist bundled into Python package
3. **Run:** Single command `uv run z-explorer` starts both backend and GUI
4. **Access:** Navigate to `http://localhost:7680`

## Error Handling

### GUI Error Handling
```typescript
try {
  const response = await fetch('/api/generate/stream');
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
} catch (error) {
  // Display error to user
  console.error('Generation failed:', error);
}
```

### Backend Error Handling
```python
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)}
    )
```

## Performance Considerations

- **SSE Efficiency:** Events sent only when state changes
- **Image Serving:** Static file serving optimized by FastAPI
- **Model Loading:** Two-phase approach prevents GPU OOM
- **Build Optimization:** Vite produces optimized bundles

## Testing Integration

- **Backend Tests:** `pytest` for API endpoints
- **GUI Tests:** `vitest` for component logic
- **Integration Tests:** Test SSE flows end-to-end

See [Development Guide - Backend](./development-guide-backend.md) for testing details.
