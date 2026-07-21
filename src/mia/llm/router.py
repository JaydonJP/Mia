from .ollama_client import OllamaClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .gemini_client import GeminiClient

class LLMRouter:
    def __init__(self, config):
        self.config = config.get("llm", {})
        self.mode = self.config.get("mode", "local")
        
        # Initialize clients
        local_cfg = self.config.get("local", {})
        cloud_cfg = self.config.get("cloud", {})
        
        self.local_client = OllamaClient(model=local_cfg.get("vision_model", "qwen2.5vl:7b"))
        self.cloud_client = None
        
        provider = cloud_cfg.get("provider", "openai")
        if provider == "openai":
            self.cloud_client = OpenAIClient(model=cloud_cfg.get("model", "gpt-4o"))
        elif provider == "anthropic":
            self.cloud_client = AnthropicClient(model=cloud_cfg.get("model", "claude-3-5-sonnet-20240620"))
        elif provider == "gemini":
            self.cloud_client = GeminiClient(model=cloud_cfg.get("model", "gemini-1.5-pro"))
            
    def set_mode(self, mode):
        self.mode = mode
        
    def generate(self, prompt, image_path=None, system_prompt=None, tools=None):
        if self.mode == "cloud" and self.cloud_client:
            print(f"Routing to Cloud ({self.cloud_client.__class__.__name__})")
            return self.cloud_client.generate(prompt, image_path, system_prompt, tools)
        elif self.mode == "auto":
            # Very basic heuristic: if image is needed or tools are heavily used, use cloud
            if image_path or tools:
                print(f"Auto-routing to Cloud ({self.cloud_client.__class__.__name__ if self.cloud_client else 'None'})")
                if self.cloud_client:
                    return self.cloud_client.generate(prompt, image_path, system_prompt, tools)
            print("Auto-routing to Local (simple)")
            return self.local_client.generate(prompt, image_path, system_prompt, tools)
        else:
            print("Routing to Local (Ollama)")
            return self.local_client.generate(prompt, image_path, system_prompt, tools)
