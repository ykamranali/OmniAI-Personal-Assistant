# Requires "Run as Administrator"
Write-Host "Installing OmniAI Prerequisites..." -ForegroundColor Cyan

# 1. Install Docker Desktop
Write-Host "Installing Docker Desktop..." -ForegroundColor Yellow
winget install Docker.DockerDesktop --accept-source-agreements --accept-package-agreements

# 2. Install Flutter
Write-Host "Installing Flutter..." -ForegroundColor Yellow
winget install Google.Flutter --accept-source-agreements --accept-package-agreements

# 3. Install Ollama
Write-Host "Installing Ollama..." -ForegroundColor Yellow
winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements

Write-Host "Installation commands executed. Please check for any installers that opened in the background." -ForegroundColor Green
Write-Host "You MUST restart your computer for Docker and Flutter to be recognized properly." -ForegroundColor Red
Write-Host "After restarting, run docker-compose up -d in this directory." -ForegroundColor Cyan
pause
