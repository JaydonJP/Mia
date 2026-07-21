from .base import LLMProvider
import os
import base64

class GeminiClient(LLMProvider):
    def __init__(self, model="gemini-1.5-pro"):
        self.model = model
        from dotenv import load_dotenv
        secrets_path = os.path.expanduser("~/.mia/secrets.env")
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)
            
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Warning: GEMINI_API_KEY not found. Gemini mode will not work until a key is set.")
            self.client = None
        else:
            try:
                from google import genai
                self.client = genai.Client(api_key=api_key)
            except ImportError:
                print("Warning: google-genai package not installed.")
                self.client = None

    def generate(self, prompt, image_path=None, system_prompt=None, tools=None):
        if not self.client:
            return "Gemini client is not configured. Please set GEMINI_API_KEY or install 'google-genai' package."
            
        contents = []
        if image_path and os.path.exists(image_path):
            try:
                from PIL import Image
                img = Image.open(image_path)
                contents.append(img)
            except Exception as e:
                print(f"Failed to read image for Gemini: {e}")
                
        contents.append(prompt)
        
        # Tools translation placeholder
        config_kwargs = {}
        if system_prompt:
            config_kwargs["system_instruction"] = system_prompt
            
        try:
            from google.genai import types
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs) if config_kwargs else None
            )
            return response.text
        except Exception as e:
            return f"Gemini error: {e}"
