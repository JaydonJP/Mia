import fastapi
from fastapi import FastAPI, WebSocket, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import threading
import time
import yaml
from pathlib import Path
import json
import base64
import os

from .core.agent import Agent

app = FastAPI(title="Mia Core API")

# Allow CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production limit to localhost:5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MiaServer:
    def __init__(self):
        self.config = self.load_config()
        self.agent = Agent(self.config)
        self.mode = self.config.get("llm", {}).get("mode", "local")
        self.agent.router.set_mode(self.mode)
        
        # We can still init TTS and STT if we want backend voice
        try:
            from .voice.tts import TextToSpeech
            self.tts = TextToSpeech()
        except ImportError:
            self.tts = None
            
        self.running = True

    def load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "mia.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

mia_instance = MiaServer()

class ChatRequest(BaseModel):
    message: str

@app.get("/api/state")
def get_state():
    return {
        "mode": mia_instance.mode,
        "running": mia_instance.running
    }

@app.post("/api/mode")
def set_mode(payload: dict):
    new_mode = payload.get("mode")
    if new_mode in ["local", "cloud", "auto"]:
        mia_instance.mode = new_mode
        mia_instance.agent.router.set_mode(new_mode)
        return {"status": "success", "mode": new_mode}
    return {"status": "error", "message": "Invalid mode"}

@app.post("/api/chat")
def chat(req: ChatRequest):
    response = mia_instance.agent.process(req.message, tts_engine=mia_instance.tts)
    return {"response": response}

@app.get("/api/screen")
def get_screen():
    # Capture screen and return as base64 for dashboard
    img_path = mia_instance.agent.screen.capture_active_monitor()
    if img_path and os.path.exists(img_path):
        with open(img_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return {"image": f"data:image/png;base64,{encoded}"}
    return {"image": None}

def start_server():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    start_server()
