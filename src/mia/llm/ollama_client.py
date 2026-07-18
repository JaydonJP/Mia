from .base import LLMProvider
import ollama

class OllamaClient(LLMProvider):
    def __init__(self, model="qwen2.5vl:7b"):
        self.model = model
        
    def generate(self, prompt, image_path=None, system_prompt=None, tools=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        user_msg = {"role": "user", "content": prompt}
        
        if image_path:
            try:
                with open(image_path, "rb") as f:
                    img_data = f.read()
                user_msg["images"] = [img_data]
            except Exception as e:
                print(f"Failed to read image: {e}")
            
        messages.append(user_msg)
        
        try:
            # Note: qwen2.5 doesn't fully support OpenAI-style tool calling natively in Ollama yet
            # but we pass tools if available in case it's a model that supports it
            kwargs = {}
            if tools:
                # Basic mapping for tools (simplified)
                pass # Complex tool mapping omitted for basic Qwen fallback
                
            response = ollama.chat(model=self.model, messages=messages, **kwargs)
            return response['message']['content']
        except Exception as e:
            return f"Ollama error: {e}"
