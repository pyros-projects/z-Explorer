# Z-Explorer Docker Image
#
# Build:
#   docker build -t z-explorer .
#
# Run:
#   docker run --gpus all -p 8345:8345 z-explorer
#
# With persistent output/cache directories:
#   docker run --gpus all -p 8345:8345 \
#     -v ./output:/app/output \
#     -v ./hf-cache:/app/.cache/huggingface \
#     z-explorer
#
# ghcr:
#   docker pull ghcr.io/pyros-projects/z-explorer
#   docker run --gpus all -p 8345:8345 ghcr.io/pyros-projects/z-explorer:latest
#
# Requirements:
#   - NVIDIA GPU with 12GB+ VRAM
#   - nvidia-container-toolkit installed on host
#   - Docker with GPU support

FROM nvidia/cuda:12.8.0-runtime-ubuntu22.04

# Prevent interactive prompts during apt install
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.12, Node.js 20, git, and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    curl \
    git \
    build-essential \
    && add-apt-repository -y ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Copy project files
COPY . .

# Build the GUI
WORKDIR /app/src/z_explorer/gui
RUN npm ci && npm run build

# Back to app root for Python setup
WORKDIR /app

# Install Python dependencies
RUN uv sync --frozen

# Create directories
RUN mkdir -p /app/output /app/.cache/huggingface

EXPOSE 8345

ENV LOCAL_OUTPUT_DIR=/app/output
ENV HF_HOME=/app/.cache/huggingface

# --quick-setup: Non-interactive config with Quick Start defaults
# --host 0.0.0.0: Bind to all interfaces (required for Docker)
CMD ["uv", "run", "z-explorer", "--quick-setup", "--host", "0.0.0.0"]
