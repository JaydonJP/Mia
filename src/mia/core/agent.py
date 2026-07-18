from .prompts import SYSTEM_PROMPT
from .memory import SessionMemory
from ..actions.executor import setup_executor
from ..llm.router import LLMRouter
from ..perception.screen import ScreenCapture
from ..perception.accessibility import AccessibilityTree
from ..privacy.redaction import Redactor
import json

class Agent:
    def __init__(self, config):
        self.memory = SessionMemory()
        self.executor = setup_executor()
        self.router = LLMRouter(config)
        self.screen = ScreenCapture()
        self.a11y = AccessibilityTree()
        self.redactor = Redactor()
        self.config = config
        
    def process(self, user_text, tts_engine=None):
        self.memory.add_user(user_text)
        
        # 1. Gather context
        tree = self.a11y.get_active_window_tree()
        img_path = None
        
        if self.router.mode in ["cloud", "auto"]:
            # Capture screen
            img_path = self.screen.capture_active_monitor()
            
            # Redact if cloud
            if self.router.mode == "cloud":
                tree = self.redactor.redact_tree(tree)
                if self.redactor.is_sensitive(tree.get("title", "")):
                    print("Sensitive app detected, skipping image upload.")
                    img_path = None
                    
        tree_str = json.dumps(tree, indent=2)
        full_prompt = f"Active Window Context:\n{tree_str}\n\nRecent History:\n{self.memory.get_context()}\n\nUser Request: {user_text}"
        
        # 2. Get LLM response
        print("Sending request to LLM...")
        response = self.router.generate(
            prompt=full_prompt, 
            image_path=img_path, 
            system_prompt=SYSTEM_PROMPT,
            tools=self.executor.get_schemas()
        )
        
        # 3. Handle tools or direct text
        if isinstance(response, list): # Tool calls from OpenAI-like APIs
            for tool_call in response:
                name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)
                result = self.executor.execute(name, args)
                print(f"Tool {name} result: {result}")
                
                if name == "respond" and tts_engine:
                    tts_engine.speak(args.get("text", ""))
                    self.memory.add_assistant(args.get("text", ""))
            return "Action executed."
        else:
            if tts_engine:
                tts_engine.speak(response)
            self.memory.add_assistant(response)
            return response
