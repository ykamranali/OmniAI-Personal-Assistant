@echo off
echo Installing OmniAI Prerequisites...

echo.
echo Installing Docker Desktop...
winget install Docker.DockerDesktop --accept-source-agreements --accept-package-agreements

echo.
echo Installing Flutter...
winget install Google.Flutter --accept-source-agreements --accept-package-agreements

echo.
echo Installing Ollama...
winget install Ollama.Ollama --accept-source-agreements --accept-package-agreements

echo.
echo Installation commands executed. Please check for any installers that opened in the background.
echo You MUST restart your computer for Docker and Flutter to be recognized properly.
echo After restarting, run docker-compose up -d in this directory.
pause
