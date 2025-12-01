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
# Note: PyTorch wheels bundle CUDA runtime. Host only needs NVIDIA drivers
# and nvidia-container-toolkit installed.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Install git and build tools (git for deps, gcc for triton/torch.compile)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . .

# Install dependencies (PyTorch includes CUDA runtime)
RUN uv sync --frozen

# Create directories
RUN mkdir -p /app/output /app/.cache/huggingface

EXPOSE 8345

ENV LOCAL_OUTPUT_DIR=/app/output
ENV HF_HOME=/app/.cache/huggingface

# --quick-setup: Non-interactive config with Quick Start defaults
# --host 0.0.0.0: Bind to all interfaces (required for Docker)
CMD ["uv", "run", "z-explorer", "--quick-setup", "--host", "0.0.0.0"]

