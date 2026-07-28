import sys
from pathlib import Path
sys.path.insert(0, "C:\\OblivionX\\Projects\\Personal\\Mia\\src")

from mia.core.agent import Agent
from mia.llm.base import LLMResponse, ToolCall
import json
import uuid

class MockRouter:
    def __init__(self):
        self.step = 0
        self.mode = "local"
    def get_model_name(self): return "Mock"
    
    def chat(self, messages, tools=None):
        self.step += 1
        if self.step == 1:
            # First turn: returns tool call to respond AND launch_app
            tc1 = ToolCall(id="1", name="respond", arguments={"text": "Opening Spotify now."})
            tc2 = ToolCall(id="2", name="launch_app", arguments={"name": "spotify"})
            return LLMResponse(tool_calls=[tc1, tc2], text=None, raw={})
        else:
            # Second turn: throws connection error
            return LLMResponse(text="[Ollama error] Failed to connect to Ollama...")

agent = Agent({})
agent.router = MockRouter()
agent.executor.execute = lambda name, args: "Success"

response = agent.process("Can you open spotify for me?")
print("RETURNED RESPONSE:")
print(repr(response))
