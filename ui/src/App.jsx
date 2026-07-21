import { useState, useEffect, useRef } from 'react'
import { Activity, Mic, Settings, Monitor, MessageSquare, Cpu, Cloud, Settings2 } from 'lucide-react'
import './index.css'

function App() {
  const [state, setState] = useState({ mode: 'local', running: false })
  const [screenImg, setScreenImg] = useState(null)
  const [chatLog, setChatLog] = useState([])
  const [input, setInput] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const chatEndRef = useRef(null)

  const API_BASE = 'http://localhost:8000/api'

  useEffect(() => {
    // Poll state
    const fetchState = async () => {
      try {
        const res = await fetch(`${API_BASE}/state`)
        const data = await res.json()
        setState(data)
      } catch (e) {
        // console.error("API not reachable", e)
      }
    }
    
    // Poll screen
    const fetchScreen = async () => {
      try {
        const res = await fetch(`${API_BASE}/screen`)
        const data = await res.json()
        if (data.image) setScreenImg(data.image)
      } catch (e) {
        // ignore
      }
    }

    fetchState()
    const intervalState = setInterval(fetchState, 2000)
    const intervalScreen = setInterval(fetchScreen, 3000) // Lower frequency for screen

    return () => {
      clearInterval(intervalState)
      clearInterval(intervalScreen)
    }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatLog])

  const handleModeChange = async (newMode) => {
    try {
      await fetch(`${API_BASE}/mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: newMode })
      })
      setState(prev => ({ ...prev, mode: newMode }))
    } catch(e) {}
  }

  const handleChat = async (e) => {
    e.preventDefault()
    if (!input.trim()) return

    const userMsg = input
    setInput('')
    setChatLog(prev => [...prev, { role: 'user', content: userMsg }])
    setIsProcessing(true)

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMsg })
      })
      const data = await res.json()
      setChatLog(prev => [...prev, { role: 'mia', content: data.response }])
    } catch(e) {
      setChatLog(prev => [...prev, { role: 'mia', content: 'Error communicating with Mia Backend.' }])
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="app-container">
      {/* Background Gradient */}
      <div className="bg-glow"></div>

      <header className="glass-panel header">
        <div className="logo-container">
          <div className={`status-indicator ${state.running ? 'online' : 'offline'}`}></div>
          <h1>Mia JARVIS Assistant</h1>
        </div>
        
        <div className="mode-toggle">
          <button 
            className={`mode-btn ${state.mode === 'local' ? 'active local' : ''}`}
            onClick={() => handleModeChange('local')}
          >
            <Cpu size={16} /> Local
          </button>
          <button 
            className={`mode-btn ${state.mode === 'cloud' ? 'active cloud' : ''}`}
            onClick={() => handleModeChange('cloud')}
          >
            <Cloud size={16} /> Cloud
          </button>
          <button 
            className={`mode-btn ${state.mode === 'auto' ? 'active auto' : ''}`}
            onClick={() => handleModeChange('auto')}
          >
            <Settings2 size={16} /> Auto
          </button>
        </div>
      </header>

      <main className="dashboard">
        {/* Left Column: Screen & Status */}
        <div className="left-panel">
          <div className="glass-panel monitor-panel">
            <h2><Monitor size={18} /> Active Context</h2>
            <div className="screen-preview">
              {screenImg ? (
                <img src={screenImg} alt="Active Screen" />
              ) : (
                <div className="placeholder">
                  <Activity className="animate-pulse" size={32} />
                  <p>Awaiting screen feed...</p>
                </div>
              )}
            </div>
          </div>
          
          <div className="glass-panel status-panel">
            <h2><Activity size={18} /> System Status</h2>
            <ul className="status-list">
              <li>
                <span>Backend Connection</span>
                <span className={`badge ${state.running ? 'success' : 'error'}`}>
                  {state.running ? 'Connected' : 'Disconnected'}
                </span>
              </li>
              <li>
                <span>Active Mode</span>
                <span className="badge info">{state.mode.toUpperCase()}</span>
              </li>
              <li>
                <span>Voice Listening</span>
                <span className="badge warning">Push-to-Talk (Right Ctrl)</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Right Column: Interaction/Chat */}
        <div className="glass-panel chat-panel">
          <h2><MessageSquare size={18} /> Interaction Log</h2>
          <div className="chat-history">
            {chatLog.length === 0 && (
              <div className="empty-chat">
                Mia is ready. Speak using hotkeys or type below.
              </div>
            )}
            {chatLog.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}`}>
                <div className="chat-avatar">{msg.role === 'mia' ? 'M' : 'U'}</div>
                <div className="chat-content">{msg.content}</div>
              </div>
            ))}
            {isProcessing && (
              <div className="chat-bubble mia processing">
                <div className="chat-avatar">M</div>
                <div className="chat-content">
                  <span className="dot"></span>
                  <span className="dot"></span>
                  <span className="dot"></span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>
          <form className="chat-input-form" onSubmit={handleChat}>
            <input 
              type="text" 
              placeholder="Type a command to Mia (or use voice)..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={isProcessing}
            />
            <button type="submit" disabled={isProcessing || !input.trim()}>Send</button>
          </form>
        </div>
      </main>
    </div>
  )
}

export default App
