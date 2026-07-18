import threading
import pystray
from PIL import Image, ImageDraw
import keyboard
import time
import yaml
from pathlib import Path
import sys

class MiaApp:
    def __init__(self):
        self.running = True
        self.config = self.load_config()
        self.mode = self.config.get("llm", {}).get("mode", "local")
        
        # Initialize components
        try:
            from .core.agent import Agent
            from .voice.stt import SpeechToText
            from .voice.tts import TextToSpeech
            from .voice.wake_word import WakeWordDetector
            
            self.agent = Agent(self.config)
            self.agent.router.set_mode(self.mode)
            self.stt = SpeechToText()
            self.tts = TextToSpeech()
            self.wake_word = WakeWordDetector()
        except ImportError as e:
            print(f"Failed to import components: {e}")
            
        self.setup_hotkeys()
        
    def load_config(self):
        config_path = Path(__file__).parent.parent.parent / "config" / "mia.yaml"
        if config_path.exists():
            with open(config_path, "r") as f:
                return yaml.safe_load(f)
        return {}

    def setup_hotkeys(self):
        ptt_key = self.config.get("voice", {}).get("push_to_talk_key", "right ctrl")
        keyboard.on_press_key(ptt_key, self.on_ptt_press)
        keyboard.on_release_key(ptt_key, self.on_ptt_release)
        # Kill switch: Ctrl+Shift+Pause
        keyboard.add_hotkey("ctrl+shift+pause", self.kill_switch)
        print(f"Hotkeys registered. PTT: {ptt_key}, Kill switch: Ctrl+Shift+Pause")

    def on_ptt_press(self, event):
        print("Listening...")
        if hasattr(self, 'stt'):
            self.stt.start_recording()

    def on_ptt_release(self, event):
        print("Processing audio...")
        if hasattr(self, 'stt'):
            text = self.stt.stop_recording_and_transcribe()
            if text:
                print(f"User: {text}")
                threading.Thread(target=self.process_request, args=(text,), daemon=True).start()

    def process_request(self, text):
        if hasattr(self, 'agent'):
            self.agent.process(text, tts_engine=self.tts)

    def kill_switch(self):
        print("Kill switch activated! Stopping all actions.")
        self.running = False
        sys.exit(1)

    def create_tray_image(self, color):
        image = Image.new('RGB', (64, 64), 'black')
        d = ImageDraw.Draw(image)
        d.ellipse((16, 16, 48, 48), fill=color)
        return image

    def run_tray(self):
        self.icon = pystray.Icon("Mia")
        self.icon.icon = self.create_tray_image('green')
        self.icon.title = f"Mia ({self.mode})"
        self.icon.menu = pystray.Menu(
            pystray.MenuItem("Mode: Local", lambda: self.set_mode("local"), checked=lambda item: self.mode == "local"),
            pystray.MenuItem("Mode: Cloud", lambda: self.set_mode("cloud"), checked=lambda item: self.mode == "cloud"),
            pystray.MenuItem("Mode: Auto", lambda: self.set_mode("auto"), checked=lambda item: self.mode == "auto"),
            pystray.MenuItem("Exit", self.stop)
        )
        self.icon.run()

    def set_mode(self, new_mode):
        self.mode = new_mode
        if hasattr(self, 'agent'):
            self.agent.router.set_mode(new_mode)
        
        if hasattr(self, 'icon'):
            self.icon.title = f"Mia ({self.mode})"
            color = 'green' if new_mode == "local" else 'orange' if new_mode == "cloud" else 'blue'
            self.icon.icon = self.create_tray_image(color)
        print(f"Mode switched to {self.mode}")

    def stop(self, icon=None, item=None):
        self.running = False
        if hasattr(self, 'icon'):
            self.icon.stop()
        print("Mia JARVIS Assistant shutting down.")
        sys.exit(0)

    def run(self):
        tray_thread = threading.Thread(target=self.run_tray, daemon=True)
        tray_thread.start()
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
