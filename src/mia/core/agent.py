from .prompts import SYSTEM_PROMPT
from .memory import SessionMemory
from ..actions.executor import setup_executor
from ..llm.router import LLMRouter
from ..perception.screen import ScreenCapture
from ..perception.accessibility import AccessibilityTree
from ..privacy.redaction import Redactor
import json
import time
import threading
from collections import deque
from datetime import datetime


class EventLog:
    """Thread-safe event log for the UI to consume via SSE."""
    
    def __init__(self, max_events=200):
        self.events = deque(maxlen=max_events)
        self.listeners = []
        self._lock = threading.Lock()
    
    def emit(self, event_type, data):
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        with self._lock:
            self.events.append(event)
            for callback in self.listeners:
                try:
                    callback(event)
                except Exception:
                    pass
    
    def subscribe(self, callback):
        with self._lock:
            self.listeners.append(callback)
    
    def unsubscribe(self, callback):
        with self._lock:
            if callback in self.listeners:
                self.listeners.remove(callback)
    
    def get_recent(self, n=50):
        with self._lock:
            return list(self.events)[-n:]


class Agent:
    def __init__(self, config):
        self.memory = SessionMemory()
        self.executor = setup_executor()
        self.router = LLMRouter(config)
        self.screen = ScreenCapture()
        self.a11y = AccessibilityTree()
        self.redactor = Redactor()
        self.config = config
        self.event_log = EventLog()
        self.state = "idle"  # idle | listening | thinking | acting | speaking
        
    def _set_state(self, new_state):
        self.state = new_state
        self.event_log.emit("state_change", {"state": new_state})
        
    def process(self, user_text, tts_engine=None):
        """Process a user request. Returns Mia's final text response."""
        self._set_state("thinking")
        self.memory.add_user(user_text)
        self.event_log.emit("user_message", {"text": user_text})
        
        # 1. Gather context
        self.event_log.emit("activity", {"message": "Scanning active window..."})
        tree = self.a11y.get_active_window_tree()
        img_path = None
        
        if self.router.mode in ["cloud", "auto"]:
            self.event_log.emit("activity", {"message": "Capturing screen..."})
            img_path = self.screen.capture_active_monitor()
            
            # Redact if cloud
            if self.router.mode == "cloud":
                tree = self.redactor.redact_tree(tree)
                if self.redactor.is_sensitive(tree.get("title", "")):
                    self.event_log.emit("activity", {"message": "Sensitive app detected — skipping screen upload"})
                    img_path = None
                    
        tree_str = json.dumps(tree, indent=2)
        full_prompt = (
            f"Active Window Context:\n{tree_str}\n\n"
            f"Recent History:\n{self.memory.get_context()}\n\n"
            f"User Request: {user_text}"
        )
        
        # 2. Get LLM response
        provider_name = self.router.mode
        self.event_log.emit("activity", {"message": f"Sending to LLM ({provider_name})..."})
        
        response = self.router.generate(
            prompt=full_prompt, 
            image_path=img_path, 
            system_prompt=SYSTEM_PROMPT,
            tools=self.executor.get_schemas()
        )
        
        # 3. Handle response
        final_response = ""
        
        if isinstance(response, list):
            # Tool calls from OpenAI-like APIs
            self._set_state("acting")
            for tool_call in response:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                
                self.event_log.emit("tool_call", {
                    "tool": name, 
                    "args": args
                })
                
                result = self.executor.execute(name, args)
                
                self.event_log.emit("tool_result", {
                    "tool": name,
                    "result": str(result)[:500]
                })
                
                if name == "respond":
                    spoken_text = args.get("text", "")
                    final_response = spoken_text
                    self._set_state("speaking")
                    if tts_engine:
                        tts_engine.speak(spoken_text)
                    self.memory.add_assistant(spoken_text)
                    self.event_log.emit("mia_response", {"text": spoken_text})
                else:
                    # Post-action verification
                    time.sleep(0.8)
                    verification_img = self.screen.capture_active_monitor()
                    self.memory.add_system(f"Executed {name}({args}). Result: {str(result)[:200]}")
                    
            if not final_response:
                final_response = "Done."
                self.memory.add_assistant(final_response)
                self.event_log.emit("mia_response", {"text": final_response})
        else:
            # Plain text response (from Ollama local or fallback)
            final_response = str(response)
            self._set_state("speaking")
            if tts_engine:
                tts_engine.speak(final_response)
            self.memory.add_assistant(final_response)
            self.event_log.emit("mia_response", {"text": final_response})
        
        self._set_state("idle")
        return final_response
