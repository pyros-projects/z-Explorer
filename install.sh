#!/bin/bash
# Z-Explorer Installer (Linux only)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.sh | bash
#
# Or download and run:
#   chmod +x install.sh && ./install.sh
#
# Note: macOS is NOT supported (bitsandbytes requires CUDA)

set -e

echo "🔥 Z-Explorer Installer"
echo "========================"
echo ""

# Check for Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "❌ macOS is not supported."
    echo "   Z-Explorer requires NVIDIA CUDA (bitsandbytes dependency)."
    echo "   Please use Linux or Windows with an NVIDIA GPU."
    exit 1
fi

# Check for NVIDIA GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  Warning: nvidia-smi not found. Z-Explorer requires an NVIDIA GPU."
    echo "   Install NVIDIA drivers first: https://docs.nvidia.com/cuda/"
    echo ""
fi

# Check for uv
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Add to PATH for this session
    export PATH="$HOME/.local/bin:$PATH"

    # Verify installation
    if ! command -v uv &> /dev/null; then
        echo "❌ Failed to install uv. Please install manually: https://docs.astral.sh/uv/"
        exit 1
    fi
    echo "✓ uv installed"
else
    echo "✓ uv already installed"
fi

# Check for Node.js (needed to build the GUI)
if ! command -v node &> /dev/null; then
    echo "📦 Installing Node.js (needed for GUI)..."

    # Try to install Node.js via package manager or NodeSource
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu - use NodeSource LTS
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash - 2>/dev/null || true
        sudo apt-get install -y nodejs 2>/dev/null || apt-get install -y nodejs 2>/dev/null || true
    elif command -v dnf &> /dev/null; then
        # Fedora/RHEL
        sudo dnf install -y nodejs npm 2>/dev/null || dnf install -y nodejs npm 2>/dev/null || true
    elif command -v pacman &> /dev/null; then
        # Arch Linux
        sudo pacman -S --noconfirm nodejs npm 2>/dev/null || pacman -S --noconfirm nodejs npm 2>/dev/null || true
    fi

    # Verify installation
    if command -v node &> /dev/null; then
        echo "✓ Node.js installed ($(node --version))"
    else
        echo "⚠️  Could not install Node.js automatically."
        echo "   Please install Node.js manually: https://nodejs.org/"
        echo "   The GUI will not be available without Node.js."
        echo ""
    fi
else
    echo "✓ Node.js already installed ($(node --version))"
fi

# Clone repository (installs in current directory by default)
INSTALL_DIR="${Z_EXPLORER_DIR:-$(pwd)/z-Explorer}"

if [ -d "$INSTALL_DIR" ]; then
    echo "📁 Directory $INSTALL_DIR already exists"
    echo "   Pulling latest changes..."
    cd "$INSTALL_DIR"
    git pull
else
    echo "📥 Cloning Z-Explorer to $INSTALL_DIR..."
    git clone https://github.com/pyros-projects/z-Explorer.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Install dependencies
echo "📦 Installing dependencies (this may take a few minutes)..."
uv sync

echo ""
echo "✅ Installation complete!"
echo ""
echo "To run Z-Explorer:"
echo "  cd $INSTALL_DIR"
echo "  uv run z-explorer"
echo ""
echo "Or add an alias to your shell config:"
echo "  alias z-explorer='cd $INSTALL_DIR && uv run z-explorer'"
echo ""

# Run quick setup and launch (downloads models automatically)
echo "🔧 Configuring with Quick Start defaults..."
uv run z-explorer --quick-setup --show-config

echo ""
echo "🚀 Launching Z-Explorer (models will download automatically)..."
echo ""
uv run z-explorer

