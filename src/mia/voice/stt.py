import sys
import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
import queue
import threading

class SpeechToText:
    def __init__(self, model_size="small"):
        print(f"Loading faster-whisper {model_size} model...")
        try:
            self.model = WhisperModel(model_size, device="cuda", compute_type="float16")
        except Exception as e:
            print(f"CUDA not available for whisper, falling back to CPU... ({e})")
            self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
            
        self.q = queue.Queue()
        self.recording = False
        self.samplerate = 16000
        self.stream = None

    def start_recording(self):
        self.recording = True
        self.q.queue.clear()
        try:
            self.stream = sd.InputStream(samplerate=self.samplerate, channels=1, 
                                         dtype='float32', callback=self.audio_callback)
            self.stream.start()
        except Exception as e:
            print(f"Error starting microphone stream: {e}")

    def audio_callback(self, indata, frames, time, status):
        if status:
            print(status, file=sys.stderr)
        if self.recording:
            self.q.put(indata.copy())

    def stop_recording_and_transcribe(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
            
        audio_data = []
        while not self.q.empty():
            audio_data.append(self.q.get())
            
        if not audio_data:
            return ""
            
        audio_np = np.concatenate(audio_data, axis=0).flatten()
        
        # Transcribe
        segments, info = self.model.transcribe(audio_np, beam_size=5)
        text = "".join([segment.text for segment in segments])
        return text.strip()
