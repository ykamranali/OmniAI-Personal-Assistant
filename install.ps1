$ErrorActionPreference = "Stop"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Omni AI Personal Agent - Self Installer " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

function Check-Command {
    param([string]$CommandName, [string]$DisplayName)
    Write-Host "Checking for $DisplayName..." -NoNewline
    if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
        Write-Host " [OK]" -ForegroundColor Green
        return $true
    } else {
        Write-Host " [MISSING]" -ForegroundColor Red
        return $false
    }
}

$missing = @()

if (-not (Check-Command "python" "Python")) { $missing += "Python" }
if (-not (Check-Command "node" "Node.js")) { $missing += "Node.js" }
if (-not (Check-Command "git" "Git")) { $missing += "Git" }
if (-not (Check-Command "docker" "Docker")) { 
    Write-Host "Docker is missing. If you have DockerSetup.exe, please install it." -ForegroundColor Yellow
    $missing += "Docker" 
}

if (-not (Check-Command "ollama" "Ollama")) {
    Write-Host "Ollama not found. Attempting to install Ollama..." -ForegroundColor Yellow
    if (Test-Path ".\OllamaSetup.exe") {
        Write-Host "Running OllamaSetup.exe silently..." -ForegroundColor Cyan
        Start-Process -FilePath ".\OllamaSetup.exe" -ArgumentList "/S" -Wait
        Write-Host "Ollama installed. Waiting for service to start..." -ForegroundColor Cyan
        Start-Sleep -Seconds 10
    } else {
        $missing += "Ollama"
    }
}

if ($missing.Count -gt 0) {
    Write-Host "`nThe following prerequisites are still missing: $($missing -join ', ')" -ForegroundColor Yellow
    $ans = Read-Host "Do you want to continue without them and install manually? (y/N)"
    if ($ans -notmatch "^y") {
        Write-Host "Please install the missing prerequisites and run this script again." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`nPulling default AI model (llama3.1) via Ollama..." -ForegroundColor Cyan
Write-Host "This may take a few minutes depending on your internet connection."
& ollama pull llama3.1

Write-Host "`nSetting up Python Virtual Environment..." -ForegroundColor Cyan
if (-not (Test-Path "backend\venv")) {
    python -m venv backend\venv
}

Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
& "backend\venv\Scripts\pip.exe" install -r backend\requirements.txt
& "backend\venv\Scripts\pip.exe" install edge-tts
if ($LASTEXITCODE -ne 0) { Write-Host "Error installing Python packages." -ForegroundColor Red; exit 1 }

Write-Host "Installing Playwright browsers..." -ForegroundColor Cyan
& "backend\venv\Scripts\playwright.exe" install
if ($LASTEXITCODE -ne 0) { Write-Host "Error installing Playwright." -ForegroundColor Red; exit 1 }

Write-Host "`nSetting up Frontend..." -ForegroundColor Cyan
Set-Location "frontend"
npm install
if ($LASTEXITCODE -ne 0) { Write-Host "Error installing Node packages." -ForegroundColor Red; exit 1 }
Set-Location ".."

Write-Host "`nGenerating .env templates..." -ForegroundColor Cyan
if (-not (Test-Path "backend\.env")) {
    Set-Content "backend\.env" "DATABASE_URL=postgresql://user:password@localhost:5432/omniai`nCHROMA_PATH=./chroma_db`nOLLAMA_BASE_URL=http://localhost:11434"
    Write-Host "Created backend\.env template." -ForegroundColor Green
}

Write-Host "`nInitializing Database Containers..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "`n=========================================" -ForegroundColor Cyan
Write-Host " Installation Complete! " -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "To start the backend:"
Write-Host "  cd backend; .\venv\Scripts\uvicorn app.main:app --reload"
Write-Host "To start the frontend/desktop app:"
Write-Host "  cd frontend; npm run tauri dev"
