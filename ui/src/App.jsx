import { useState, useEffect, useRef, useCallback } from 'react'
import {
  Activity, Monitor, MessageSquare, Cpu, Cloud,
  Zap, Send, Mic, Terminal, Eye, Radio, Wrench, ChevronRight
} from 'lucide-react'
import './index.css'

const API_BASE = 'http://localhost:8000/api'

// ─── Activity Icon Map ───────────────────────────────────────────
function ActivityIcon({ type }) {
  const size = 13
  switch (type) {
    case 'tool_call': return <Wrench size={size} color="#8b5cf6" />
    case 'tool_result': return <ChevronRight size={size} color="#4a5a74" />
    case 'activity': return <Zap size={size} color="#f59e0b" />
    case 'state_change': return <Radio size={size} color="#3b82f6" />
    case 'user_message': return <MessageSquare size={size} color="#60a5fa" />
    case 'mia_response': return <MessageSquare size={size} color="#10b981" />
    case 'system': return <Terminal size={size} color="#60a5fa" />
    default: return <Activity size={size} color="#4a5a74" />
  }
}

function formatTime(iso) {
  if (!iso) return ''
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
  } catch {
    return ''
  }
}

function activityText(event) {
  const d = event.data || {}
  switch (event.type) {
    case 'tool_call': return `Tool: ${d.tool}(${JSON.stringify(d.args || {}).slice(0, 80)})`
    case 'tool_result': return `→ ${(d.result || '').slice(0, 120)}`
    case 'activity': return d.message || ''
    case 'state_change': return `State → ${d.state}`
    case 'user_message': return `You: ${d.text}`
    case 'mia_response': return `Mia: ${(d.text || '').slice(0, 100)}`
    case 'system': return d.message || ''
    case 'connected': return 'Connected to Mia backend'
    default: return JSON.stringify(d).slice(0, 100)
  }
}

// ─── Main App ─────────────────────────────────────────────────────
export default function App() {
  const [state, setState] = useState({
    running: false, mode: 'local', provider: 'openai',
    agentState: 'idle', error: null, hasTTS: false
  })
  const [activityLog, setActivityLog] = useState([])
  const [chatLog, setChatLog] = useState([])
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [screenImg, setScreenImg] = useState(null)

  const chatEndRef = useRef(null)
  const activityEndRef = useRef(null)
  const sseRef = useRef(null)

  // ── Poll state ──────────────────────────────────────────────────
  useEffect(() => {
    const fetchState = async () => {
      try {
        const res = await fetch(`${API_BASE}/state`)
        if (res.ok) {
          const data = await res.json()
          setState(data)
        }
      } catch { /* offline */ }
    }

    fetchState()
    const interval = setInterval(fetchState, 2500)
    return () => clearInterval(interval)
  }, [])

  // ── SSE stream ──────────────────────────────────────────────────
  useEffect(() => {
    let es = null
    let retryTimeout = null

    function connect() {
      es = new EventSource(`${API_BASE}/events/stream`)
      sseRef.current = es

      es.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data)
          setActivityLog(prev => [...prev.slice(-150), event])

          // Update agent state from SSE
          if (event.type === 'state_change' && event.data?.state) {
            setState(prev => ({ ...prev, agentState: event.data.state }))
          }
        } catch { /* ignore parse errors */ }
      }

      es.onerror = () => {
        es.close()
        // Retry after 3s
        retryTimeout = setTimeout(connect, 3000)
      }
    }

    connect()
    return () => {
      if (es) es.close()
      if (retryTimeout) clearTimeout(retryTimeout)
    }
  }, [])

  // ── Poll screen (low frequency) ────────────────────────────────
  useEffect(() => {
    const fetchScreen = async () => {
      try {
        const res = await fetch(`${API_BASE}/screen`)
        if (res.ok) {
          const data = await res.json()
          if (data.image) setScreenImg(data.image)
        }
      } catch { /* ignore */ }
    }

    fetchScreen()
    const interval = setInterval(fetchScreen, 5000)
    return () => clearInterval(interval)
  }, [])

  // ── Load history on mount ──────────────────────────────────────
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${API_BASE}/history`)
        if (res.ok) {
          const data = await res.json()
          if (data.history?.length) {
            setChatLog(data.history.filter(m => m.role !== 'system').map(m => ({
              role: m.role === 'user' ? 'user' : 'mia',
              content: m.content
            })))
          }
        }
      } catch { /* offline */ }
    }
    fetchHistory()
  }, [])

  // ── Auto-scroll ─────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatLog, isProcessing])

  useEffect(() => {
    activityEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [activityLog])

  // ── Handlers ────────────────────────────────────────────────────
  const handleModeChange = async (newMode) => {
    try {
      await fetch(`${API_BASE}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      })
      setState(prev => ({ ...prev, mode: newMode }))
    } catch { /* ignore */ }
  }

  const handleProviderChange = async (e) => {
    const newProvider = e.target.value
    try {
      await fetch(`${API_BASE}/provider`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: newProvider })
      })
      setState(prev => ({ ...prev, provider: newProvider }))
    } catch { /* ignore */ }
  }

  const handleChat = async (e) => {
    e.preventDefault()
    const msg = input.trim()
    if (!msg || isProcessing) return

    setInput('')
    setChatLog(prev => [...prev, { role: 'user', content: msg }])
    setIsProcessing(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: msg })
      })
      const data = await res.json()
      setChatLog(prev => [...prev, { role: 'mia', content: data.response }])
    } catch {
      setChatLog(prev => [...prev, { role: 'mia', content: 'Could not reach Mia backend. Is the server running?' }])
    } finally {
      setIsProcessing(false)
    }
  }

  const agentState = state.agentState || 'idle'

  return (
    <div className="app-container">
      {/* Background effects */}
      <div className="bg-effects">
        <div className="bg-glow-1"></div>
        <div className="bg-glow-2"></div>
        <div className="bg-grid"></div>
      </div>

      {/* ───── HEADER ───── */}
      <header className="glass header">
        <div className="header-left">
          <div className="mia-logo">
            <div className="logo-core">
              <div className="logo-ring"></div>
              <div className="logo-dot"></div>
            </div>
            <div>
              <div className="logo-text">MIA</div>
              <div className="logo-subtitle">Personal Assistant</div>
            </div>
          </div>

          <div className={`connection-badge ${state.running ? 'online' : 'offline'}`}>
            <span className="connection-dot"></span>
            {state.running ? 'Online' : 'Offline'}
          </div>
        </div>

        <div className="header-controls">
          <div className="mode-switcher">
            {['local', 'cloud', 'auto'].map(mode => (
              <button
                key={mode}
                className={`mode-btn ${state.mode === mode ? `active ${mode}` : ''}`}
                onClick={() => handleModeChange(mode)}
              >
                {mode === 'local' && <Cpu size={13} />}
                {mode === 'cloud' && <Cloud size={13} />}
                {mode === 'auto' && <Zap size={13} />}
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>

          <select
            className="provider-select"
            value={state.provider}
            onChange={handleProviderChange}
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
            <option value="gemini">Gemini</option>
          </select>
        </div>
      </header>

      {/* ───── DASHBOARD ───── */}
      <main className="dashboard">
        {/* ── LEFT SIDEBAR ── */}
        <div className="sidebar">
          {/* Mia Core Visualizer */}
          <div className="glass core-panel">
            <div className="core-visualizer" data-state={agentState}>
              <div className="core-outer-ring"></div>
              <div className="core-mid-ring"></div>
              <div className="core-inner-ring"></div>
              <div className="core-center">
                <div className="core-center-dot"></div>
              </div>
            </div>
            <div className="core-state-label" data-state={agentState}>
              {agentState === 'idle' && '● Ready'}
              {agentState === 'thinking' && '◉ Thinking'}
              {agentState === 'acting' && '◈ Executing'}
              {agentState === 'speaking' && '◉ Speaking'}
              {agentState === 'listening' && '◉ Listening'}
              {agentState === 'initializing' && '○ Initializing'}
            </div>
          </div>

          {/* Activity Feed */}
          <div className="glass activity-panel">
            <div className="panel-header">
              <Activity size={14} /> Activity Log
            </div>
            <div className="activity-feed">
              {activityLog.length === 0 && (
                <div className="activity-item">
                  <span className="activity-text" style={{ opacity: 0.4, fontStyle: 'italic' }}>
                    Waiting for events...
                  </span>
                </div>
              )}
              {activityLog.map((event, i) => (
                <div key={i} className={`activity-item ${event.type || ''}`}>
                  <span className="activity-time">{formatTime(event.timestamp)}</span>
                  <span className="activity-icon"><ActivityIcon type={event.type} /></span>
                  <span className="activity-text">{activityText(event)}</span>
                </div>
              ))}
              <div ref={activityEndRef} />
            </div>
          </div>

          {/* Screen Preview */}
          <div className="glass screen-panel">
            <div className="panel-header">
              <Eye size={14} /> Screen Context
            </div>
            <div className="screen-preview-container">
              {screenImg ? (
                <img src={screenImg} alt="Active Screen" />
              ) : (
                <div className="screen-placeholder">
                  <Monitor size={24} />
                  <span>No screen feed</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── MAIN CHAT PANEL ── */}
        <div className="glass chat-panel">
          <div className="panel-header">
            <MessageSquare size={14} /> Mia
          </div>

          <div className="chat-history">
            {chatLog.length === 0 && !isProcessing && (
              <div className="chat-empty">
                <div className="chat-empty-icon">
                  <Mic size={28} color="var(--accent)" />
                </div>
                <h3>Hello, I'm Mia</h3>
                <p>
                  Your personal AI assistant. Use voice with{' '}
                  <span className="shortcut-hint">Right Ctrl</span>{' '}
                  or type a command below.
                </p>
              </div>
            )}

            {chatLog.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                <div className="chat-avatar">
                  {msg.role === 'mia' ? 'M' : 'U'}
                </div>
                <div className="chat-content">{msg.content}</div>
              </div>
            ))}

            {isProcessing && (
              <div className="chat-bubble mia">
                <div className="chat-avatar">M</div>
                <div className="chat-content typing-indicator">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-area">
            <form className="chat-input-form" onSubmit={handleChat}>
              <input
                type="text"
                placeholder="Ask Mia anything..."
                value={input}
                onChange={e => setInput(e.target.value)}
                disabled={isProcessing}
              />
              <button
                type="submit"
                className="send-btn"
                disabled={isProcessing || !input.trim()}
              >
                <Send size={16} />
              </button>
            </form>
            <div className="chat-input-hint">
              <Mic size={11} /> Voice: hold <span className="shortcut-hint">Right Ctrl</span>
              &nbsp;·&nbsp;
              Kill switch: <span className="shortcut-hint">Ctrl+Shift+Pause</span>
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
