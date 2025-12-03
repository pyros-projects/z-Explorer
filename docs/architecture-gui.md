# Z-Explorer GUI Architecture

## Executive Summary

Z-Explorer's GUI is a modern Svelte 4 single-page application (SPA) that provides a desktop-class user experience for local AI image generation. The frontend communicates with the Python backend via REST API and Server-Sent Events (SSE) for real-time progress updates. The GUI features a terminal-style CLI input with autocomplete, a responsive masonry gallery, and persistent user settings.

**Key Features:** Terminal-style input, real-time progress, masonry gallery, settings persistence, responsive design

**Version:** 0.3.0
**Framework:** Svelte 4 + TypeScript
**Build Tool:** Vite 5

---

## Technology Stack

### Core Dependencies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Framework** | Svelte 4 | Reactive UI components |
| **Language** | TypeScript 5 | Type safety |
| **Build Tool** | Vite 5 | Fast dev server and bundling |
| **Desktop Wrapper** | Tauri 2 (optional) | Native desktop app |
| **Testing** | Vitest + Testing Library | Unit and integration tests |
| **Styling** | CSS Variables | Theming and dark mode |

### Development Dependencies

```json
{
  "@sveltejs/vite-plugin-svelte": "^3.0.0",
  "@tauri-apps/api": "^2.0.0",
  "@tauri-apps/cli": "^2.0.0",
  "@testing-library/svelte": "^5.2.7",
  "@vitest/coverage-v8": "^2.1.8",
  "typescript": "^5.3.0",
  "vite": "^5.0.0",
  "vitest": "^2.1.8"
}
```

---

## Architecture Pattern

**Component-Based Single-Page Application (SPA)**

```
┌─────────────────────────────────────────────────────────────┐
│                           Browser                             │
│                      http://localhost:8345                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │   index.html  │
                    │   (SPA shell) │
                    └───────┬───────┘
                            │
                            ▼
               ┌────────────────────────┐
               │      App.svelte        │
               │  (Root Component)      │
               └────────┬───────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
   ┌─────────┐   ┌──────────┐   ┌──────────┐
   │ Gallery │   │ FakeCLI  │   │ Settings │
   └────┬────┘   └────┬─────┘   └────┬─────┘
        │             │               │
        ▼             ▼               ▼
   [Layouts]    [Autocomplete]   [Forms]
   [Preview]    [Progress]       [Validation]
```

---

## Key Components

### 1. Root Component: `App.svelte`

**Purpose:** Application orchestrator and state manager

**Responsibilities:**
- Backend connection management (REST + SSE)
- Image generation coordination
- State synchronization between components
- Event routing and dispatch

**Key State:**

```typescript
let images: ImageData[] = [];              // Generated images
let isGenerating = false;                  // Generation in progress
let progress = 0;                          // Current progress (0-100)
let selectedImage: ImageData | null = null; // Preview selection
let isBackendConnected = false;            // Server connection status
let needsSetup = false;                    // First-run setup required
```

**API Base Resolution:**

```typescript
function getApiBase(): string {
  const { protocol, hostname, port } = window.location;

  // Vite dev server (port 5173) - use proxy
  if (port === '5173') return '';

  // Production - use same origin as UI
  return `${protocol}//${hostname}${port ? ':' + port : ''}`;
}
```

**SSE Connection Management:**

```typescript
eventSource = new EventSource(`${API_BASE}/api/generate/stream?${params}`);

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  // Update progress
  if (data.progress !== undefined) {
    progress = data.progress;
  }

  // Image saved - add to gallery and show preview
  if (data.stage === 'image_saved' && data.path) {
    const imageData = { url: toDisplayUrl(data.path), prompt: data.data?.prompt };
    images = [imageData, ...images];
    selectedImage = imageData;
  }

  // Generation complete
  if (data.stage === 'complete') {
    isGenerating = false;
    eventSource?.close();
  }
};
```

**Component Integration:**

- **Gallery:** Displays generated images with multiple layout modes
- **FakeCLI:** Terminal-style input with autocomplete and progress
- **Settings:** Configuration dialog for models and UI preferences
- **Setup:** First-run wizard for model download

---

### 2. Terminal Input: `FakeCLI.svelte`

**Purpose:** Terminal-style command-line interface with autocomplete

**Features:**
- Autocomplete for commands (`/help`, `/vars`, etc.)
- Autocomplete for prompt variables (`__animal__`, `__style__`)
- Real-time progress display with stage tracking
- Command history with collapsible sections
- Tips and tutorial sections

**Key State:**

```typescript
let input = '';                            // Current input
let suggestions: string[] = [];            // Autocomplete suggestions
let history: HistoryItem[] = [];           // Command/output history
let currentProgress = 0;                   // Current generation progress
let currentStage = '';                     // Current stage name
let progressBarIndex = -1;                 // Progress bar position in history
```

**Autocomplete Logic:**

```typescript
function updateSuggestions() {
  const textBeforeCursor = input.slice(0, cursorPosition);

  // Command suggestions
  if (textBeforeCursor.includes('/')) {
    const lastSlash = textBeforeCursor.lastIndexOf('/');
    const partial = textBeforeCursor.slice(lastSlash);
    suggestions = commands.filter(cmd => cmd.startsWith(partial));
  }

  // Variable suggestions
  if (textBeforeCursor.includes('__')) {
    const lastVar = textBeforeCursor.lastIndexOf('__');
    const afterVar = textBeforeCursor.slice(lastVar);
    if ((afterVar.match(/__/g) || []).length === 1) {
      suggestions = promptVars.filter(v => v.startsWith(afterVar));
    }
  }
}
```

**Progress Display:**

```typescript
export function updateProgress(percent: number, stage: string, message: string) {
  currentProgress = percent;
  currentStage = stage;

  // Update progress bar in place
  if (progressBarIndex >= 0) {
    history[progressBarIndex] = { type: 'progress-bar', percent, stage };
  }

  // Add message below progress bar (skip silent stages)
  if (message && !silentStages.has(stage)) {
    const icon = stageIcons[stage] || '⚡';
    history = [...history, { type: 'progress-msg', text: `${icon} ${message}` }];
  }
}
```

**Command System:**

Commands available:
- `/help` - Show help
- `/vars` - List prompt variables
- `/enhance <prompt>` - Enhance without generating
- `/seed <number>` - Set seed
- `/size <WxH>` - Set output size
- `/gpu` - Show GPU memory
- `/unload` - Free GPU memory
- `/settings` - Open settings
- `/version` - Show version
- `/changelog` - Show changelog
- `/quit` - Exit

**Batch Parameter Parsing:**

```typescript
function parseParams(input: string): { prompt: string; params: any } {
  // Syntax: "prompt : x10,h832,w1216"
  // x<N> = count, h<N> = height, w<N> = width

  const parts = input.split(':');
  const paramPart = parts[parts.length - 1].trim();

  if (!/[xhw]\d/.test(paramPart)) {
    return { prompt: input, params: defaultParams };
  }

  // Extract count, height, width
  const params = { count: 1, height: 1024, width: 1024 };
  for (const param of paramPart.split(',')) {
    if (param.startsWith('x')) params.count = parseInt(param.slice(1));
    if (param.startsWith('h')) params.height = parseInt(param.slice(1));
    if (param.startsWith('w')) params.width = parseInt(param.slice(1));
  }

  return { prompt: parts.slice(0, -1).join(':').trim(), params };
}
```

---

### 3. Gallery: `Gallery.svelte`

**Purpose:** Display generated images with multiple layout modes

**Layout Modes:**

| Mode | Component | Description |
|------|-----------|-------------|
| `grid-square` | `GridSquare.svelte` | Equal-sized square grid (Instagram-style) |
| `grid-auto` | `GridAuto.svelte` | Auto-fitting grid preserving aspect ratios |
| `masonry-vertical` | `MasonryVertical.svelte` | Pinterest-style vertical masonry |
| `masonry-horizontal` | `MasonryHorizontal.svelte` | Horizontal scrolling masonry |
| `flex-row` | `FlexRow.svelte` | Single-row horizontal flex layout |

**Key Features:**
- Thumbnail size presets (small, medium, large, custom)
- Layout mode switching
- Progress indicator during generation
- Image preview on click
- Settings button

**Component Structure:**

```svelte
<div class="gallery">
  <div class="toolbar">
    <select bind:value={$settings.gallery.layout}>
      <option value="masonry-vertical">Masonry (Vertical)</option>
      <option value="grid-auto">Grid (Auto)</option>
      <!-- ... -->
    </select>
    <button on:click={onOpenSettings}>⚙️ Settings</button>
  </div>

  {#if isGenerating}
    <div class="progress-overlay">
      <div class="progress-bar" style="width: {progress}%"></div>
    </div>
  {/if}

  <svelte:component
    this={currentLayout}
    {images}
    on:select={handleSelect}
  />
</div>
```

**Image Preview:**

When user clicks an image, App.svelte displays a full-screen overlay:

```svelte
{#if selectedImage}
  <div class="preview-overlay" on:click={closePreview}>
    <img src={selectedImage.url} alt="Preview" />
    {#if selectedImage.prompt}
      <div class="preview-prompt">
        <span class="prompt-label">📜 Prompt</span>
        <p>{selectedImage.prompt}</p>
      </div>
    {/if}
    <button class="close-btn">×</button>
  </div>
{/if}
```

---

### 4. Settings Dialog: `Settings.svelte`

**Purpose:** Runtime configuration for models, gallery, CLI, and generation

**Setting Categories:**

1. **Models**
   - Image model mode (hf_download, sdnq, hf_local, components)
   - Image model repository/path
   - LLM mode (hf_download, z_image, hf_local, gguf)
   - LLM repository/path

2. **Gallery**
   - Layout mode (masonry-vertical, grid-auto, etc.)
   - Thumbnail size (small, medium, large, custom)
   - Custom thumbnail height

3. **CLI**
   - Font size (small, medium, large)
   - Show history on start
   - Show tips on start
   - Show tutorial on start
   - CLI height

4. **Generation**
   - Default count
   - Default width
   - Default height
   - Default seed

**Settings Persistence:**

```typescript
// src/lib/services/settingsService.ts
export function saveSettings(settings: ZExplorerSettings): void {
  localStorage.setItem('z-explorer-settings', JSON.stringify(settings));
}

export function loadSettings(): ZExplorerSettings {
  const stored = localStorage.getItem('z-explorer-settings');
  return stored ? JSON.parse(stored) : DEFAULT_SETTINGS;
}
```

**Model Configuration Flow:**

1. User changes model settings in dialog
2. Dialog checks if model is cached (POST `/api/settings/models/check-cache`)
3. If not cached, prompts to download (GET `/api/settings/models/download` with SSE)
4. On save, sends config to backend (POST `/api/settings/models`)
5. Backend stores runtime override (doesn't modify `.env`)
6. Dialog triggers reload (POST `/api/models/reload`)
7. Models unload, new config becomes active

---

### 5. Setup Wizard: `Setup.svelte`

**Purpose:** First-run model download wizard

**Flow:**

1. **Check Status:** GET `/api/setup/status`
   - Returns: `is_configured`, `models_needed`, `models_downloaded`

2. **Show Model List:**
   - Display required models (e.g., Z-Image-Turbo, Qwen3-4B)
   - Show download sizes
   - Estimate time based on connection speed

3. **Download Models:** GET `/api/setup/download` (SSE)
   - Stream progress events:
     ```json
     {
       "model_name": "Z-Image-Turbo",
       "status": "downloading",
       "current_file": "model.safetensors",
       "files_done": 3,
       "files_total": 10,
       "bytes_done": 1500000000,
       "bytes_total": 24000000000,
       "progress_percent": 6.25,
       "speed_mbps": 50.5,
       "eta_seconds": 280
     }
     ```

4. **Completion:**
   - Emit `complete` event to App.svelte
   - App reloads images and starts main UI

**Progress Display:**

```svelte
{#each modelsNeeded as model}
  <div class="model-download">
    <h3>{model.name}</h3>
    <div class="progress-bar">
      <div class="fill" style="width: {model.progress}%"></div>
    </div>
    <div class="details">
      {model.files_done}/{model.files_total} files •
      {formatBytes(model.bytes_done)}/{formatBytes(model.bytes_total)} •
      {model.speed_mbps.toFixed(1)} MB/s •
      ETA: {formatTime(model.eta_seconds)}
    </div>
  </div>
{/each}
```

---

## State Management

### Svelte Stores

Z-Explorer uses Svelte's built-in reactivity with a writable store for settings:

```typescript
// src/lib/stores/settings.ts
import { writable } from 'svelte/store';

let _settings: Writable<ZExplorerSettings>;

export function initializeSettings(): void {
  const initial = loadSettings();
  _settings = writable(initial);
}

export const settings: Readable<ZExplorerSettings> = {
  subscribe: (run, invalidate) => _settings.subscribe(run, invalidate),
};
```

**Update Functions:**

```typescript
export function updateGallery(changes: Partial<GallerySettings>): void {
  _settings.update((current) => {
    const updated = { ...current, gallery: { ...current.gallery, ...changes } };
    saveSettings(updated);
    return updated;
  });
}

export function updateCLI(changes: Partial<CLISettings>): void {
  // Similar pattern
}
```

**Reactive Updates:**

Components can subscribe to settings:

```svelte
<script>
  import { settings } from './stores/settings';

  $: fontSize = $settings.cli.fontSize; // Reactive
  $: layout = $settings.gallery.layout;
</script>

<div style="font-size: {fontSize}">
  <!-- Content -->
</div>
```

### Component Communication

**Parent → Child:** Props

```svelte
<FakeCLI
  {isGenerating}
  isTauriAvailable={isTauriAvailable || isBackendConnected}
  getGpuInfo={handleGpuInfo}
  unloadModels={handleUnload}
  listVariables={handleListVariables}
/>
```

**Child → Parent:** Events

```svelte
<script>
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  function submit() {
    dispatch('generate', { prompt, params, seed });
  }
</script>

<button on:click={submit}>Generate</button>
```

**Parent receives:**

```svelte
<FakeCLI on:generate={handleGenerate} />

<script>
  function handleGenerate(event) {
    const { prompt, params, seed } = event.detail;
    // ...
  }
</script>
```

---

## Build Process

### Vite Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],

  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },

  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8345',
        changeOrigin: true,
      },
    },
  },
});
```

**Proxy Configuration:**
- Development: Vite proxy forwards `/api/*` to backend
- Production: GUI served by FastAPI at `/`, APIs at `/api/*`

### Build Commands

```bash
npm install          # Install dependencies
npm run dev          # Start dev server (port 5173)
npm run build        # Build for production (dist/)
npm run preview      # Preview production build
npm run check        # TypeScript/Svelte type checking
npm run test         # Run Vitest tests
npm run test:watch   # Watch mode
```

### Production Bundle

Output structure:
```
dist/
├── index.html           # SPA shell
├── assets/
│   ├── index-abc123.js  # Main bundle (hashed)
│   ├── index-def456.css # Styles (hashed)
│   └── ...              # Other chunks
└── ...
```

**Bundle served by FastAPI:**

```python
# server.py
@app.get("/", include_in_schema=False)
async def serve_gui():
    gui_dist = _get_gui_dist_dir()
    if gui_dist:
        return FileResponse(gui_dist / "index.html")
    return JSONResponse({"error": "GUI not found"}, status_code=404)

app.mount("/assets", StaticFiles(directory=str(gui_dist / "assets")), name="assets")
```

---

## Integration with Backend

### REST API Calls

**List Images:**

```typescript
async function loadImages() {
  const res = await fetch(`${API_BASE}/api/images`);
  if (res.ok) {
    const data = await res.json();
    images = data.images.map(img => ({
      url: `${API_BASE}${img.url}`,
      prompt: img.prompt,
    }));
  }
}
```

**Get GPU Info:**

```typescript
async function handleGpuInfo(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/gpu`);
  return res.ok ? await res.json() : null;
}
```

**Unload Models:**

```typescript
async function handleUnload(): Promise<any> {
  const res = await fetch(`${API_BASE}/api/unload`, { method: 'POST' });
  return res.ok ? await res.json() : null;
}
```

### SSE Progress Streaming

**Connection:**

```typescript
const queryParams = new URLSearchParams({
  prompt: 'a cat',
  count: '1',
  width: '1024',
  height: '1024',
});

eventSource = new EventSource(`${API_BASE}/api/generate/stream?${queryParams}`);
```

**Message Handling:**

```typescript
eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.stage) {
    case 'starting':
      progress = data.progress || 0;
      break;

    case 'diffusion_step':
      progress = data.progress || 0;
      cliComponent.updateProgress(data.progress, data.stage, data.message);
      break;

    case 'image_saved':
      const imageData = { url: toDisplayUrl(data.path), prompt: data.data?.prompt };
      images = [imageData, ...images];
      selectedImage = imageData;
      break;

    case 'complete':
      isGenerating = false;
      progress = 0;
      eventSource?.close();
      cliComponent.completeGeneration(true);
      break;

    case 'error':
      isGenerating = false;
      cliComponent.completeGeneration(false);
      cliComponent.addResult(data.message, true);
      eventSource?.close();
      break;
  }
};
```

**Error Handling:**

```typescript
eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  isGenerating = false;
  cliComponent.addResult('❌ Connection to server lost', true);
  eventSource?.close();
};
```

---

## Testing Strategy

### Test Structure

```
src/
└── z_explorer/
    └── gui/
        └── src/
            ├── __tests__/
            │   ├── setup.ts                    # Test setup/globals
            │   └── App.integration.test.ts     # Integration tests
            └── lib/
                ├── __tests__/
                │   └── Settings.test.ts        # Component tests
                ├── services/
                │   └── __tests__/
                │       └── settingsService.test.ts
                └── gallery/
                    └── __tests__/
                        └── layouts.test.ts
```

### Testing Tools

- **Vitest:** Fast test runner (Vite-native)
- **Testing Library:** DOM testing utilities
- **jsdom:** Browser environment simulation

### Test Examples

**Component Test:**

```typescript
// Settings.test.ts
import { render, fireEvent } from '@testing-library/svelte';
import Settings from '../Settings.svelte';

test('settings dialog opens and closes', async () => {
  const { getByText, queryByText } = render(Settings, { props: { open: false } });

  // Initially hidden
  expect(queryByText('Model Settings')).toBeNull();

  // Open dialog
  await render(Settings, { props: { open: true } });
  expect(getByText('Model Settings')).toBeTruthy();
});
```

**Service Test:**

```typescript
// settingsService.test.ts
import { loadSettings, saveSettings, DEFAULT_SETTINGS } from '../settingsService';

test('loads default settings when localStorage is empty', () => {
  localStorage.clear();
  const settings = loadSettings();
  expect(settings).toEqual(DEFAULT_SETTINGS);
});

test('persists settings to localStorage', () => {
  const customSettings = { ...DEFAULT_SETTINGS, gallery: { layout: 'grid-auto' } };
  saveSettings(customSettings);

  const loaded = loadSettings();
  expect(loaded.gallery.layout).toBe('grid-auto');
});
```

**Integration Test:**

```typescript
// App.integration.test.ts
import { render, waitFor } from '@testing-library/svelte';
import App from '../App.svelte';

test('fetches images on mount', async () => {
  // Mock fetch
  global.fetch = vi.fn(() =>
    Promise.resolve({
      ok: true,
      json: () => Promise.resolve({ images: [{ url: '/output/test.png' }] }),
    })
  );

  const { getByAltText } = render(App);

  await waitFor(() => {
    expect(getByAltText('Generated image')).toBeTruthy();
  });
});
```

### Coverage Target

Target: 70% (GUI components, services, stores)

Focus areas:
- Settings persistence
- SSE connection handling
- Layout component rendering
- Command parsing

---

## Styling and Theming

### CSS Variables

```css
:root {
  /* Colors */
  --bg-primary: #0a0a0f;
  --bg-secondary: #121218;
  --bg-tertiary: #1a1a24;
  --bg-card: #1f1f2e;

  --text-primary: #f8fafc;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;

  --accent-primary: #8b5cf6;    /* Purple */
  --accent-secondary: #22d3ee;  /* Cyan */
  --accent-purple: #8b5cf6;
  --accent-cyan: #22d3ee;

  --border-color: rgba(255, 255, 255, 0.1);
  --border-radius: 8px;

  /* Gradients */
  --gradient-brand: linear-gradient(135deg, #8b5cf6, #22d3ee);
  --gradient-glow: radial-gradient(circle, rgba(139, 92, 246, 0.15), transparent);

  /* Fonts */
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
  --font-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
```

### Component-Scoped Styles

Svelte components use scoped styles by default:

```svelte
<script>
  let count = 0;
</script>

<button on:click={() => count++}>
  Clicked {count} times
</button>

<style>
  button {
    /* Only applies to this component's button */
    background: var(--accent-primary);
    color: var(--text-primary);
    border: none;
    border-radius: var(--border-radius);
    padding: 8px 16px;
    cursor: pointer;
    transition: all 0.2s;
  }

  button:hover {
    background: var(--accent-secondary);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
  }
</style>
```

### Global Styles

```css
/* app.css */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: var(--font-sans);
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--accent-primary);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--accent-secondary);
}
```

### Responsive Design

```css
/* Mobile-first approach */
.gallery {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

@media (min-width: 768px) {
  .gallery {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  .gallery {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (min-width: 1536px) {
  .gallery {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

---

## Performance Considerations

### Bundle Size

- **Main bundle:** ~150KB (gzipped)
- **Svelte runtime:** ~15KB (gzipped)
- **CSS:** ~20KB (gzipped)

**Optimization Strategies:**
- Tree-shaking (Vite)
- Code splitting (dynamic imports)
- CSS minification
- Asset hashing for cache busting

### Reactivity

**Avoid unnecessary updates:**

```svelte
<script>
  import { onMount } from 'svelte';

  let images = [];

  // Only fetch once on mount
  onMount(async () => {
    images = await loadImages();
  });

  // Reactive - updates when images changes
  $: imageCount = images.length;
</script>

<p>Total images: {imageCount}</p>
```

**Use derived stores for computed values:**

```typescript
export const thumbnailHeightPx: Readable<number> = derived(
  settings,
  ($settings) => getThumbnailHeightPx(
    $settings.gallery.thumbnailSize,
    $settings.gallery.thumbnailHeight
  )
);
```

### Image Loading

**Lazy loading:**

```svelte
<img
  src={image.url}
  alt="Generated image"
  loading="lazy"
/>
```

**Progressive enhancement:**

```svelte
{#if imageLoaded}
  <img src={image.url} alt="High-res" />
{:else}
  <div class="skeleton-loader"></div>
{/if}
```

---

## Accessibility

### Keyboard Navigation

- Tab through interactive elements
- Enter to submit CLI input
- Arrow keys for autocomplete navigation
- Escape to close dialogs

### ARIA Labels

```svelte
<button
  aria-label="Open settings"
  aria-haspopup="dialog"
  on:click={openSettings}
>
  ⚙️
</button>

<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="settings-title"
>
  <h2 id="settings-title">Settings</h2>
  <!-- ... -->
</div>
```

### Focus Management

```svelte
<script>
  import { onMount } from 'svelte';

  let inputEl: HTMLInputElement;

  onMount(() => {
    inputEl?.focus();
  });
</script>

<input bind:this={inputEl} />
```

---

## Future Enhancements

### Planned Features

1. **Drag-and-drop image upload** (for image-to-image)
2. **Keyboard shortcuts** (Ctrl+Enter to generate, etc.)
3. **Image editing tools** (crop, resize, filters)
4. **Batch operations** (delete, download zip)
5. **Search and filter** (by prompt, date, size)

### Technical Improvements

1. **Virtual scrolling** (for large image galleries)
2. **Service worker** (offline support, PWA)
3. **Image optimization** (WebP conversion, thumbnails)
4. **Internationalization** (i18n support)

---

## Brownfield Development Notes

### Critical Constraints

1. **Svelte 4 (not 5):** Use Svelte 4 APIs (Svelte 5 has breaking changes)
2. **TypeScript strict mode:** All new code must be type-safe
3. **Vite as bundler:** Do not switch to webpack/rollup
4. **Component-based architecture:** Follow existing patterns

### Extension Points

1. **New gallery layouts:** Add to `src/lib/gallery/`, implement layout interface
2. **New settings categories:** Add to `settingsService.ts`, update `Settings.svelte`
3. **New CLI commands:** Add to `FakeCLI.svelte:handleCommand`
4. **New API integrations:** Add to `App.svelte` handler functions

### Code Organization Principles

- **One component per file:** `ComponentName.svelte`
- **Services in separate files:** `src/lib/services/`
- **Stores for shared state:** `src/lib/stores/`
- **Tests colocated:** `__tests__/` directory next to source

---

## References

- **Project Repository:** https://github.com/pyros-projects/z-Explorer
- **Svelte Documentation:** https://svelte.dev/docs
- **Vite Documentation:** https://vitejs.dev/
- **Tauri Documentation:** https://tauri.app/
- **Testing Library:** https://testing-library.com/docs/svelte-testing-library/intro

---

**Document Version:** 1.0
**Last Updated:** 2025-12-02
**For AI Agents:** This document provides comprehensive context for brownfield PRD work on z-Explorer GUI components.
