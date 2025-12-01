# Changelog

All notable changes to Z-Explorer will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.4.0] - 2025-12-01

### 🎉 Beginner-Friendly Setup & Flexible Model Loading

This release makes Z-Explorer accessible to everyone with a guided setup wizard and support for quantized models that run on consumer GPUs.

### Added

#### Setup Wizard
- **Three setup presets** for different needs:
  - **Quick Start**: Optimized quantized models (~12GB VRAM) - perfect for beginners
  - **Custom Setup**: Mix and match model sources for power users
  - **Full Quality**: Maximum quality for 24GB+ GPUs
- **Automatic model download** after configuration with progress tracking
- **Sanity check** verifies models load correctly before first use
- **Recovery options** if verification fails: continue anyway, redo setup, or exit

#### Flexible Model Loading
- **Image model modes**: `hf_download`, `hf_local`, `components`, `sdnq`
- **SDNQ quantized models** for lower VRAM usage (~6GB download, ~12GB VRAM)
- **ComfyUI component support** - use existing safetensor files directly
- **Automatic key conversion** from ComfyUI to diffusers format

#### Independent LLM Configuration
- **Generic LLM support** - renamed from `QWEN_*` to `LLM_*` environment variables
- **BNB 4-bit quantized models** work out of the box (e.g., `unsloth/Qwen3-4B-Instruct-2507-bnb-4bit`)
- **LLM modes**: `z_image`, `hf_download`, `hf_local`, `gguf`
- **Separate LLM from image model** - configure each independently

#### CLI Improvements
- `z-explorer --setup` - Run setup wizard anytime
- `z-explorer --show-config` - Quick configuration check

#### Documentation
- **Comprehensive configuration guide** at `docs/CONFIGURATION.md`
- Updated README with beginner-focused installation instructions

### Changed

- Default VRAM recommendation increased from 8GB to 12GB (for Quick Start preset)
- Environment variables renamed: `QWEN_MODE` → `LLM_MODE`, `QWEN_PATH` → `LLM_PATH`, etc.

### Removed

- Tauri desktop application (build complexity issues)

---

## [0.3.0] - 2024-11-30

### 🎉 Major Release: Desktop GUI Integration

This release unifies the CLI and GUI into a single cohesive application with three modes.

### Added

#### Desktop Application
- **Native desktop app** via Tauri with bundled `uv` binary
- **Zero-config installation**: Download, install, run - no Python setup required!
- **First-run auto-setup**: Dependencies downloaded automatically (~2GB, cached)
- **Cross-platform build scripts**: `tauri-build.ps1` (Windows) and `tauri-build.sh` (Linux/macOS)

#### Three Operating Modes
- **GUI Mode** (default): `z-explorer` - Modern web-based interface
- **CLI Mode**: `z-explorer --cli` - Terminal interface for power users
- **Server Mode**: `z-explorer --server` - Headless API server

#### New Features
- **Progress streaming** via Server-Sent Events (SSE)
- **Masonry gallery layout** for generated images
- **Prompt saved alongside images** as `.txt` files
- **Variable autocomplete** in the CLI-style input
- **`/changelog` command** to view this changelog in-app
- **Version display** in both GUI and CLI

#### Architecture Improvements
- **Single source of truth**: All generation logic in `core/generator.py`
- **FastAPI server** with REST endpoints and SSE streaming
- **Pydantic models** for type-safe request/response handling
- **66 tests** with 44% coverage (critical paths covered)

### Changed

- Default mode is now **GUI** (previously CLI-only)
- Server port standardized to **8345**
- Simplified Tauri backend (removed duplicate Python scripts)

### Removed

- Old `pyros-app/` directory (merged into `src/gui/`)
- Duplicate Python scripts from `src-tauri/scripts/`
- Subprocess-based Tauri architecture (now uses HTTP)

### Technical Details

#### API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/variables` | List prompt variables |
| GET | `/api/gpu` | GPU memory status |
| POST | `/api/unload` | Unload models |
| GET | `/api/images` | List generated images |
| GET | `/api/generate/stream` | Generate with SSE progress |

#### Build Outputs
- Linux: `.deb`, `.rpm`, `.AppImage`
- Windows: `.msi`, `.exe`
- macOS: `.dmg`, `.app`

---

## [0.2.1] - 2024-11-29

### Added
- Initial FastAPI server module
- Core types and generator extraction
- Basic test suite

### Changed
- Refactored CLI to use shared core module

---

## [0.2.0] - 2024-11-28

### Added
- Z-Image-Turbo integration for fast image generation
- Qwen3-4B for prompt enhancement
- Variable substitution system (`__variable__` syntax)
- Batch generation support
- Terminal image preview

---

## [0.1.0] - 2024-11-27

### Added
- Initial CLI implementation
- Basic image generation pipeline
- Prompt variable loading from markdown files

---

[0.4.0]: https://github.com/pyros-projects/z-Explorer/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/pyros-projects/z-Explorer/compare/v0.2.1...v0.3.0
[0.2.1]: https://github.com/pyros-projects/z-Explorer/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/pyros-projects/z-Explorer/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/pyros-projects/z-Explorer/releases/tag/v0.1.0
