# SME Bridge MVP Development Environment Starter for Windows
# This script mirrors the functionality of dev.sh for PowerShell users.

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting SME Bridge MVP Development Environment..." -ForegroundColor Cyan

# 1. Setup environment variables if missing
if (-not (Test-Path "apps/api/.env")) {
    Write-Host "Creating apps/api/.env from example..." -ForegroundColor Gray
    Copy-Item "apps/api/.env.example" "apps/api/.env"
}

if (-not (Test-Path "apps/web/.env")) {
    Write-Host "Creating apps/web/.env from example..." -ForegroundColor Gray
    Copy-Item "apps/web/.env.example" "apps/web/.env"
}

# 2. Process tracking for cleanup
$Global:RunningProcesses = @()

function Stop-AllServices {
    Write-Host "`n🛑 Shutting down all SME Bridge MVP services..." -ForegroundColor Red
    foreach ($p in $Global:RunningProcesses) {
        if ($p -and -not $p.HasExited) {
            try {
                # Stop the process and all its children
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            } catch {
                # Ignore errors if process already closed
            }
        }
    }
    Write-Host "👋 Goodbye!" -ForegroundColor Gray
    exit
}

# 3. Setup and start Backend (FastAPI)
Write-Host "-----------------------------------------"
Write-Host "⚙️  Checking Backend (FastAPI)..." -ForegroundColor Yellow
Push-Location apps/api

$PythonExe = ".venv\Scripts\python.exe"
$UvicornExe = ".venv\Scripts\uvicorn.exe"

if (-not (Test-Path ".venv")) {
    Write-Host "Setting up Python virtual environment..." -ForegroundColor Gray
    python -m venv .venv
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r requirements-dev.txt
}

Write-Host "Starting FastAPI Server on Port 8000..." -ForegroundColor Gray
$apiProc = Start-Process $UvicornExe -ArgumentList "app.main:app --reload" -NoNewWindow -PassThru
$Global:RunningProcesses += $apiProc
Pop-Location

# 4. Start Background Worker
Write-Host "-----------------------------------------"
Write-Host "👷 Starting Background Worker..." -ForegroundColor Yellow
Push-Location apps/api
$workerProc = Start-Process $PythonExe -ArgumentList "-m app.processing.worker" -NoNewWindow -PassThru
$Global:RunningProcesses += $workerProc
Pop-Location

# 5. Setup and start Frontend (React)
Write-Host "-----------------------------------------"
Write-Host "🎨 Checking Frontend (React)..." -ForegroundColor Yellow
Push-Location apps/web

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing NPM dependencies..." -ForegroundColor Gray
    npm install
}

Write-Host "Starting React Dashboard (Vite)..." -ForegroundColor Gray
# On Windows, npm is usually a cmd or ps1 file, so we call it through the shell
$webProc = Start-Process npm -ArgumentList "run dev" -NoNewWindow -PassThru
$Global:RunningProcesses += $webProc
Pop-Location

Write-Host "========================================="
Write-Host "✅ SME Bridge MVP is running!" -ForegroundColor Green
Write-Host "   Dashboard: http://localhost:5173"
Write-Host "   API Docs:  http://localhost:8000/docs"
Write-Host "   (Make sure Ollama and Supabase are active)"
Write-Host ""
Write-Host "Press Ctrl+C to stop all services."
Write-Host "========================================="

# Keep script running to maintain background processes and handle Ctrl+C
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
}
catch {
    # This catches Ctrl+C
    Stop-AllServices
}
finally {
    Stop-AllServices
}
