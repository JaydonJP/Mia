import mss
import mss.tools
from PIL import Image
from pathlib import Path
import time

class ScreenCapture:
    def __init__(self):
        self.sct = mss.mss()
        
    def capture_active_monitor(self, save_path="logs/screenshot.jpg"):
        """Capture the screen and downscale it for the VLM."""
        # For simplicity, capture the primary monitor
        # In a real setup, we might want to find which monitor has the active window
        monitor = self.sct.monitors[1]
        
        sct_img = self.sct.grab(monitor)
        img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
        
        # Downscale to max 1280px wide to save VRAM and API costs
        max_width = 1280
        if img.width > max_width:
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path, "JPEG", quality=85)
        return save_path
