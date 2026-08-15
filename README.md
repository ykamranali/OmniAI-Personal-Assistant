# OmniAI Personal Assistant

**OmniAI** is an AI Operating System built with a Next.js + Tauri desktop frontend and a Python FastAPI backend. It features voice interaction (including an always-on, wake-word-activated local voice loop), local AI models via Ollama, and desktop automation via Playwright and PyAutoGUI.

## Architecture
- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind, packaged as a native desktop app with Tauri.
- **Backend**: FastAPI, Python 3.12, WebSockets.
- **Database**: PostgreSQL with `pgvector` for semantic long-term memory (ChromaDB is used as the local vector store by default).
- **AI Core**: Ollama (chat + vision models), faster-whisper (STT), edge-tts (TTS), openWakeWord (wake-word detection).
- **Automation**: Playwright (Web), PyAutoGUI (OS) — see "OS Automation Safety" below.

## Key Features

- **Chat** — text chat against any local Ollama model, with streaming responses and long-term memory (approve/deny before anything is saved).
- **OS Automation Agent** — a screenshot-driven vision loop that can click, type, scroll, and operate your desktop on request. Gated behind an explicit "OS Control" toggle, and pauses for your approval before anything that looks sensitive (deleting data, sending messages, spending money, handling credentials).
- **Always-on Voice Assistant** — an optional, fully local wake-word loop (openWakeWord + faster-whisper + edge-tts) that lets you talk hands-free, with barge-in support (you can interrupt it while it's speaking). Configure it in Settings.

## Getting Started

### 1. Prerequisites
Ensure you have the following installed on your machine:
- **Python 3.12**
- **Node.js** (for the Next.js/Tauri frontend) and **Rust** (required by Tauri)
- **Docker Desktop** (for the PostgreSQL database)
- **Ollama** (for local inference — pull a fast chat model and a vision-capable model: `ollama pull llama3.2:3b` and `ollama pull llama3.2-vision`. `llama3.2:3b` is the default because it responds much faster than larger models on typical hardware; swap in a bigger model via Settings if you have the GPU for it and want higher-quality answers.)
- A working **microphone and speakers** if you want to use the always-on voice assistant

> *Tip: Windows users can simply right-click and "Run as administrator" on the `install_dependencies.bat` file to automatically install Docker and Ollama.*

### 2. Backend Setup
1. Open a terminal in the `backend` folder.
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install
   ```
4. Start the Database:
   Navigate to the root directory and run:
   ```bash
   docker-compose up -d
   ```
5. Start the FastAPI server (Or use `start_backend.bat`):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

### 3. Frontend Setup
1. Open a terminal in the `frontend` folder.
2. Install packages:
   ```bash
   npm install
   ```
3. Run the desktop application in development mode:
   ```bash
   npm run tauri dev
   ```
   (Or `npm run dev` to run just the Next.js UI in a browser at `http://localhost:3000`, without the Tauri shell.)

## OS Automation Safety

The OS agent (Settings → OS Control) can see your screen and control the mouse/keyboard. A few safeguards are built in:
- It only runs when "OS Control" is explicitly enabled.
- Requests that match risky patterns (delete/remove/uninstall, send a message/email, pay/purchase/transfer, passwords/credentials, etc.) pause and require your explicit approval before anything happens.
- Each run is capped by a step limit and a time budget (configurable in Settings).
- Every executed action is logged to `backend/logs/os_agent_actions.log` for review.

These are heuristics, not a security boundary — only enable OS Control for tasks you'd trust an assistant to actually carry out.

## Project Structure
- `/backend`: The FastAPI application, Agents, Plugins, and AI services.
- `/frontend`: The Next.js UI, wrapped as a native desktop app via Tauri (`frontend/src-tauri`).
- `/docker`: Container configurations for pgvector.

## Testing
Run the backend test suite using `pytest`:
```bash
cd backend
pytest
```
