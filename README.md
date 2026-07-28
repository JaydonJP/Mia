<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/platform-windows-0078d6?style=for-the-badge&logo=windows&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM-ollama%20%7C%20openai%20%7C%20claude%20%7C%20gemini-ff6b35?style=for-the-badge" />
  <img src="https://img.shields.io/badge/status-active%20development-brightgreen?style=for-the-badge" />
</p>

<h1 align="center">
  <br>
  🤖 Mia
  <br>
  <sub><sup>Your Personal JARVIS for Windows</sup></sub>
</h1>

<p align="center">
  <strong>A local-first, autonomous AI desktop assistant that can see your screen, search the web, launch your apps, manage files, run workflows, and talk back — like JARVIS from Iron Man, but running on your machine.</strong>
</p>

<p align="center">
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-features">Features</a> •
  <a href="#-tools">Tools</a> •
  <a href="#%EF%B8%8F-architecture">Architecture</a> •
  <a href="#-configuration">Configuration</a> •
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 💡 What is Mia?

Mia is a **fully local AI assistant for Windows** that goes beyond chatbots. She doesn't just answer questions — she **takes real action on your computer**.

She can see what's on your screen, understand your intent through voice or text, search the web, read files, execute multi-step workflows, and speak back — all transparently logged to the terminal so you always know exactly what's happening.

```
You:  "Hey Mia, activate study mode"
Mia:  [System]  Activating workflow: study_mode
      [Tool]    Executing: launch_app({"name": "notion"})
      [Tool]    Result: Launched notion (via known app registry)
      [Tool]    Executing: launch_app({"name": "spotify"})
      [Tool]    Result: Launched spotify (via known app registry)
      [Tool]    Executing: open_url({"url": "https://scholar.google.com"})
      [Tool]    Result: Opened URL: https://scholar.google.com
      ╭─ Mia ──────────────────────────────────────────────╮
      │ Study mode activated. Notion, Spotify, and Google  │
      │ Scholar are all open and ready for you.            │
      ╰────────────────────────────────────────────────────╯
```

### Why Mia?

| Feature | Traditional Assistants | Mia |
|---|---|---|
| **Privacy** | Sends everything to the cloud | Runs 100% locally by default (Ollama) |
| **Screen awareness** | Blind | Sees your active window in real-time |
| **System control** | Pre-built integrations only | Clicks buttons, types anywhere, runs workflows |
| **Web access** | None (local models) | Real web search + page reading |
| **File management** | None | Read, write, list files and folders |
| **Memory** | Session-only | Persistent SQLite DB across restarts |
| **Transparency** | Black box | Every tool call logged in your terminal |
| **Flexibility** | Locked to one provider | Hot-swap Ollama ↔ OpenAI ↔ Claude ↔ Gemini |

---

## ✨ Features

### 🧠 Multi-Provider LLM Intelligence
Mia uses a proper **ReAct (Reason + Act) loop** — not one-shot answers. She reasons about tool results, chains multiple actions, and verifies outcomes before responding. Switch providers on-the-fly, even mid-conversation:

| Provider | Mode | Best For |
|---|---|---|
| **Ollama** (local) | `local` | Privacy, offline use, no API costs |
| **OpenAI** GPT-4o | `cloud` | Complex reasoning, reliable tool calling |
| **Anthropic** Claude | `cloud` | Nuanced understanding, careful execution |
| **Google** Gemini | `cloud` | Multimodal tasks, fast responses |
| **Auto** | `auto` | Mia decides — simple tasks stay local, complex ones go cloud |

All four providers support **native tool calling** with full multi-turn context, so Mia never loses track of what she's doing mid-task.

### 🖥️ Rich Terminal UI
The primary interface is a beautiful, transparent terminal REPL powered by `rich`:
- **Animated spinner** during LLM thinking (with elapsed time)
- **Color-coded log prefixes**: `[System]` cyan, `[Tool]` yellow, `[LLM]` green, `[Error]` red, `[Network]` blue
- **Styled response panels** for Mia's final replies
- **Built-in commands**: `mode`, `model`, `clear`, `tools`, `workflows`, `help`

### 👁️ Screen & Context Awareness
On every request, Mia can:
1. **Capture your active monitor** via `mss`, downscaled to 1280px for efficiency
2. **Extract the UI accessibility tree** of your foreground window — every button, field, and tab
3. **Send both to the LLM** for full visual + structural context

### 🎤 Voice Interface (Optional)
- **Push-to-Talk**: Hold `Right Ctrl` to speak, release to process
- **Wake Word**: "Hey Mia" detection (ONNX model slot ready for `openWakeWord`)
- **Speech-to-Text**: `faster-whisper` with automatic CUDA→CPU fallback
- **Text-to-Speech**: `Piper` neural TTS for natural-sounding replies
- **Kill Switch**: `Ctrl+Shift+Pause` instantly halts all input simulation

### 🔒 Privacy-First Design
- **Local by default** — Ollama runs everything on your GPU, nothing leaves your machine
- **Sensitive app detection** — Banking, password managers, and authenticators are auto-blocked from screen uploads
- **Privacy redaction** — Password fields and sensitive UI elements are stripped before cloud requests
- **Configurable blocklist** — Add your own apps to `config/sensitive_apps.yaml`

### 💾 Persistent Memory
Mia remembers across sessions via a **SQLite database** at `~/.mia/mia.db`:
- Conversation history (bootstrapped on startup)
- Action log (every tool call with timestamp and result)
- User profile (name, preferences — set via `mia.set_profile()`)

### 📡 FastAPI Dashboard (Optional)
A web dashboard with FastAPI + SSE streaming:
- Real-time activity feed
- Chat interface
- Screen preview
- Mode & provider switching
- 9 REST endpoints

---

## 🛠️ Tools

Mia has **17 tools** she can chain together in a multi-turn ReAct loop:

### App & Window Management
| Tool | Description |
|---|---|
| `launch_app(name)` | Launch any Windows app. 4-strategy: known registry → Start Menu shortcuts → PATH → fallback |
| `open_url(url)` | Open a URL in the default browser |
| `focus_window(title)` | Bring a window to the front by partial title match |

### Keyboard & UI Interaction
| Tool | Description |
|---|---|
| `type_text(text)` | Type text into the focused input field |
| `hotkey(keys)` | Press keyboard combos (`ctrl+c`, `alt+tab`, `win+e`, etc.) |
| `click_element(name)` | Click a UI element by its accessibility name |

### Web & Information
| Tool | Description |
|---|---|
| `web_search(query)` | Search the web via DuckDuckGo (or Google). Returns titles, URLs, and snippets |
| `read_webpage(url)` | Fetch a URL and extract the main text content |

### File System
| Tool | Description |
|---|---|
| `list_directory(path)` | List files and folders (sandboxed to allowed dirs) |
| `read_file(path)` | Read file contents (up to 10 KB) |
| `write_file(path, content)` | Create or overwrite a file |
| `create_directory(path)` | Create a directory and its parents |

### Workflows
| Tool | Description |
|---|---|
| `activate_workflow(name)` | Run a named automation sequence (e.g., `study_mode`, `work_mode`) |
| `list_workflows()` | Show all available workflows |

### System
| Tool | Description |
|---|---|
| `run_powershell(cmd)` | Execute allowlisted PowerShell commands (destructive ops blocked) |
| `wait(seconds)` | Pause between actions for UI to settle |
| `respond(text)` | Speak/display a response to the user |

---

## 🚀 Quick Start

### Prerequisites
- **Windows 10/11**
- **Python 3.11+**
- **[Ollama](https://ollama.com/)** (for local mode — optional if using cloud APIs)

### 1. Clone & Setup

```bash
git clone https://github.com/JaydonJP/Mia.git
cd Mia
```

```powershell
# Create virtual environment and install
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

### 2. Pull a Local Model (Optional — for local mode)

```powershell
# Install Ollama from https://ollama.com, then:
ollama pull qwen2.5vl:3b   # Recommended for 8GB VRAM
# or
ollama pull qwen2.5vl:7b   # Better quality, needs 12GB VRAM
```

### 3. Configure API Keys (Optional — for cloud mode)

Create `~/.mia/secrets.env`:
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# For Google Custom Search (optional)
GOOGLE_SEARCH_API_KEY=...
GOOGLE_SEARCH_CX=...
```

### 4. Run

```powershell
# Interactive CLI (primary interface)
python -m mia

# Use cloud mode
python -m mia --mode cloud

# Start FastAPI backend (for web dashboard)
python -m mia --server
```

That's it. No Node.js required to use Mia. The CLI is the primary interface.

---

## 🖥️ CLI Interface

```
 ╔══════════════════════════════════════════╗
 ║         M I A  •  AI Assistant          ║
 ╠══════════════════════════════════════════╣
 ║  Mode: local       Model: Ollama (qwen2.5vl:3b) ║
 ║  Type 'quit' to exit, 'help' for commands ║
 ╚══════════════════════════════════════════╝

 You > open spotify
  [System]  Sending to Ollama (qwen2.5vl:3b) (step 1)...
  [Tool]    Executing: launch_app({"name": "spotify"})
  [Tool]    Result: Launched spotify (via known app registry)
  [System]  Sending to Ollama (qwen2.5vl:3b) (step 2)...
╭─ Mia ─────────────────────────────────╮
│ Spotify is open. Enjoy the music! 🎵  │
╰────────────────────────────────────────╯
```

### Built-in Commands

| Command | Description |
|---|---|
| `quit` / `exit` | Exit Mia |
| `mode local\|cloud\|auto` | Switch LLM mode |
| `model` | Show current model info |
| `clear` | Clear conversation history |
| `tools` | List all 17 available tools |
| `workflows` | List available automation workflows |
| `help` | Show all commands |

---

## 🏗️ Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Input Layer                                  │
│    CLI REPL (primary) · Voice PTT · FastAPI /api/chat          │
└───────────────────────────┬────────────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────────────┐
│                    Agent (agent.py)                             │
│  ReAct Loop · EventLog · Persistent DB · State Machine         │
│                                                                 │
│  ┌──── LLM Router ────┐  ┌── Tool Executor (17 tools) ──────┐  │
│  │ Ollama  (local)    │  │ launch_app · open_url            │  │
│  │ OpenAI  (cloud)    │  │ web_search · read_webpage        │  │
│  │ Anthropic (cloud)  │  │ list_dir · read_file · write_file│  │
│  │ Gemini  (cloud)    │  │ activate_workflow · run_powershell│  │
│  │ Auto    (smart)    │  │ type_text · hotkey · click_element│  │
│  └────────────────────┘  └──────────────────────────────────┘  │
│                                                                 │
│  ┌── Memory ────────────────────────────────────────────────┐   │
│  │ SessionMemory (in-RAM) · MiaDatabase (SQLite, ~/.mia/db) │   │
│  └──────────────────────────────────────────────────────────┘   │
└───────────────────────────┬────────────────────────────────────┘
                            │
┌───────────────────────────┴────────────────────────────────────┐
│                    Output Layer                                 │
│    Rich Terminal UI · Piper TTS · SSE Event Stream             │
└────────────────────────────────────────────────────────────────┘
```

### Project Structure

```
Mia/
├── config/
│   ├── mia.yaml              # Main configuration
│   ├── workflows.yaml        # Named workflow automations
│   └── sensitive_apps.yaml   # Privacy blocklist
├── src/mia/
│   ├── __main__.py            # CLI entry point (interactive REPL)
│   ├── app.py                 # System tray + hotkey manager
│   ├── server.py              # FastAPI backend (9 endpoints)
│   ├── core/
│   │   ├── agent.py           # ReAct loop + EventLog + state machine
│   │   ├── database.py        # SQLite persistent storage
│   │   ├── memory.py          # Session + persistent memory
│   │   └── prompts.py         # Dynamic system prompt builder
│   ├── llm/
│   │   ├── base.py            # LLMProvider interface + LLMResponse/ToolCall
│   │   ├── router.py          # Smart routing (local/cloud/auto)
│   │   ├── ollama_client.py   # Local Ollama (native tool calling)
│   │   ├── openai_client.py   # OpenAI GPT-4o (vision + tools)
│   │   ├── anthropic_client.py # Claude (tool_use/tool_result blocks)
│   │   └── gemini_client.py   # Gemini (FunctionDeclaration format)
│   ├── actions/
│   │   ├── executor.py        # Tool registration (all 17 tools)
│   │   ├── apps.py            # 4-strategy app launcher + open_url
│   │   ├── web.py             # DuckDuckGo + Google search + page reader
│   │   ├── files.py           # Sandboxed file system operations
│   │   ├── workflows.py       # Named workflow engine
│   │   ├── input.py           # Keyboard + UI element clicking
│   │   └── shell.py           # Safe PowerShell execution (allowlist)
│   ├── perception/
│   │   ├── screen.py          # Screen capture (mss + Pillow)
│   │   └── accessibility.py   # Windows UI Automation tree
│   ├── voice/
│   │   ├── stt.py             # faster-whisper STT (CUDA/CPU)
│   │   ├── tts.py             # Piper neural TTS
│   │   └── wake_word.py       # Wake word detection
│   ├── ui/
│   │   └── console.py         # Rich terminal UI (spinner, logs, panels)
│   ├── privacy/
│   │   └── redaction.py       # PII redaction + sensitive app blocking
│   └── tools/
│       └── registry.py        # OpenAI-compatible tool schema registry
├── models/                    # Local model files (Piper voice, wake word)
├── logs/                      # Action audit log
├── pyproject.toml
└── README.md
```

---

## ⚙️ Configuration

### `config/mia.yaml`

```yaml
llm:
  mode: local          # local | cloud | auto
  local:
    provider: ollama
    vision_model: qwen2.5vl:3b   # or :7b for better quality
  cloud:
    provider: gemini   # openai | anthropic | gemini
    model: gemini-3.5-flash

voice:
  push_to_talk_key: right ctrl
  wake_word: "hey mia"

web_search:
  provider: duckduckgo  # duckduckgo | google

filesystem:
  allowed_dirs:
    - "~"           # User home (default)
    # - "C:\\Projects"
```

### `config/workflows.yaml`

Define named automation sequences:

```yaml
workflows:
  study_mode:
    description: "Open Notion, Spotify, and Google Scholar"
    actions:
      - type: launch_app
        target: notion
        delay: 2
      - type: launch_app
        target: spotify
        delay: 2
      - type: open_url
        target: "https://scholar.google.com"

  work_mode:
    description: "Open VS Code, Slack, and Gmail"
    actions:
      - type: launch_app
        target: vscode
        delay: 2
      - type: launch_app
        target: slack
        delay: 2
      - type: open_url
        target: "https://mail.google.com"
```

Activate with: `"Mia, activate study mode"` or `> activate_workflow study_mode`

### `config/sensitive_apps.yaml`

Apps whose screen content is blocked from cloud uploads:
```yaml
blocklist:
  - "Bank"
  - "Bitwarden"
  - "1Password"
  - "Authenticator"
  - "Settings"
```

---

## 🛣️ Roadmap

- [x] **v0.1** — Project scaffolding, voice pipeline (STT/TTS/wake word)
- [x] **v0.1** — Screen perception (mss + Windows UI Automation)
- [x] **v0.1** — Multi-provider cloud mode (OpenAI, Anthropic, Gemini)
- [x] **v0.1** — Tool registry + basic action execution
- [x] **v0.1** — FastAPI backend + SSE event streaming
- [x] **v0.2** — Fixed multi-turn ReAct agent loop (tool results fed back to LLM)
- [x] **v0.2** — Fixed app launcher (4-strategy: registry → Start Menu → PATH → fallback)
- [x] **v0.2** — Fixed Anthropic & Gemini tool calling (was completely broken)
- [x] **v0.2** — Rich terminal UI (spinners, colored logs, interactive REPL)
- [x] **v0.2** — Web search (DuckDuckGo + Google Custom Search option)
- [x] **v0.2** — File system tools (sandboxed read/write/list)
- [x] **v0.2** — Named workflow engine (`config/workflows.yaml`)
- [x] **v0.2** — Persistent SQLite memory across sessions
- [ ] **v0.3** — Google Calendar integration (read + create events)
- [ ] **v0.3** — Proactive mode (Mia suggests actions when she notices context changes)
- [ ] **v0.3** — Custom Piper voice fine-tuning
- [ ] **v0.4** — Floating overlay HUD (always-on-screen status widget)
- [ ] **v0.4** — App-specific tool profiles (browser, VS Code, Spotify)

---

## 🧰 Tech Stack

| Layer | Technology |
|---|---|
| **Language** | Python 3.11+ |
| **Local LLM** | Ollama — Qwen 2.5 VL (3B/7B) |
| **Cloud LLM** | OpenAI GPT-4o · Anthropic Claude · Google Gemini |
| **Agent Loop** | Custom ReAct (multi-turn tool calling, max 10 steps) |
| **Persistent Storage** | SQLite via `sqlite3` (built-in) |
| **Terminal UI** | Rich (spinners, panels, color themes) |
| **Voice STT** | faster-whisper (CUDA/CPU auto-detect) |
| **Voice TTS** | Piper (ONNX neural voices) |
| **Web Search** | ddgs (DuckDuckGo) · Google Custom Search API |
| **Screen Capture** | mss + Pillow |
| **UI Automation** | uiautomation + pywinauto |
| **Backend** | FastAPI + Uvicorn + SSE |

---

## 🤖 Built with AI

This project was built through **human-AI pair programming**.

**v0.1** was scaffolded with **Gemini**, which built the initial voice pipeline, screen perception, all 4 LLM provider clients, the tool registry, and the FastAPI server.

**The JARVIS dashboard** was designed and implemented by **Claude Opus 4**, which also audited the codebase for critical bugs and rewrote the Agent with a proper EventLog + SSE streaming system.

**v0.2 (this overhaul)** was a full architecture review by **Claude Sonnet 4**, which:
- Diagnosed 7 root-cause bugs (fake app launching, single-shot tool loop, broken Anthropic/Gemini tool calling, etc.)
- Rewrote the multi-turn ReAct agent loop from scratch
- Implemented the 4-strategy Windows app launcher
- Fixed all 4 LLM clients to use a unified `chat()` interface with proper tool calling
- Built the Rich terminal UI and interactive CLI REPL
- Added 10 new tools (web search, file ops, workflows, URL opening)
- Implemented SQLite persistent memory
- Added the named workflow engine

> Different models for different strengths: Gemini for rapid scaffolding, Claude Opus for deep architectural auditing and premium UI design, Claude Sonnet for systematic bug-fixing, interface unification, and feature expansion.

---

## 📄 License

This project is for educational and personal use. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <sub>Built with ☕, 🎵, and way too many terminal tabs by <a href="https://github.com/JaydonJP">@JaydonJP</a></sub>
  <br>
  <sub>Pair programmed with Gemini · Claude Opus 4 · Claude Sonnet 4</sub>
</p>
