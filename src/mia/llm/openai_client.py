from .base import LLMProvider
import os
import base64
from openai import OpenAI

class OpenAIClient(LLMProvider):
    def __init__(self, model="gpt-4o"):
        self.model = model
        # Try to load API key from secrets file if it exists
        from dotenv import load_dotenv
        secrets_path = os.path.expanduser("~/.mia/secrets.env")
        if os.path.exists(secrets_path):
            load_dotenv(secrets_path)
            
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate(self, prompt, image_path=None, system_prompt=None, tools=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
            
        content = [{"type": "text", "text": prompt}]
        
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{img_data}"}
                })
            except Exception as e:
                print(f"Failed to read image for OpenAI: {e}")

        messages.append({"role": "user", "content": content})
        
        kwargs = {
            "model": self.model,
            "messages": messages,
        }
        
        if tools:
            kwargs["tools"] = tools
            
        try:
            response = self.client.chat.completions.create(**kwargs)
            message = response.choices[0].message
            if message.tool_calls:
                return message.tool_calls
            return message.content
        except Exception as e:
            return f"OpenAI error: {e}"
