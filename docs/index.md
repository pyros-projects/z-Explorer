# z-Explorer Documentation Index

**Generated:** 2025-12-02
**Version:** 0.4.40
**Project Type:** Multi-part Monolith

---

## 🎯 Quick Start

**For AI Agents working on z-Explorer:**
1. Start here: [Project Overview](./project-overview.md)
2. Understand the parts: [Architecture - Backend](./architecture-backend.md) + [Architecture - GUI](./architecture-gui.md)
3. See how they connect: [Integration Architecture](./integration-architecture.md)
4. Find what you need below ⬇️

---

## 📊 Project Overview

- **Type:** Multi-part monolith (single Python package with embedded Svelte GUI)
- **Primary Language:** Python 3.12 (Backend) + TypeScript (GUI)
- **Architecture:** Service-oriented API + Component-based SPA
- **Version:** 0.4.40

### Quick Reference

#### Part 1: Backend/CLI
- **Type:** Backend API + CLI
- **Tech Stack:** Python 3.12, FastAPI, PyTorch, Transformers, Diffusers
- **Root:** `src/z_explorer/`
- **Entry Points:** `cli.py`, `server.py`, `core/generator.py`

#### Part 2: GUI (Svelte Frontend)
- **Type:** Web SPA
- **Tech Stack:** Svelte 4, TypeScript 5.3, Vite 5
- **Root:** `src/z_explorer/gui/`
- **Entry Point:** `src/main.ts` → `App.svelte`

---

## 📚 Generated Documentation

### Architecture Documentation

- **[Project Overview](./project-overview.md)** - High-level project summary
- **[Architecture - Backend](./architecture-backend.md)** - Backend/CLI architecture
- **[Architecture - GUI](./architecture-gui.md)** - Svelte GUI architecture
- **[Integration Architecture](./integration-architecture.md)** - How parts communicate
- **[Source Tree Analysis](./source-tree-analysis.md)** - Annotated directory structure

### API & Contracts

- **[API Contracts - Backend](./api-contracts-backend.md)** - REST API + SSE endpoints
- [Data Models - Backend](./data-models-backend.md) _(To be generated)_
- [UI Component Inventory - GUI](./ui-component-inventory-gui.md) _(To be generated)_

### Development Guides

- [Development Guide - Backend](./development-guide-backend.md) _(To be generated)_
- [Development Guide - GUI](./development-guide-gui.md) _(To be generated)_
- [Deployment Guide](./deployment-guide.md) _(To be generated)_

---

## 📖 Existing Documentation

### Project Documentation
- **[README.md](../README.md)** - Main project README with quickstart
- **[CLAUDE.md](../CLAUDE.md)** - Claude Code development instructions
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history and release notes

### Configuration & Migration
- **[CONFIGURATION.md](./CONFIGURATION.md)** - Model configuration guide
- **[Mistral Migration Guide](./mistral/MIGRATION_GUIDE.md)** - Migrating to Ministral 3B

### Specifications
- **[UI Settings Improvements](./specs/001-ui-settings-improvements/)** - UI settings feature spec
  - [Product Requirements](./specs/001-ui-settings-improvements/product-requirements.md)
  - [Implementation Plan](./specs/001-ui-settings-improvements/implementation-plan.md)
  - [Solution Design](./specs/001-ui-settings-improvements/solution-design.md)

---

## 🎨 Key Features

### Backend Features
- **Two-phase generation pipeline**: LLM enhancement (Phase 1) → Image generation (Phase 2)
- **Multiple model modes**: SDNQ quantized, HuggingFace download, local paths, GGUF
- **CLI interface**: Expert terminal mode for power users
- **FastAPI server**: REST API with SSE for real-time progress streaming
- **Setup wizard**: Interactive first-run configuration

### GUI Features
- **Terminal-style CLI**: FakeCLI component with autocomplete
- **Image gallery**: 5 layout modes (Grid Square, Grid Auto, Flex Row, Masonry V/H)
- **Real-time progress**: SSE connection for live generation updates
- **Settings dialog**: Runtime model configuration override
- **Setup wizard UI**: First-run model download with progress

---

## 🔗 Integration Patterns

### GUI → Backend
- **REST API**: Fetch calls to `/api/*` endpoints
- **SSE Stream**: `/api/generate/stream` for real-time progress
- **Image Display**: `/output/{filename}` for generated images

### Backend → GUI
- **Static Serving**: Serves `gui/dist/` at root path
- **API Gateway**: Provides `/api/*` endpoints for GUI

See [Integration Architecture](./integration-architecture.md) for detailed integration patterns.

---

## 🛠️ Development

### Getting Started (Backend)

```bash
# Install dependencies
uv sync

# Run the application (web UI mode)
uv run z-explorer

# Run in CLI mode
uv run z-explorer --cli

# Run tests
uv run pytest
```

### Getting Started (GUI)

```bash
# From src/z_explorer/gui/
npm install
npm run dev          # Start Vite dev server (port 5173)
npm run build        # Build for production
npm run test         # Run Vitest tests
```

### Testing

```bash
# Backend tests
uv run pytest

# GUI tests
cd src/z_explorer/gui && npm run test

# Coverage
uv run pytest --cov
npm run test:coverage
```

See generated development guides (when available) for detailed workflows.

---

## 📂 Critical Directories

### Backend
- `src/z_explorer/core/` - Core generation logic
- `src/z_explorer/services/` - Utility services (download, preview)
- `src/z_explorer/models/` - Data models and schemas
- `tests/` - Test suite

### GUI
- `src/z_explorer/gui/src/lib/` - Component library
- `src/z_explorer/gui/src/lib/gallery/` - Gallery layout components
- `src/z_explorer/gui/src/lib/stores/` - Svelte stores (state management)
- `src/z_explorer/gui/dist/` - Production build output

---

## 🚀 For Brownfield PRD Work

When creating PRDs for z-Explorer features:

1. **Start with this index** - Get oriented on project structure
2. **Review relevant architecture**:
   - **Backend-only features**: [Architecture - Backend](./architecture-backend.md)
   - **GUI-only features**: [Architecture - GUI](./architecture-gui.md)
   - **Full-stack features**: Both architectures + [Integration Architecture](./integration-architecture.md)
3. **Check API contracts**: [API Contracts](./api-contracts-backend.md) for endpoint design
4. **Review source tree**: [Source Tree Analysis](./source-tree-analysis.md) for file locations

---

## 📝 Documentation Metadata

**Generated by:** BMad Method - document-project workflow
**Scan Level:** Exhaustive
**Mode:** Initial scan
**Parts Documented:** 2 (Backend, GUI)

---

**Need more detail?** All documentation files listed above provide comprehensive coverage for AI-assisted development.
