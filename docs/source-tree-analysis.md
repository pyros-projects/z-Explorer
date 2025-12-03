# Source Tree Analysis

**Generated:** 2025-12-02
**Project:** z-Explorer (Multi-part Monolith)

## Project Root Structure

```
z-Explorer/
├── src/z_explorer/           # Main Python package (Backend)
│   ├── gui/                  # Svelte frontend (GUI)
│   ├── core/                 # Core generation logic
│   ├── services/             # Service modules
│   └── models/               # Data models
├── tests/                    # Test suite
├── docs/                     # Documentation (this file)
├── library/                  # Prompt variable libraries
├── output/                   # Generated images
├── pyproject.toml           # Python package configuration
└── README.md                # Project documentation
```

## Part 1: Backend/CLI (`src/z_explorer/`)

```
src/z_explorer/
├── __init__.py              # Package initialization
├── cli.py                   # CLI interface (entry point)
├── server.py                # FastAPI server (entry point)
├── image_generator.py       # Z-Image-Turbo pipeline
├── llm_provider.py          # Qwen3-4B LLM integration
├── model_config.py          # Model configuration management
├── setup_wizard.py          # Interactive setup
├── globals.py               # Global state
│
├── core/                    # Core generation logic
│   ├── __init__.py
│   ├── generator.py         # Two-phase generation pipeline
│   └── types.py             # Type definitions
│
├── services/                # Service modules
│   ├── download.py          # Model download with progress
│   └── preview.py           # Image preview utilities
│
├── models/                  # Data models
│   └── prompt_vars.py       # Prompt variable definitions
│
└── gui/                     # Svelte frontend (Part 2)
    ├── src/                 # Svelte source code
    ├── dist/                # Built GUI files
    ├── public/              # Static assets
    ├── package.json         # NPM dependencies
    └── vite.config.ts       # Vite build configuration
```

### Critical Backend Directories

| Directory | Purpose | Entry Points |
|-----------|---------|--------------|
| `core/` | Generation pipeline logic | `generator.py` |
| `services/` | Utility services | `download.py`, `preview.py` |
| `models/` | Data models and schemas | `prompt_vars.py` |

### Backend Entry Points

- **CLI:** `cli.py` → `main()` function
- **Server:** `server.py` → FastAPI app instance
- **Core Pipeline:** `core/generator.py` → `generate_images()`

## Part 2: GUI (`src/z_explorer/gui/`)

```
src/z_explorer/gui/
├── src/
│   ├── main.ts              # Application entry point
│   ├── App.svelte           # Root component
│   ├── app.css              # Global styles
│   │
│   └── lib/                 # Component library
│       ├── FakeCLI.svelte   # Terminal-style CLI interface
│       ├── Gallery.svelte   # Image gallery with layouts
│       ├── Settings.svelte  # Settings dialog
│       ├── Setup.svelte     # Setup wizard UI
│       │
│       ├── gallery/         # Gallery layout components
│       │   ├── GridSquare.svelte
│       │   ├── GridAuto.svelte
│       │   ├── FlexRow.svelte
│       │   ├── MasonryVertical.svelte
│       │   └── MasonryHorizontal.svelte
│       │
│       ├── stores/          # Svelte stores (state management)
│       │   └── settings.ts
│       │
│       └── services/        # Service modules
│           └── settingsService.ts
│
├── dist/                    # Production build output
│   ├── index.html
│   └── assets/             # Bundled JS/CSS
│
├── public/                  # Static assets
│   └── assets/
│       ├── icon.jpg
│       └── logo.jpg
│
├── package.json             # Dependencies
├── vite.config.ts           # Vite configuration
├── tsconfig.json            # TypeScript configuration
└── vitest.config.ts         # Test configuration
```

### Critical GUI Directories

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `src/lib/` | Component library | All `.svelte` components |
| `src/lib/gallery/` | Gallery layouts | Layout components |
| `src/lib/stores/` | State management | Svelte stores |
| `src/lib/services/` | Service layer | API clients, utilities |
| `dist/` | Production build | Served by FastAPI |

### GUI Entry Points

- **Main:** `src/main.ts` → Initializes Svelte app
- **Root Component:** `src/App.svelte` → Application shell
- **Build:** `vite build` → Outputs to `dist/`

## Integration Points

### Backend → GUI
- **GUI Serving:** `server.py` serves `gui/dist/` static files
- **API Gateway:** Backend provides `/api/*` endpoints for GUI

### GUI → Backend
- **REST API:** Fetch calls to `/api/*` endpoints
- **SSE Stream:** `/api/generate/stream` for real-time progress
- **Image Display:** `/output/{filename}` for generated images

## Test Structure

```
tests/
├── test_cli.py              # CLI tests
├── test_generator.py        # Core generator tests
├── test_llm_provider.py     # LLM provider tests
├── test_image_generator.py  # Image generator tests
├── test_model_config.py     # Config tests
│
└── test_server/             # API tests
    ├── test_endpoints.py    # Endpoint tests
    └── test_sse.py          # SSE stream tests
```

## Build Artifacts

- **Backend Build:** No build step (Python package)
- **GUI Build:** `gui/dist/` (Vite production build)
- **Distribution:** Bundled in Python package with `hatch`

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python package config, dependencies |
| `gui/package.json` | GUI dependencies |
| `gui/vite.config.ts` | Vite build configuration |
| `gui/tsconfig.json` | TypeScript compiler config |
| `.env` | Environment variables (model config) |
| `Dockerfile` | Container image definition |

## Development Files

| File | Purpose |
|------|---------|
| `README.md` | Project documentation |
| `CLAUDE.md` | Claude Code instructions |
| `CHANGELOG.md` | Version history |
| `install.sh` / `install.ps1` | Installation scripts |

See [Development Guide - Backend](./development-guide-backend.md) and [Development Guide - GUI](./development-guide-gui.md) for detailed development workflows.
