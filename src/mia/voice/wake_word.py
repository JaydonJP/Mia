class WakeWordDetector:
    def __init__(self, model_path="models/hey_mia.onnx"):
        self.model_path = model_path
        self.running = False
        
    def start(self, callback):
        self.running = True
        print("Wake word detector started (mock mode). Waiting for 'Hey Mia'...")
        # In a real implementation, this would read from the mic and run openWakeWord
        # If wake word is detected, it calls callback()

    def stop(self):
        self.running = False
