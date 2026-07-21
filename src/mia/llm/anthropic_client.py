from .base import LLMProvider
import os
import base64

class AnthropicClient(LLMProvider):
    def __init__(self, model="claude-3-5-sonnet-20240620"):
        self.model = model
        from dotenv import load_dotenv
        secrets_path = os.path.expanduser("~/.mia/secrets.env")
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)
            
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not found. Anthropic mode will not work until a key is set.")
            self.client = None
        else:
            try:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=api_key)
            except ImportError:
                print("Warning: anthropic package not installed.")
                self.client = None

    def generate(self, prompt, image_path=None, system_prompt=None, tools=None):
        if not self.client:
            return "Anthropic client is not configured. Please set ANTHROPIC_API_KEY or install 'anthropic' package."
            
        messages = []
        content = []
        
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": img_data
                    }
                })
            except Exception as e:
                print(f"Failed to read image for Anthropic: {e}")
                
        content.append({"type": "text", "text": prompt})
        messages.append({"role": "user", "content": content})
        
        kwargs = {
            "model": self.model,
            "max_tokens": 1024,
            "messages": messages,
        }
        if system_prompt:
            kwargs["system"] = system_prompt
            
        # Tool formatting for anthropic is slightly different from OpenAI but 
        # assume tools follow a compatible schema for now or will be adapted
        if tools:
            # Simple conversion placeholder
            # kwargs["tools"] = tools
            pass 
            
        try:
            response = self.client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"Anthropic error: {e}"
