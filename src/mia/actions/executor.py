from .apps import launch_app, focus_window
from .input import type_text, hotkey, click_element
from .shell import run_powershell
from ..tools.registry import ToolRegistry
import time

def setup_executor():
    registry = ToolRegistry()
    
    registry.register(
        name="launch_app",
        description="Launch an application by name (e.g. 'notepad', 'chrome', 'spotify')",
        parameters={
            "properties": {"name": {"type": "string", "description": "The name of the app to launch"}},
            "required": ["name"]
        },
        func=launch_app
    )
    
    registry.register(
        name="focus_window",
        description="Bring a window to the front by partial title match",
        parameters={
            "properties": {"title": {"type": "string", "description": "Part of the window title to search for"}},
            "required": ["title"]
        },
        func=focus_window
    )
    
    registry.register(
        name="type_text",
        description="Type text into the currently focused input field",
        parameters={
            "properties": {"text": {"type": "string", "description": "The text to type"}},
            "required": ["text"]
        },
        func=type_text
    )
    
    registry.register(
        name="hotkey",
        description="Press a keyboard hotkey combination (e.g., 'ctrl+c', 'alt+tab', 'win+e')",
        parameters={
            "properties": {"keys": {"type": "string", "description": "The hotkey combination"}},
            "required": ["keys"]
        },
        func=hotkey
    )
    
    registry.register(
        name="click_element",
        description="Click a UI element by its exact name in the active window's accessibility tree",
        parameters={
            "properties": {"name": {"type": "string", "description": "The exact name of the UI element"}},
            "required": ["name"]
        },
        func=click_element
    )
    
    registry.register(
        name="run_powershell",
        description="Run a safe PowerShell command. Only whitelisted commands are allowed: dir, ls, echo, Get-Process, Get-Date, ping, ipconfig",
        parameters={
            "properties": {"cmd": {"type": "string", "description": "The PowerShell command to run"}},
            "required": ["cmd"]
        },
        func=run_powershell
    )
    
    registry.register(
        name="wait",
        description="Wait for a specified number of seconds before the next action",
        parameters={
            "properties": {"seconds": {"type": "number", "description": "Seconds to wait (max 30)"}},
            "required": ["seconds"]
        },
        func=lambda seconds: time.sleep(min(seconds, 30)) or f"Waited {seconds} seconds."
    )
    
    # The respond tool — this is how Mia speaks back to the user.
    # The actual TTS playback is handled by the agent, not here.
    registry.register(
        name="respond",
        description="Speak a response to the user. Use this whenever you want to communicate verbally.",
        parameters={
            "properties": {"text": {"type": "string", "description": "The text to speak to the user"}},
            "required": ["text"]
        },
        func=lambda text: text  # Just returns the text; agent handles TTS
    )
    
    return registry
