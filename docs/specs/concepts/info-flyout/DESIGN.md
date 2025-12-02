# Z-Explorer UX Improvements — Design Document

This document covers four interconnected features that improve the Z-Explorer experience:

1. **Info Flyout Panel** — On-demand metadata for generated images
2. **Gallery Search** — Full-text search over prompts
3. **LiteLLM Integration** — Unified LLM provider support for the entire app
4. **Variable Editor** — Standalone app for managing variable lists with AI expansion

---

# Part 1: Info Flyout Panel

## Overview

Replace the static prompt display below the lightbox image with an **on-demand info panel** that slides in from the right when the user clicks an info button. This gives the generated image maximum screen real estate by default while keeping all metadata one click away.

## Problem Statement

Currently, the lightbox shows the prompt below the image, which:
1. **Steals vertical space** from the image — the star of the show
2. **Always visible** even when user just wants to admire the art
3. **Limited to prompt only** — no room for other useful metadata
4. **Only stores the final prompt** — loses the original template with variables

## Solution

### Info Button Overlay

A small `ⓘ` button positioned in the bottom-right corner of the image:
- Semi-transparent background with blur
- Subtle purple border matching brand
- Scales on hover for affordance
- Non-intrusive, doesn't distract from art

### Slide-in Panel

When clicked, a panel slides in from the right edge:
- **Width**: 320px (fixed)
- **Animation**: Slide from right, 300ms ease-out
- **Background**: Semi-transparent dark with blur
- **Border**: Left edge has purple accent border

### Panel Contents

```
┌─────────────────────────────┐
│ Image Info              [×] │  ← Header with close button
├─────────────────────────────┤
│ 📝 ORIGINAL PROMPT          │  ← The template user typed
│ ┌─────────────────────────┐ │
│ │ a __animal__ in a       │ │
│ │ magical forest > enhance│ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ 📜 FINAL PROMPT             │  ← After substitution + enhancement
│ ┌─────────────────────────┐ │
│ │ A cute cat in a vibrant │ │
│ │ 2D digital artwork...   │ │
│ └─────────────────────────┘ │
├─────────────────────────────┤
│ ┌───────┐ ┌───────┐         │  ← Metadata grid
│ │📐 Size│ │🎲 Seed│         │
│ │1024²  │ │543769 │         │
│ └───────┘ └───────┘         │
│ ┌───────┐ ┌───────┐         │
│ │📅 Date│ │💾 File│         │
│ │Dec 2  │ │1.2 MB │         │
│ └───────┘ └───────┘         │
├─────────────────────────────┤
│ [📋 Copy Prompt] [🔄 Regen] │  ← Action buttons
└─────────────────────────────┘
```

## Data Model Changes

### Current `ImageData` Interface

```typescript
interface ImageData {
  url: string;
  prompt?: string;        // Only stores final prompt
  aspectRatio?: number;
}
```

### New `ImageData` Interface

```typescript
interface ImageData {
  url: string;
  originalPrompt?: string;  // Template as user typed: "a __animal__ > enhance"
  finalPrompt?: string;     // After substitution + enhancement
  seed?: number;
  width?: number;
  height?: number;
  createdAt?: string;       // ISO timestamp
  fileSize?: number;        // Bytes
  model?: string;           // "sdnq" | "hf" etc (future)
  enhanced?: boolean;       // Was > operator used?
}
```

### Backend Changes Required

The `/api/generate/stream` SSE events need to include both prompts:

```python
# In generator.py, when emitting image_saved event
{
    "stage": "image_saved",
    "path": "/output/z_image_xxx.png",
    "data": {
        "original_prompt": "a __animal__ > enhance",  # NEW
        "final_prompt": "A cute cat in vibrant 2D...",
        "seed": 543769263,
        "width": 1024,
        "height": 1024
    }
}
```

### Metadata JSON Sidecar

Save a `.json` file alongside each image:

```
output/
  z_image_20251202_091338_543769263.png
  z_image_20251202_091338_543769263.json  ← metadata sidecar
```

Contents:
```json
{
  "original_prompt": "a __animal__ in a magical forest > enhance",
  "final_prompt": "A cute cat in a vibrant 2D digital artwork style...",
  "seed": 543769263,
  "width": 1024,
  "height": 1024,
  "created_at": "2025-12-02T09:13:38Z",
  "model": "sdnq",
  "enhanced": true
}
```

This enables:
- Metadata survives app restarts (not just in-session memory)
- Gallery can load metadata for existing images
- **Search functionality** (see Part 2)
- Future: filter by seed, date, model

## UI Components

### New Components

1. **`InfoButton.svelte`** — The `ⓘ` overlay button
2. **`InfoPanel.svelte`** — The slide-in panel with all content

### Modified Components

1. **`App.svelte`** — Add InfoButton to lightbox, conditionally render InfoPanel
2. **`Gallery.svelte`** — Pass extended ImageData to selection event

## Interaction Design

| Action | Result |
|--------|--------|
| Click image in gallery | Open lightbox (existing) |
| Click `ⓘ` button | Panel slides in from right |
| Click `×` on panel | Panel slides out |
| Click outside panel (on image) | Panel slides out |
| Press `Escape` | Close panel (if open) OR close lightbox |
| Press `i` key | Toggle panel open/close |

### Action Buttons

| Button | Action |
|--------|--------|
| 📋 Copy Prompt | Copy **final prompt** to clipboard, show toast |
| 📋 Copy Original | Copy **original prompt** to clipboard (the reusable one) |
| 🔄 Regenerate | Pre-fill CLI with original prompt (future) |
| 📂 Open Folder | Open containing folder in file manager (future) |
| 🗑️ Delete | Delete image with confirmation (future) |

## Animation Specs

### Panel Slide-In
```css
@keyframes slideIn {
  from { transform: translateX(100%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}
animation: slideIn 0.3s ease-out;
```

### Panel Slide-Out
```css
@keyframes slideOut {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(100%); opacity: 0; }
}
animation: slideOut 0.2s ease-in;
```

### Info Button Hover
```css
.info-btn:hover {
  background: rgba(139, 92, 246, 0.3);
  border-color: #a855f7;
  transform: scale(1.1);
}
transition: all 0.2s ease;
```

---

# Part 2: Gallery Search

## Overview

Add full-text search over image prompts, accessible via:
- **CLI command**: `/search <query>`
- **UI**: Search input in gallery header

## Problem Statement

As users generate hundreds of images, finding specific ones becomes impossible. "Where's that emo girl with the corset?" requires scrolling through everything.

## Solution

### Search Scope

Search matches against:
1. **Original prompt** — The template with variables (`a __animal__ in forest`)
2. **Final prompt** — The substituted/enhanced result (`A cute fox in enchanted forest...`)

Case-insensitive, substring matching. Simple and fast.

### CLI Interface

```
/search emo corset
```

Returns:
```
🔍 Found 3 images matching "emo corset":
  1. z_image_20251202_081226_3534366672.png
     "Drawing of a beautiful emo woman wearing a sleek black lace corset..."
  2. z_image_20251202_081217_5437692633.png
     "...emo woman in a flat 2D style, wearing a sleek sheer black dress..."
  3. z_image_20251201_143052_9182736455.png
     "...dark aesthetic, corset with intricate silver detailing..."
```

### UI Interface

Add search box to Gallery header:

```
┌──────────────────────────────────────────────────────────┐
│ 🔍 [Search prompts...                    ]  Gallery (47) │
└──────────────────────────────────────────────────────────┘
```

- Real-time filtering as you type (debounced 300ms)
- Shows match count
- `Esc` clears search
- Empty search shows all images

### Backend API

New endpoint:

```
GET /api/images/search?q=emo+corset
```

Response:
```json
{
  "query": "emo corset",
  "count": 3,
  "images": [
    {
      "url": "/output/z_image_xxx.png",
      "original_prompt": "...",
      "final_prompt": "...",
      "match_field": "final_prompt",
      "snippet": "...emo woman wearing a sleek black lace corset..."
    }
  ]
}
```

### Implementation

Search reads from `.json` sidecar files (created in Part 1). For each image:

```python
def matches(image_meta: dict, query: str) -> bool:
    query = query.lower()
    original = (image_meta.get("original_prompt") or "").lower()
    final = (image_meta.get("final_prompt") or "").lower()
    return query in original or query in final
```

Simple substring search is sufficient for v1. Future: fuzzy matching, semantic search.

---

# Part 3: LiteLLM Integration

## Overview

Add LiteLLM as a new `LLM_MODE` option, enabling access to 100+ LLM providers (OpenAI, Anthropic, Ollama, etc.) using a unified interface. This applies to the **entire app** — prompt enhancement, variable generation, and any future LLM features.

## Current State

```bash
# Current env vars
LLM_MODE=hf_download          # or z_image, hf_local, gguf
LLM_REPO=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit
```

The app only supports local models via HuggingFace Transformers.

## New Configuration

### Rename `LLM_REPO` → `LLM_MODEL`

More accurate — it's a model identifier, not always a repo.

```bash
# Local model via Transformers
LLM_MODE=hf_download
LLM_MODEL=unsloth/Qwen3-4B-Instruct-2507-bnb-4bit

# LiteLLM — external APIs
LLM_MODE=litellm
LLM_MODEL=openai/gpt-4o-mini
```

### No Custom API Key Variables!

LiteLLM reads standard environment variables for each provider. Users set the provider's expected env vars:

```bash
# OpenAI
LLM_MODE=litellm
LLM_MODEL=openai/gpt-4o-mini
OPENAI_API_KEY=sk-...

# Anthropic
LLM_MODE=litellm
LLM_MODEL=anthropic/claude-3-haiku-20240307
ANTHROPIC_API_KEY=sk-ant-...

# Azure OpenAI
LLM_MODE=litellm
LLM_MODEL=azure/my-deployment
AZURE_API_KEY=...
AZURE_API_BASE=https://my-resource.openai.azure.com

# Ollama (local, no key needed)
LLM_MODE=litellm
LLM_MODEL=ollama/llama3

# Any OpenAI-compatible API
LLM_MODE=litellm
LLM_MODEL=openai/my-model
OPENAI_API_KEY=...
OPENAI_API_BASE=http://localhost:1234/v1
```

See full provider list: https://docs.litellm.ai/docs/providers

## Implementation

### New Dependency

```toml
# pyproject.toml
dependencies = [
    "litellm>=1.0.0",
    # ...
]
```

### LLM Provider Abstraction

Create a unified interface in `llm_provider.py`:

```python
from enum import Enum
from typing import Optional
import os

class LLMMode(Enum):
    HF_DOWNLOAD = "hf_download"
    HF_LOCAL = "hf_local"
    Z_IMAGE = "z_image"
    GGUF = "gguf"
    LITELLM = "litellm"  # NEW

class LLMProvider:
    def __init__(self):
        self.mode = LLMMode(os.getenv("LLM_MODE", "hf_download"))
        self.model = os.getenv("LLM_MODEL", "unsloth/Qwen3-4B-Instruct-2507-bnb-4bit")
        self._local_model = None
    
    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        if self.mode == LLMMode.LITELLM:
            return self._generate_litellm(prompt, max_tokens)
        else:
            return self._generate_local(prompt, max_tokens)
    
    def _generate_litellm(self, prompt: str, max_tokens: int) -> str:
        import litellm
        response = litellm.completion(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def _generate_local(self, prompt: str, max_tokens: int) -> str:
        # Existing Transformers-based generation
        ...
```

### Benefits

| Feature | Local (Transformers) | LiteLLM |
|---------|---------------------|---------|
| Offline | ✅ | ❌ (except Ollama) |
| Cost | Free | Pay per token |
| Quality | Good (Qwen3-4B) | Excellent (GPT-4, Claude) |
| Speed | GPU-dependent | Fast (API) |
| VRAM | ~8GB | 0 |
| Setup | Download models | Just API key |

### Use Cases

| Use Case | Recommended Mode |
|----------|------------------|
| Offline/air-gapped | `hf_download` |
| Low VRAM (<8GB) | `litellm` with cheap model |
| Best quality prompts | `litellm` with `gpt-4o` |
| Privacy-conscious | `hf_download` or `ollama/` |
| Variable expansion (creative) | `litellm` with `gpt-4o-mini` |

## Migration

### Breaking Change: `LLM_REPO` → `LLM_MODEL`

1. Update `model_config.py` to read `LLM_MODEL` with fallback to `LLM_REPO`
2. Update `env.example` and docs
3. Deprecation warning if `LLM_REPO` is set

```python
# Backward compatibility
llm_model = os.getenv("LLM_MODEL") or os.getenv("LLM_REPO")
if os.getenv("LLM_REPO") and not os.getenv("LLM_MODEL"):
    warnings.warn("LLM_REPO is deprecated, use LLM_MODEL instead")
```

## Setup Wizard Integration

The setup wizard should offer LiteLLM as an option:

```
LLM Configuration:
  ○ Local (Qwen3-4B) — Runs on your GPU, ~8GB VRAM, offline
  ○ Cloud API (LiteLLM) — Use OpenAI, Anthropic, etc.

[If Cloud API selected]
Provider: [OpenAI ▼]
Model: [gpt-4o-mini ▼]
API Key: [sk-...                    ]
         ℹ️ Get your key at platform.openai.com/api-keys
```

---

# Part 4: Variable Editor

## Overview

A **standalone sub-application** at `/var-editor` for managing variable lists with AI-powered expansion. Accessible via:
- **CLI command**: `/vars` — opens browser to `/var-editor`
- **Direct URL**: `http://localhost:8345/var-editor`

## Why Separate App?

1. **Full screen real estate** — Three-panel layout needs space
2. **Different workflow** — You curate variables, then return to generating
3. **Future-proof** — Establishes routing pattern for `/settings`, `/gallery`, etc.

## Architecture

```
localhost:8345/           → Main app (Gallery + CLI)
localhost:8345/var-editor → Variable Editor app
```

Both served by same FastAPI backend, routed in Svelte.

**Important:** Variable Editor uses the **same LLM configuration** as the main app (`LLM_MODE` + `LLM_MODEL`). No separate config.

## Layout

```
┌─────────────┬────────────────────────────────┬──────────────────┐
│  SIDEBAR    │         EDITOR                 │    AI PANEL      │
│             │                                │                  │
│ 🔍 Search   │  # Classic styles              │ ✨ AI Expansion  │
│             │  SamDoesArt, soft pastels      │                  │
│ 🐾 animal   │  Studio Ghibli, hand-painted   │ How many? [20]   │
│ 🎨 art_style│  Makoto Shinkai, dramatic      │                  │
│ 👗 outfit   │                                │ Guidance:        │
│ 💇 hair     │  # Painterly                   │ [more anime...] │
│ 🎭 emotion  │  oil painting, brushstrokes    │                  │
│             │  watercolor, soft edges        │ [✨ Generate]    │
│ [+ New]     │                                │                  │
│             │                                │ ┌──────────────┐ │
│             │                                │ │ Preview:     │ │
│             │                                │ │ ukiyo-e...   │ │
│             │                                │ │ art deco...  │ │
│             │                                │ │ pixel art... │ │
│             │                                │ └──────────────┘ │
│             │                                │ [🔄] [✅ Add]    │
├─────────────┴────────────────────────────────┴──────────────────┤
│ Modified · 23 items · Ctrl+S Save · Ctrl+G Generate · Esc Close │
└─────────────────────────────────────────────────────────────────┘
```

## Sidebar (Variable List)

- Search/filter variables
- List all `.txt` files from variables directory
- Show icon (auto-assigned or custom), name, item count
- Click to select and load into editor
- "New Variable" button at bottom

## Editor (Center Panel)

- Full text editor with line numbers
- One value per line
- **Comments with `#`** — Sent to AI for context steering!
- Syntax highlighting (values vs comments)
- Standard editor shortcuts (Ctrl+S save, Ctrl+Z undo)

### Comment-Driven AI Generation

Comments are powerful. They steer the AI:

```
# Anime-inspired digital art styles
SamDoesArt, soft pastel colors
Studio Ghibli, hand-painted, whimsical

# Dark moody realistic styles  
noir photography, high contrast shadows
gothic, dramatic lighting, desaturated
```

When generating, the LLM sees this structure and understands:
- There are two categories
- Each has a distinct aesthetic
- New items should fit these categories

## AI Panel (Right Side)

### Configuration

| Option | Values | Default |
|--------|--------|---------|
| Count | 10, 20, 30, 50, custom | 20 |
| Guidance | Free text input | empty |
| Creativity | Similar, Balanced, Creative | Balanced |

### Generation Flow

1. User configures options
2. Click "Generate N More"
3. Backend sends existing list + comments to LLM (using app's `LLM_MODE`/`LLM_MODEL`)
4. LLM returns new items
5. Preview shows generated items
6. User can:
   - **Regenerate** — Try again with same settings
   - **Add All** — Append to editor
   - **Cherry-pick** — Click individual items to add (future)

### Prompt Template

```
You are helping expand a list of values for an image generation variable called "{variable_name}".

Here is the current list with any organizational comments:
---
{file_contents}
---

Generate {count} new unique entries that:
1. Match the style and format of existing entries
2. Respect the category structure indicated by comments
3. Are creative but consistent with the theme
{guidance_instruction}

Return ONLY the new values, one per line. No numbering, no explanations.
```

## Backend API

### Endpoints

```
GET  /api/variables              — List all variable files
GET  /api/variables/{name}       — Get contents of a variable file
PUT  /api/variables/{name}       — Save/update a variable file
POST /api/variables/{name}       — Create new variable file
DELETE /api/variables/{name}     — Delete a variable file

POST /api/variables/generate     — AI-generate new items
```

### Generate Endpoint

```
POST /api/variables/generate
Content-Type: application/json

{
  "variable_name": "art_style",
  "current_content": "# Anime styles\nSamDoesArt...",
  "count": 20,
  "guidance": "focus on realistic photography styles",
  "creativity": "balanced"
}
```

Response:
```json
{
  "generated": [
    "editorial fashion, soft studio lighting",
    "street photography, candid moment",
    "portrait, shallow depth of field",
    ...
  ]
}
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+S` | Save current file |
| `Ctrl+G` | Generate with AI |
| `Ctrl+N` | New variable |
| `Escape` | Close editor / return to main app |
| `Ctrl+/` | Toggle comment on line |

## File Operations

| Action | Behavior |
|--------|----------|
| Save | Write to `variables/{name}.txt` |
| New | Create `variables/{name}.txt`, prompt for name |
| Delete | Confirm, then remove file |
| Import | Upload `.txt` file |
| Export | Download current file |

---

# Implementation Phases

Order is based on dependencies:
```
Metadata → Info Flyout → Search → LiteLLM → Var Editor
   │           │            │         │          │
   │           │            │         │          └── Capstone, uses everything
   │           │            │         └── Prep for var editor + improves main app
   │           │            └── Unlocked by metadata, high user value
   │           └── Quick visible win, pure frontend
   └── Foundation — everything else reads from this
```

## Phase 1: Metadata Foundation
- Modify SSE events to include `original_prompt`, `seed`, `width`, `height`
- Update `ImageData` interface (frontend)
- Save `.json` sidecar files alongside images
- Load metadata when gallery loads existing images
- Backward compat: images without sidecar show partial info

## Phase 2: Info Flyout
- Add InfoButton and InfoPanel components
- Wire up to existing `selectedImage` in App.svelte
- Display all available metadata (original prompt, final prompt, size, seed, date)
- Panel open/close with animations
- Copy prompt buttons (both original and final)

## Phase 3: Gallery Search
- Add search box to Gallery header
- Implement `/search` CLI command
- Create `/api/images/search` endpoint
- Search reads from `.json` sidecar files
- Real-time filtering in UI (debounced)

## Phase 4: LiteLLM Integration
- Add `litellm` dependency to pyproject.toml
- Rename `LLM_REPO` → `LLM_MODEL` (with backward compat)
- Add `LLM_MODE=litellm` option
- Abstract LLM provider in `llm_provider.py`
- Update setup wizard with cloud API option
- Update docs and env.example

## Phase 5: Variable Editor - Core
- Add Svelte Router (or path-based conditional rendering)
- Create `/var-editor` route
- Build three-panel layout (sidebar, editor, AI panel)
- Implement CRUD API for variable files
- Basic text editing with save
- Keyboard shortcuts (Ctrl+S, Esc)

## Phase 6: Variable Editor - AI Expansion
- Implement `/api/variables/generate` endpoint
- Uses same LLM config as main app (LLM_MODE/LLM_MODEL)
- Wire up AI panel with count/guidance/creativity options
- Preview generated items before adding
- Add All / Regenerate flow

## Phase 7: Polish & Extended Actions
- Info panel: Regenerate with seed, Open Folder, Delete
- Variable Editor: Import/Export files
- Toast notifications for feedback
- Error handling and edge cases
- Mobile/responsive considerations

---

# Open Questions

1. **Search: Fuzzy or exact?** — Start with substring, add fuzzy later?
2. **Variable icons** — Auto-assign based on name, or let user pick?
3. **Cherry-pick generated items** — Add individually, or all-or-nothing for v1?
4. **LiteLLM in setup wizard** — Show provider-specific fields dynamically?

---

# Success Metrics

| Feature | Success Criteria |
|---------|------------------|
| Info Flyout | Image gets 100% space by default, metadata 1 click away |
| Search | Find any image by prompt fragment in < 1 second |
| LiteLLM | Use GPT-4/Claude for prompt enhancement with single env var change |
| Variable Editor | Create and AI-expand a variable list without touching files |

---

# References

- Mockup (Info Flyout): `docs/specs/concepts/info-flyout/mockup-info-overlay.html`
- Mockup (Variable Editor): `docs/specs/concepts/info-flyout/mockup-variable-editor.html`
- Current lightbox: `src/z_explorer/gui/src/App.svelte`
- Current variables API: `src/z_explorer/server.py`
- LiteLLM docs: https://docs.litellm.ai/
- LiteLLM providers: https://docs.litellm.ai/docs/providers
