import os
import sounddevice as sd
import numpy as np
from pathlib import Path
try:
    from piper import PiperVoice
except ImportError:
    PiperVoice = None

class TextToSpeech:
    def __init__(self, voice_model_path="models/en_GB-alan-medium.onnx"):
        self.model_path = Path(voice_model_path)
        self.voice = None
        if PiperVoice:
            if not self.model_path.exists():
                print(f"Warning: TTS model not found at {self.model_path}. Text-only mode fallback.")
            else:
                self.voice = PiperVoice.load(str(self.model_path))
        else:
            print("Piper TTS not installed. Text-only mode fallback.")
            
    def speak(self, text):
        if not self.voice:
            print(f"Mia: {text}")
            return
            
        print(f"Mia: {text}")
        try:
            audio_stream = self.voice.synthesize_stream_raw(text)
            
            for chunk in audio_stream:
                audio_np = np.frombuffer(chunk, dtype=np.int16)
                sd.play(audio_np, samplerate=22050)
                sd.wait()
        except Exception as e:
            print(f"TTS Error: {e}")
