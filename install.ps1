# Adviser-CLI Premium Single-Command Installer for Windows (PowerShell)
# Zero-Infrastructure Local RAG Assistant

$ErrorActionPreference = "Stop"

# Clear Host and write a beautiful ASCII Banner
Clear-Host
Write-Host "    ___       __     _                     " -ForegroundColor Cyan
Write-Host "   /   | ____/ /_  __(_)____ ___  _____     " -ForegroundColor Cyan
Write-Host "  / /| |/ __  / | / / / ___/ _ \/ ___/     " -ForegroundColor Cyan
Write-Host " / ___ / /_/ /| |/ / (__  )  __/ /         " -ForegroundColor Cyan
Write-Host "/_/  |_\__,_/ |___/_/____/\___/_/          " -ForegroundColor Cyan
Write-Host "                                           " -ForegroundColor Cyan
Write-Host "Starting premium zero-infrastructure local RAG assistant installation..." -ForegroundColor White

# Step 1: Check Python Environment
Write-Host "`n[1/4] Checking Python environment..." -ForegroundColor Blue
$pythonCmd = "python"
try {
    $pythonVersionStr = & python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
} catch {
    try {
        $pythonVersionStr = & python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")'
        $pythonCmd = "python3"
    } catch {
        Write-Host "Error: Python is not installed or not in your system PATH." -ForegroundColor Red
        Write-Host "Please download and install Python 3.10+ from https://python.org" -ForegroundColor Yellow
        Exit 1
    }
}

$parts = $pythonVersionStr.Split('.')
$major = [int]$parts[0]
$minor = [int]$parts[1]

if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
    Write-Host "Error: Adviser requires Python 3.10 or higher. Found: $pythonVersionStr" -ForegroundColor Red
    Exit 1
}
Write-Host "✓ Found compatible Python $pythonVersionStr" -ForegroundColor Green

# Step 2: Establish Virtual Environment
Write-Host "`n[2/4] Initializing Python virtual environment..." -ForegroundColor Blue
if (-not (Test-Path "venv")) {
    & $pythonCmd -m venv venv
    Write-Host "✓ Created virtual environment in .\venv" -ForegroundColor Green
} else {
    Write-Host "✓ Virtual environment already exists at .\venv" -ForegroundColor Green
}

# Step 3: Install Package & Dependencies
Write-Host "`n[3/4] Sourcing environment and installing dependencies..." -ForegroundColor Blue

# Check for uv package manager
$hasUv = $false
try {
    $null = Get-Command uv -ErrorAction SilentlyContinue
    $hasUv = $true
} catch {}

if ($hasUv) {
    Write-Host "→ Found 'uv' package manager. Installing with maximum speed..." -ForegroundColor Cyan
    & .\venv\Scripts\pip.exe install uv
    & .\venv\Scripts\uv.exe pip install -e ".[dev]"
} else {
    Write-Host "→ 'uv' not found. Defaulting to standard pip..." -ForegroundColor Yellow
    & .\venv\Scripts\python.exe -m pip install --upgrade pip
    & .\venv\Scripts\pip.exe install -e ".[dev]"
}
Write-Host "✓ Successfully installed Adviser-CLI and all dependencies" -ForegroundColor Green

# Execute init automatically to get them started right away
$nonInteractive = $false
if ($args.Contains("--non-interactive") -or $env:ADVISER_NON_INTERACTIVE) {
    $nonInteractive = $true
}

if (-not $nonInteractive) {
    Write-Host "`nLaunching Adviser interactive Setup Wizard..." -ForegroundColor Cyan
    & .\venv\Scripts\adviser.exe init
} else {
    Write-Host "`n✓ Setup complete. You can now run 'adviser init' to configure your active profile." -ForegroundColor Green
}
