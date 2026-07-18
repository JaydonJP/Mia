from .apps import launch_app, focus_window
from .input import type_text, hotkey, click_element
from .shell import run_powershell
from ..tools.registry import ToolRegistry
import time

def setup_executor():
    registry = ToolRegistry()
    
    registry.register(
        name="launch_app",
        description="Launch an application by name",
        parameters={
            "properties": {"name": {"type": "string", "description": "The name of the app to launch"}},
            "required": ["name"]
        },
        func=launch_app
    )
    
    registry.register(
        name="focus_window",
        description="Bring a window to the front",
        parameters={
            "properties": {"title": {"type": "string", "description": "Part of the window title"}},
            "required": ["title"]
        },
        func=focus_window
    )
    
    registry.register(
        name="type_text",
        description="Type text into the currently focused field",
        parameters={
            "properties": {"text": {"type": "string", "description": "The text to type"}},
            "required": ["text"]
        },
        func=type_text
    )
    
    registry.register(
        name="hotkey",
        description="Press a keyboard hotkey (e.g., 'ctrl+c', 'alt+tab')",
        parameters={
            "properties": {"keys": {"type": "string", "description": "The hotkey combination"}},
            "required": ["keys"]
        },
        func=hotkey
    )
    
    registry.register(
        name="click_element",
        description="Click a UI element by its name in the active window",
        parameters={
            "properties": {"name": {"type": "string", "description": "The exact name of the element"}},
            "required": ["name"]
        },
        func=click_element
    )
    
    registry.register(
        name="run_powershell",
        description="Run a safe powershell command",
        parameters={
            "properties": {"cmd": {"type": "string", "description": "The command to run"}},
            "required": ["cmd"]
        },
        func=run_powershell
    )
    
    registry.register(
        name="wait",
        description="Wait for a specified number of seconds",
        parameters={
            "properties": {"seconds": {"type": "number", "description": "Seconds to wait"}},
            "required": ["seconds"]
        },
        func=lambda seconds: time.sleep(seconds) or f"Waited {seconds} seconds."
    )
    
    return registry
