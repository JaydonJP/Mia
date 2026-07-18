class SessionMemory:
    def __init__(self, max_turns=10):
        self.history = []
        self.max_turns = max_turns
        
    def add_user(self, text):
        self.history.append({"role": "user", "content": text})
        self._trim()
        
    def add_assistant(self, text):
        self.history.append({"role": "assistant", "content": text})
        self._trim()
        
    def _trim(self):
        if len(self.history) > self.max_turns * 2:
            self.history = self.history[-self.max_turns * 2:]
            
    def get_context(self):
        if not self.history:
            return "No previous conversation."
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.history])
