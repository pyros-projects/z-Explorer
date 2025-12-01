# Z-Explorer Installer for Windows
#
# Usage (run in PowerShell):
#   irm https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.ps1 | iex
#
# Or download and run:
#   .\install.ps1

$ErrorActionPreference = "Stop"

Write-Host "🔥 Z-Explorer Installer" -ForegroundColor Magenta
Write-Host "========================" -ForegroundColor Magenta
Write-Host ""

# Check for NVIDIA GPU
try {
    $null = Get-Command nvidia-smi -ErrorAction Stop
    Write-Host "✓ NVIDIA GPU detected" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Warning: nvidia-smi not found. Z-Explorer requires an NVIDIA GPU." -ForegroundColor Yellow
    Write-Host "   Install NVIDIA drivers first: https://docs.nvidia.com/cuda/" -ForegroundColor Yellow
    Write-Host ""
}

# Check for git
try {
    $null = Get-Command git -ErrorAction Stop
    Write-Host "✓ Git installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git not found. Please install Git first: https://git-scm.com/download/win" -ForegroundColor Red
    exit 1
}

# Check for uv
$uvInstalled = $false
try {
    $null = Get-Command uv -ErrorAction Stop
    $uvInstalled = $true
    Write-Host "✓ uv already installed" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing uv (fast Python package manager)..." -ForegroundColor Cyan
    
    try {
        Invoke-RestMethod https://astral.sh/uv/install.ps1 | Invoke-Expression
        
        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")
        
        # Verify installation
        $null = Get-Command uv -ErrorAction Stop
        $uvInstalled = $true
        Write-Host "✓ uv installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install uv. Please install manually: https://docs.astral.sh/uv/" -ForegroundColor Red
        exit 1
    }
}

# Determine install directory
$InstallDir = if ($env:Z_EXPLORER_DIR) { $env:Z_EXPLORER_DIR } else { "$env:USERPROFILE\z-Explorer" }

# Clone or update repository
if (Test-Path $InstallDir) {
    Write-Host "📁 Directory $InstallDir already exists" -ForegroundColor Cyan
    Write-Host "   Pulling latest changes..." -ForegroundColor Cyan
    Push-Location $InstallDir
    git pull
} else {
    Write-Host "📥 Cloning Z-Explorer to $InstallDir..." -ForegroundColor Cyan
    git clone https://github.com/pyros-projects/z-Explorer.git $InstallDir
    Push-Location $InstallDir
}

# Install dependencies
Write-Host "📦 Installing dependencies (this may take a few minutes)..." -ForegroundColor Cyan
uv sync

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run Z-Explorer:" -ForegroundColor Cyan
Write-Host "  cd $InstallDir" -ForegroundColor White
Write-Host "  uv run z-explorer" -ForegroundColor White
Write-Host ""

# Run quick setup (configures with sensible defaults)
Write-Host "🔧 Configuring with Quick Start defaults..." -ForegroundColor Cyan
uv run z-explorer --quick-setup --show-config

Write-Host ""
Write-Host "✅ Configuration complete!" -ForegroundColor Green
Write-Host "   First run will download ~10GB of models (one-time)." -ForegroundColor Cyan
Write-Host ""

# Ask if user wants to run now
$response = Read-Host "🚀 Run Z-Explorer now? [Y/n]"
if ($response -eq "" -or $response -match "^[Yy]") {
    uv run z-explorer
}

Pop-Location

