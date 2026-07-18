from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def generate(self, prompt, image_path=None, system_prompt=None, tools=None):
        """
        Generate a response.
        :param prompt: User prompt
        :param image_path: Optional path to an image
        :param system_prompt: Optional system instructions
        :param tools: Optional list of tool definitions
        :return: string response or list of tool calls
        """
        pass
