# z-Explorer Project Overview

**Generated:** 2025-12-02
**Project Type:** Multi-part Monolith
**Version:** 0.4.40

## Executive Summary

z-Explorer is a local AI image generation tool that combines Z-Image-Turbo (image generation) with Qwen3-4B (LLM for prompt enhancement). Everything runs locally with no cloud APIs required. The project consists of a Python backend with FastAPI server and CLI interface, plus a Svelte-based web GUI.

## Project Structure

**Repository Type:** Multi-part monolith (single Python package with embedded GUI)

### Part 1: Backend/CLI
- **Location:** `src/z_explorer/`
- **Type:** Backend API + CLI
- **Language:** Python 3.12
- **Primary Tech:** FastAPI, PyTorch, Transformers, Diffusers

### Part 2: GUI
- **Location:** `src/z_explorer/gui/`
- **Type:** Web Frontend
- **Language:** TypeScript
- **Primary Tech:** Svelte 4, Vite

## Technology Stack Summary

| Category | Backend | GUI |
|----------|---------|-----|
| **Language** | Python 3.12 | TypeScript 5.3 |
| **Framework** | FastAPI 0.109+ | Svelte 4.2 |
| **Build Tool** | uv | Vite 5.0 |
| **Testing** | pytest, pytest-cov | Vitest 2.1 |
| **AI/ML** | PyTorch, Transformers, Diffusers | N/A |
| **Server** | Uvicorn (ASGI) | Dev: Vite Dev Server |
| **Package Manager** | uv | npm |

## Architecture Classification

**Backend:** Service-oriented API backend with CLI interface
**GUI:** Component-based SPA (Single Page Application)
**Integration:** REST API + Server-Sent Events (SSE)

## Key Features

### Backend Features
- **Two-phase generation pipeline**: LLM (phase 1) → Diffusion model (phase 2) for GPU memory management
- **Multiple model loading modes**: HuggingFace download, SDNQ quantized, local paths, GGUF
- **CLI interface**: Expert/terminal mode for power users
- **FastAPI server**: RESTful API with SSE for real-time progress
- **Setup wizard**: Interactive first-run configuration
- **Model download service**: Progress tracking for large AI models

### GUI Features
- **Terminal-style CLI interface**: FakeCLI component with autocomplete
- **Multiple gallery layouts**: Grid, Masonry, Flex Row
- **Real-time generation progress**: SSE connection to backend
- **Settings management**: Runtime configuration override
- **Setup wizard UI**: First-run model download interface

## Development Approach

This is a **brownfield project** with active development. The codebase follows modern Python packaging practices (PEP 621) with uv as the package manager and includes comprehensive testing infrastructure.

## Links to Detailed Documentation

- [Architecture - Backend](./architecture-backend.md)
- [Architecture - GUI](./architecture-gui.md)
- [API Contracts](./api-contracts-backend.md)
- [Data Models](./data-models-backend.md)
- [UI Component Inventory](./ui-component-inventory-gui.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Integration Architecture](./integration-architecture.md)
- [Development Guide - Backend](./development-guide-backend.md)
- [Development Guide - GUI](./development-guide-gui.md)

## Quick Start

See the [Development Guide - Backend](./development-guide-backend.md) for installation and setup instructions.
