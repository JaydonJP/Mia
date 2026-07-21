"""
Mia JARVIS — FastAPI Backend Server
Provides REST + SSE endpoints for the dashboard UI.
"""
import asyncio
import json
import threading
import queue
import time
import yaml
import base64
import os
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Mia JARVIS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def load_config():
    config_path = Path(__file__).parent.parent.parent / "config" / "mia.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    return {}


# ---------------------------------------------------------------------------
# Lazy singleton — only initialized on first request, not at import time
# ---------------------------------------------------------------------------
class MiaBackend:
    _instance = None
    _lock = threading.Lock()
    
    @classmethod
    def get(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        self.config = load_config()
        self.mode = self.config.get("llm", {}).get("mode", "local")
        self.provider = self.config.get("llm", {}).get("cloud", {}).get("provider", "openai")
        self.ready = False
        self.error = None
        self.tts = None
        self.agent = None
        
        # SSE event queues — one per connected client
        self.sse_queues: list[queue.Queue] = []
        self._sse_lock = threading.Lock()
        
        # Initialize in background to not block server startup
        self._init_thread = threading.Thread(target=self._initialize, daemon=True)
        self._init_thread.start()
    
    def _initialize(self):
        try:
            from .core.agent import Agent
            self.agent = Agent(self.config)
            self.agent.router.set_mode(self.mode)
            
            # Subscribe to agent events and forward to SSE clients
            self.agent.event_log.subscribe(self._broadcast_event)
            
            # Try loading TTS (optional)
            try:
                from .voice.tts import TextToSpeech
                self.tts = TextToSpeech()
            except Exception:
                self.tts = None
            
            self.ready = True
            self._broadcast_event({
                "type": "system",
                "data": {"message": "Mia backend initialized successfully."},
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            self.error = str(e)
            self._broadcast_event({
                "type": "system",
                "data": {"message": f"Initialization error: {e}"},
                "timestamp": datetime.now().isoformat()
            })
    
    def _broadcast_event(self, event):
        with self._sse_lock:
            dead = []
            for q in self.sse_queues:
                try:
                    q.put_nowait(event)
                except queue.Full:
                    dead.append(q)
            for q in dead:
                self.sse_queues.remove(q)
    
    def create_sse_queue(self):
        q = queue.Queue(maxsize=100)
        with self._sse_lock:
            self.sse_queues.append(q)
        return q
    
    def remove_sse_queue(self, q):
        with self._sse_lock:
            if q in self.sse_queues:
                self.sse_queues.remove(q)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class ChatRequest(BaseModel):
    message: str

class ModeRequest(BaseModel):
    mode: str

class ProviderRequest(BaseModel):
    provider: str


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/state")
def get_state():
    backend = MiaBackend.get()
    return {
        "running": backend.ready,
        "mode": backend.mode,
        "provider": backend.provider,
        "error": backend.error,
        "agentState": backend.agent.state if backend.agent else "initializing",
        "hasTTS": backend.tts is not None,
    }


@app.post("/api/mode")
def set_mode(req: ModeRequest):
    backend = MiaBackend.get()
    if req.mode not in ("local", "cloud", "auto"):
        return {"status": "error", "message": "Invalid mode. Use local/cloud/auto."}
    backend.mode = req.mode
    if backend.agent:
        backend.agent.router.set_mode(req.mode)
    backend._broadcast_event({
        "type": "system",
        "data": {"message": f"Mode switched to {req.mode}"},
        "timestamp": datetime.now().isoformat()
    })
    return {"status": "ok", "mode": req.mode}


@app.post("/api/provider")
def set_provider(req: ProviderRequest):
    backend = MiaBackend.get()
    if req.provider not in ("openai", "anthropic", "gemini"):
        return {"status": "error", "message": "Invalid provider."}
    backend.provider = req.provider
    # Update config and re-init router's cloud client
    backend.config.setdefault("llm", {}).setdefault("cloud", {})["provider"] = req.provider
    if backend.agent:
        from .llm.router import LLMRouter
        backend.agent.router = LLMRouter(backend.config)
        backend.agent.router.set_mode(backend.mode)
    backend._broadcast_event({
        "type": "system",
        "data": {"message": f"Cloud provider changed to {req.provider}"},
        "timestamp": datetime.now().isoformat()
    })
    return {"status": "ok", "provider": req.provider}


@app.post("/api/chat")
def chat(req: ChatRequest):
    backend = MiaBackend.get()
    if not backend.ready or not backend.agent:
        return {"response": "Mia is still initializing. Please wait a moment."}
    
    # Run agent synchronously for now (the SSE stream gives real-time feedback)
    try:
        response = backend.agent.process(req.message, tts_engine=backend.tts)
        return {"response": response}
    except Exception as e:
        return {"response": f"Error processing request: {e}"}


@app.get("/api/history")
def get_history():
    backend = MiaBackend.get()
    if backend.agent:
        return {"history": backend.agent.memory.get_history_list()}
    return {"history": []}


@app.post("/api/history/clear")
def clear_history():
    backend = MiaBackend.get()
    if backend.agent:
        backend.agent.memory.clear()
    return {"status": "ok"}


@app.get("/api/screen")
def get_screen():
    backend = MiaBackend.get()
    if not backend.agent:
        return {"image": None}
    try:
        img_path = backend.agent.screen.capture_active_monitor()
        if img_path and os.path.exists(img_path):
            with open(img_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return {"image": f"data:image/jpeg;base64,{encoded}"}
    except Exception:
        pass
    return {"image": None}


@app.get("/api/events")
def get_recent_events():
    backend = MiaBackend.get()
    if backend.agent:
        return {"events": backend.agent.event_log.get_recent(50)}
    return {"events": []}


@app.get("/api/events/stream")
async def event_stream(request: Request):
    """Server-Sent Events endpoint for real-time activity feed."""
    backend = MiaBackend.get()
    q = backend.create_sse_queue()
    
    async def generate():
        try:
            # Send initial heartbeat
            yield f"data: {json.dumps({'type': 'connected', 'data': {'message': 'SSE connected'}, 'timestamp': datetime.now().isoformat()})}\n\n"
            
            while True:
                # Check if client disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    event = q.get(timeout=0.5)
                    yield f"data: {json.dumps(event)}\n\n"
                except queue.Empty:
                    # Send keepalive every 15 seconds
                    yield f": keepalive\n\n"
                    
        finally:
            backend.remove_sse_queue(q)
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def start_server():
    import uvicorn
    uvicorn.run("mia.server:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    start_server()
