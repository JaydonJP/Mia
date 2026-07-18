class ToolRegistry:
    def __init__(self):
        self.tools = {}
        self.schemas = []
        
    def register(self, name, description, parameters, func):
        self.tools[name] = func
        
        # OpenAI style schema
        self.schemas.append({
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": parameters.get("properties", {}),
                    "required": parameters.get("required", [])
                }
            }
        })
        
    def get_schemas(self):
        return self.schemas
        
    def execute(self, name, kwargs):
        print(f"Executing tool: {name} with args: {kwargs}")
        if name in self.tools:
            try:
                result = self.tools[name](**kwargs)
                return str(result)
            except Exception as e:
                return f"Error executing {name}: {e}"
        return f"Tool {name} not found."
