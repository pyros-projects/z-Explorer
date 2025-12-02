# Z-Explorer Installer for Windows
#
# Usage (run in PowerShell):
#   irm https://raw.githubusercontent.com/pyros-projects/z-Explorer/main/install.ps1 | iex
#
# With custom host (for servers/Docker):
#   $env:Z_EXPLORER_HOST = "0.0.0.0"; irm ... | iex
#
# Or download and run:
#   .\install.ps1
#   .\install.ps1 -Host 0.0.0.0

param(
    [string]$BindHost = $null
)

$ErrorActionPreference = "Stop"

# Determine host (parameter > env var > default)
$HostParam = if ($BindHost) { $BindHost } elseif ($env:Z_EXPLORER_HOST) { $env:Z_EXPLORER_HOST } else { "127.0.0.1" }

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

# Check for Node.js
try {
    $null = Get-Command node -ErrorAction Stop
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js $nodeVersion already installed" -ForegroundColor Green
} catch {
    Write-Host "📦 Installing Node.js via winget..." -ForegroundColor Cyan

    try {
        $null = Get-Command winget -ErrorAction Stop
        # winget writes progress to stderr - redirect to suppress
        $wingetOutput = winget install OpenJS.NodeJS.LTS --accept-source-agreements --accept-package-agreements 2>&1
        if ($LASTEXITCODE -ne 0) {
            throw "winget failed: $wingetOutput"
        }

        # Refresh PATH
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

        # Verify installation
        $null = Get-Command node -ErrorAction Stop
        $nodeVersion = node --version 2>&1
        Write-Host "✓ Node.js $nodeVersion installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Node.js. Please install manually: https://nodejs.org/" -ForegroundColor Red
        exit 1
    }
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

# Determine install directory (installs in current directory by default)
$InstallDir = if ($env:Z_EXPLORER_DIR) { $env:Z_EXPLORER_DIR } else { "$(Get-Location)\z-Explorer" }

# Clone or update repository
if (Test-Path $InstallDir) {
    Write-Host "📁 Directory $InstallDir already exists" -ForegroundColor Cyan
    Write-Host "   Pulling latest changes..." -ForegroundColor Cyan
    Push-Location $InstallDir
    # Git writes progress to stderr, which PowerShell treats as error - redirect to suppress
    $pullOutput = git pull 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Git pull failed: $pullOutput" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    Write-Host "   $pullOutput" -ForegroundColor Gray
} else {
    Write-Host "📥 Cloning Z-Explorer to $InstallDir..." -ForegroundColor Cyan
    # Git writes progress to stderr, which PowerShell treats as error - redirect to suppress
    $cloneOutput = git clone https://github.com/pyros-projects/z-Explorer.git $InstallDir 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Git clone failed: $cloneOutput" -ForegroundColor Red
        exit 1
    }
    Push-Location $InstallDir
}

# Install dependencies
Write-Host "📦 Installing dependencies (this may take a few minutes)..." -ForegroundColor Cyan
# uv writes info to stderr, which PowerShell treats as error - redirect to suppress
$syncOutput = uv sync 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ uv sync failed: $syncOutput" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host $syncOutput -ForegroundColor Gray

Write-Host ""
Write-Host "✅ Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To run Z-Explorer:" -ForegroundColor Cyan
Write-Host "  cd $InstallDir" -ForegroundColor White
Write-Host "  uv run z-explorer" -ForegroundColor White
Write-Host ""

# Run with quick-setup (configures defaults and launches)
Write-Host ""
Write-Host "🚀 Launching Z-Explorer on $HostParam (models will download automatically)..." -ForegroundColor Cyan
Write-Host ""
# uv writes info to stderr - merge streams to prevent PowerShell error
uv run z-explorer --quick-setup --host $HostParam 2>&1

Pop-Location
