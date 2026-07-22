<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/react-19-61dafb?style=for-the-badge&logo=react&logoColor=white" />
  <img src="https://img.shields.io/badge/platform-windows-0078d6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/status-active%20development-brightgreen?style=for-the-badge" />
</p>

<h1 align="center">
  <br>
  🤖 Mia
  <br>
  <sub><sup>Your Personal JARVIS for Windows</sup></sub>
</h1>

<p align="center">
  <strong>A local-first, voice-controlled AI assistant that can see your screen, click your buttons, launch your apps, and talk back — like JARVIS from Iron Man, but running on your machine.</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#%EF%B8%8F-architecture">Architecture</a> •
  <a href="#-the-dashboard">Dashboard</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-built-with-ai">Built with AI</a>
</p>

---

## 💡 What is Mia?

Mia is a **fully local AI assistant for Windows** that goes beyond chatbots. She doesn't just answer questions — she **takes action on your computer**.

She can see what's on your screen through real-time screen capture and Windows UI Automation, understand your intent through voice or text, and execute multi-step workflows by clicking buttons, typing text, launching apps, and running commands — all while speaking back to you through neural text-to-speech.

```
You:    "Hey Mia, open Chrome and search for the weather in Tokyo"
Mia:    *launches Chrome* → *clicks address bar* → *types query* → *presses Enter*
        "Done. Looks like it's 28°C and sunny in Tokyo."
```

### Why Mia?

| Feature | Traditional Assistants | Mia |
|---|---|---|
| **Privacy** | Sends everything to the cloud | Runs 100% locally by default (Ollama) |
| **Screen awareness** | Blind | Sees your active window in real-time |
| **System control** | Limited to pre-built integrations | Clicks any button, types anywhere, runs commands |
| **Voice** | Cloud-dependent | Local Whisper STT + Piper TTS — works offline |
| **Flexibility** | Locked to one provider | Hot-swap between Ollama, OpenAI, Anthropic, or Gemini |

---

## ✨ Features

### 🧠 Multi-Provider LLM Intelligence
Mia isn't locked to one AI. Switch between providers on-the-fly — even mid-conversation:

| Provider | Mode | Best For |
|---|---|---|
| **Ollama** (local) | `local` | Privacy, offline use, no API costs |
| **OpenAI** GPT-4o | `cloud` | Complex reasoning, tool calling |
| **Anthropic** Claude | `cloud` | Nuanced understanding |
| **Google** Gemini | `cloud` | Multimodal tasks |
| **Auto** | `auto` | Mia decides — simple tasks stay local, complex ones go cloud |

### 👁️ Screen Perception
Mia sees what you see. On every request, she:
1. **Captures your active monitor** via `mss` and downscales to 1280px for efficiency
2. **Extracts the UI accessibility tree** of your foreground window — every button, text field, and tab
3. **Sends both to the LLM** so she understands the full visual and structural context

### 🎤 Voice Interface
- **Push-to-Talk**: Hold `Right Ctrl` to speak, release to process
- **Wake Word**: "Hey Mia" detection (ONNX model slot ready)
- **Speech-to-Text**: `faster-whisper` with automatic CUDA→CPU fallback
- **Text-to-Speech**: `Piper` neural TTS for natural-sounding responses
- **Kill Switch**: `Ctrl+Shift+Pause` instantly halts all actions

### 🛠️ System Actions (Tool Calling)
Mia has 8 tools she can chain together in a ReAct loop:

| Tool | What it does |
|---|---|
| `launch_app(name)` | Launch any Windows application |
| `focus_window(title)` | Bring a window to the front by partial title |
| `click_element(name)` | Click a UI element by its accessibility name |
| `type_text(text)` | Type text into the focused input field |
| `hotkey(keys)` | Press keyboard combos like `ctrl+c`, `alt+tab` |
| `run_powershell(cmd)` | Execute safe, allowlisted PowerShell commands |
| `wait(seconds)` | Pause between actions for UI to settle |
| `respond(text)` | Speak a response back to the user via TTS |

### 🔒 Privacy-First Design
- **Local by default** — Ollama runs everything on your GPU, nothing leaves your machine
- **Sensitive app detection** — Banking, password managers, and authenticator apps are auto-blocked from screen uploads
- **Privacy redaction layer** — Password fields and sensitive UI elements are redacted before cloud requests
- **Configurable blocklist** — Add your own apps to `config/sensitive_apps.yaml`

### 📡 Real-Time Dashboard
A JARVIS-inspired web dashboard (React + FastAPI) that shows:
- **Arc Reactor Core** — An animated visualizer that responds to Mia's state (idle, thinking, acting, speaking)
- **Live Activity Feed** — Server-Sent Events streaming every action in real-time
- **Chat Interface** — Rich interaction log with typing indicators
- **Screen Preview** — Thumbnail of what Mia currently sees
- **Mode & Provider Switching** — Change AI provider or processing mode without restarting

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11**
- **Python 3.11+**
- **Node.js 18+** (for the dashboard)
- **[Ollama](https://ollama.com/)** (for local mode)

### 1. Clone & Setup

```bash
git clone https://github.com/JaydonJP/Mia.git
cd Mia
```

```powershell
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install Python dependencies
pip install -e .

# Pull Ollama models (requires Ollama installed)
.\scripts\setup_models.ps1
```

### 2. Install Dashboard

```powershell
cd ui
npm install
cd ..
```

### 3. Configure (Optional)

API keys go in `~/.mia/secrets.env`:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...
```

Edit `config/mia.yaml` to change defaults:
```yaml
llm:
  mode: local          # local | cloud | auto
  local:
    vision_model: qwen2.5vl:3b
  cloud:
    provider: openai   # openai | anthropic | gemini
    model: gpt-4o

voice:
  push_to_talk_key: right ctrl
  wake_word: "hey mia"
```

### 4. Run

**Terminal 1 — Backend:**
```powershell
cd src
python -m uvicorn mia.server:app --host 127.0.0.1 --port 8000
```

**Terminal 2 — Dashboard:**
```powershell
cd ui
npm run dev
```

**Open** → [http://localhost:5173](http://localhost:5173)

> **CLI-only mode** (no dashboard): `python -m mia` — runs with system tray + hotkeys only.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Mia Dashboard (React)                  │
│  Arc Reactor · Activity Feed · Chat · Screen Preview     │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP / SSE
┌────────────────────────┴─────────────────────────────────┐
│                  FastAPI Server (server.py)               │
│  /api/chat · /api/state · /api/events/stream · /api/...  │
└────────────────────────┬─────────────────────────────────┘
                         │
┌────────────────────────┴─────────────────────────────────┐
│                     Agent (agent.py)                      │
│  EventLog · SessionMemory · ReAct Loop · State Machine   │
├──────────┬───────────┬───────────┬───────────────────────┤
│ LLM      │ Perception│ Actions   │ Voice                 │
│ Router   │           │           │                       │
│ ┌──────┐ │ ┌───────┐ │ ┌───────┐ │ ┌──────┐ ┌────────┐  │
│ │Ollama│ │ │Screen │ │ │Launch │ │ │Whispr│ │Piper   │  │
│ │OpenAI│ │ │Capture│ │ │Click  │ │ │ STT  │ │TTS     │  │
│ │Anthro│ │ │A11y   │ │ │Type   │ │ └──────┘ └────────┘  │
│ │Gemini│ │ │Tree   │ │ │Hotkey │ │                       │
│ └──────┘ │ └───────┘ │ │Shell  │ │                       │
│          │           │ └───────┘ │                       │
└──────────┴───────────┴───────────┴───────────────────────┘
```

### Project Structure

```
Mia/
├── config/
│   ├── mia.yaml              # Main configuration
│   └── sensitive_apps.yaml   # Privacy blocklist
├── src/mia/
│   ├── __main__.py            # CLI entry point (system tray mode)
│   ├── app.py                 # System tray + hotkey manager
│   ├── server.py              # FastAPI backend for dashboard
│   ├── core/
│   │   ├── agent.py           # Brain — ReAct loop + EventLog
│   │   ├── memory.py          # Conversation session memory
│   │   └── prompts.py         # JARVIS personality prompt
│   ├── llm/
│   │   ├── base.py            # Abstract LLM provider interface
│   │   ├── router.py          # Smart routing (local/cloud/auto)
│   │   ├── ollama_client.py   # Local Ollama integration
│   │   ├── openai_client.py   # OpenAI GPT-4o client
│   │   ├── anthropic_client.py # Anthropic Claude client
│   │   └── gemini_client.py   # Google Gemini client
│   ├── perception/
│   │   ├── screen.py          # Screen capture (mss + Pillow)
│   │   └── accessibility.py   # Windows UI Automation tree extraction
│   ├── actions/
│   │   ├── executor.py        # Tool registry + execution
│   │   ├── apps.py            # App launch + window focus
│   │   ├── input.py           # Keyboard input + UI element clicking
│   │   └── shell.py           # Safe PowerShell execution
│   ├── voice/
│   │   ├── stt.py             # faster-whisper speech-to-text
│   │   ├── tts.py             # Piper neural text-to-speech
│   │   └── wake_word.py       # Wake word detection
│   ├── privacy/
│   │   └── redaction.py       # PII redaction + sensitive app blocking
│   └── tools/
│       └── registry.py        # OpenAI-compatible tool schema registry
├── ui/                        # React + Vite dashboard
│   ├── src/
│   │   ├── App.jsx            # JARVIS dashboard
│   │   ├── index.css          # Premium dark UI styling
│   │   └── main.jsx           # Entry point
│   └── index.html
├── scripts/
│   ├── setup.ps1              # Windows Defender exclusion
│   └── setup_models.ps1       # Download Ollama models
├── models/                    # Local model files (Piper, wake word)
├── pyproject.toml
└── README.md
```

---

## 🎨 The Dashboard

The web dashboard is a JARVIS-inspired command center built with React and vanilla CSS.

### Design Highlights
- **Arc Reactor Visualizer** — Three concentric CSS-animated rings orbit a pulsing core. Animation speed and color change dynamically based on Mia's state:
  - 🔵 **Idle** — Slow, calm blue pulse
  - 🟡 **Thinking** — Fast golden spin
  - 🟣 **Acting** — Intense violet acceleration
  - 🟢 **Speaking** — Green wave pattern
- **Glassmorphism** — Frosted glass panels with blue-tinted borders over a deep navy background with animated gradient orbs
- **Real-time SSE Feed** — Every internal event (tool call, result, state change) streams to the UI instantly
- **Typography** — Inter for body text, JetBrains Mono for the activity log
- **Responsive** — Sidebar collapses on smaller screens

---

## ⚙️ Configuration

### `config/mia.yaml`

| Key | Values | Description |
|---|---|---|
| `llm.mode` | `local` / `cloud` / `auto` | Default processing mode |
| `llm.local.vision_model` | Ollama model name | Model for screen understanding |
| `llm.cloud.provider` | `openai` / `anthropic` / `gemini` | Cloud AI provider |
| `llm.cloud.model` | Model identifier | Specific model to use |
| `voice.push_to_talk_key` | Key name | PTT hotkey (default: `right ctrl`) |
| `voice.wake_word` | String | Wake phrase (default: `hey mia`) |

### `config/sensitive_apps.yaml`

Apps in this blocklist will have their screen captures blocked from cloud uploads:
```yaml
blocklist:
  - "Bank"
  - "Bitwarden"
  - "1Password"
  - "Settings"
```

---

## 🛣️ Roadmap

- [x] **Phase 0** — Project scaffolding, dependency setup
- [x] **Phase 1** — Voice shell (wake word, PTT, STT, TTS)
- [x] **Phase 2** — Screen perception (capture + UI tree extraction)
- [x] **Phase 2b** — Multi-provider cloud mode (OpenAI, Anthropic, Gemini)
- [x] **Phase 3** — System actions (tool registry, ReAct loop)
- [x] **Phase 4** — Reliable automation (post-action verification, session memory)
- [x] **Phase 5** — JARVIS dashboard (React + FastAPI + SSE)
- [ ] **Phase 6** — Custom Piper voice fine-tuning
- [ ] **Phase 7** — Proactive mode (Mia suggests actions based on context)
- [ ] **Phase 8** — App-specific shortcut profiles
- [ ] **Phase 9** — Floating overlay widget (always-on-screen HUD)

---

## 🤖 Built with AI

This project was built through **human-AI pair programming** — a real-world demonstration of how modern AI coding assistants accelerate development.

### The Development Process

**Phase 1–4** were built with **Gemini 3.1 Pro**, which:
- Scaffolded the full project structure and `pyproject.toml`
- Implemented the voice pipeline (STT, TTS, wake word)
- Built the screen perception system (mss + uiautomation)
- Created all 4 LLM provider clients (Ollama, OpenAI, Anthropic, Gemini)
- Wrote the tool registry and action executors
- Set up the initial FastAPI server and basic React UI

**Phase 5 (JARVIS Rebuild)** was executed by **Claude Opus 4**, which:
- Audited the entire codebase and identified **18 critical issues** (including a crash-causing missing method, dead code paths, and a server that crashed on import)
- Rewrote the `Agent` class with a thread-safe `EventLog` system for real-time event streaming
- Rebuilt the FastAPI server from scratch with lazy initialization, SSE streaming, 8 endpoints, and proper error handling
- Redesigned the entire dashboard UI as a JARVIS-inspired command center with an animated arc-reactor visualizer, glassmorphism panels, and state-responsive animations
- Wrote this README

> The codebase demonstrates how different AI models bring different strengths: Gemini for rapid scaffolding and broad implementation, Claude for deep auditing, architectural fixes, and premium polish.

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+, JavaScript (React) |
| **Local LLM** | Ollama (Qwen 2.5 VL) |
| **Cloud LLM** | OpenAI, Anthropic, Google Gemini |
| **Voice STT** | faster-whisper (CUDA/CPU) |
| **Voice TTS** | Piper (ONNX neural voices) |
| **Screen Capture** | mss + Pillow |
| **UI Automation** | uiautomation + pywinauto |
| **Backend** | FastAPI + Uvicorn |
| **Frontend** | React 19 + Vite |
| **Streaming** | Server-Sent Events (SSE) |

---

## 📄 License

This project is for educational and personal use. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ☕, 🎵, and way too many terminal tabs by <a href="https://github.com/JaydonJP">@JaydonJP</a></sub>
  <br>
  <sub>Pair programmed with Gemini 3.1 Pro & Claude Opus 4</sub>
</p>
