#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Quick activation script for Stock Sentinel backend development

.DESCRIPTION
    Activates the backend virtual environment and sets up the terminal
    for development. Just run: .\activate.ps1

.EXAMPLE
    PS> .\activate.ps1
    (.venv) PS C:\Users\acer\Downloads\stock sentinal\backend>
#>

# Get current location
$rootPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Navigate to backend
$backendPath = Join-Path $rootPath "backend"

if (-not (Test-Path $backendPath)) {
    Write-Host "❌ Error: 'backend' folder not found at $backendPath" -ForegroundColor Red
    exit 1
}

# Check if .venv exists
$venvPath = Join-Path $backendPath ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Error: .venv not found at $venvPath" -ForegroundColor Red
    Write-Host ""
    Write-Host "To create a new virtual environment, run:" -ForegroundColor Yellow
    Write-Host "  cd $backendPath"
    Write-Host "  python -m venv .venv"
    exit 1
}

# Check if activation script exists
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "❌ Error: Activation script not found at $activateScript" -ForegroundColor Red
    exit 1
}

# Navigate to backend and activate venv
Set-Location $backendPath
Write-Host "📂 Changed directory to: $backendPath" -ForegroundColor Cyan
Write-Host ""

# Activate
& $activateScript

# Verify activation
if ($env:VIRTUAL_ENV) {
    Write-Host ""
    Write-Host "✅ Virtual environment activated successfully!" -ForegroundColor Green
    Write-Host "📦 Python version: $(python --version)" -ForegroundColor Cyan
    Write-Host "📦 Pip version: $(pip --version).split()[1]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📝 Helpful commands:" -ForegroundColor Yellow
    Write-Host "  pip list                  - List all packages"
    Write-Host "  pip show <package>        - Show package details"
    Write-Host "  pip freeze > req.txt      - Generate requirements"
    Write-Host "  uvicorn app.main:app --reload  - Start FastAPI app"
    Write-Host "  deactivate                - Exit virtual environment"
    Write-Host ""
} else {
    Write-Host "❌ Failed to activate virtual environment" -ForegroundColor Red
    exit 1
}
