"""
Tool executor — registers all Mia tools and provides the unified interface
used by the agent loop.

This is the single source of truth for every tool Mia can call.
"""

from __future__ import annotations

import time
from ..tools.registry import ToolRegistry

# Import action modules
from .apps import launch_app, open_url, focus_window
from .input import type_text, hotkey, click_element
from .shell import run_powershell
from .web import web_search, read_webpage
from .files import list_directory, read_file, write_file, create_directory
from .workflows import activate_workflow, list_workflows


def setup_executor() -> ToolRegistry:
    """Create and return a ToolRegistry with all Mia tools registered."""
    registry = ToolRegistry()

    # ==================================================================
    # App & Window management
    # ==================================================================
    registry.register(
        name="launch_app",
        description="Launch an application by name (e.g., 'notepad', 'chrome', 'spotify', 'vscode', 'discord')",
        parameters={
            "properties": {
                "name": {"type": "string", "description": "The name of the app to launch"},
            },
            "required": ["name"],
        },
        func=launch_app,
    )

    registry.register(
        name="open_url",
        description="Open a URL in the default web browser",
        parameters={
            "properties": {
                "url": {"type": "string", "description": "The URL to open (e.g. 'https://google.com')"},
            },
            "required": ["url"],
        },
        func=open_url,
    )

    registry.register(
        name="focus_window",
        description="Bring a window to the front by partial title match",
        parameters={
            "properties": {
                "title": {"type": "string", "description": "Part of the window title to search for"},
            },
            "required": ["title"],
        },
        func=focus_window,
    )

    # ==================================================================
    # Keyboard & UI interaction
    # ==================================================================
    registry.register(
        name="type_text",
        description="Type text into the currently focused input field",
        parameters={
            "properties": {
                "text": {"type": "string", "description": "The text to type"},
            },
            "required": ["text"],
        },
        func=type_text,
    )

    registry.register(
        name="hotkey",
        description="Press a keyboard shortcut (e.g. 'ctrl+c', 'alt+tab', 'win+e', 'ctrl+shift+n')",
        parameters={
            "properties": {
                "keys": {"type": "string", "description": "The hotkey combination"},
            },
            "required": ["keys"],
        },
        func=hotkey,
    )

    registry.register(
        name="click_element",
        description="Click a UI element by its exact name in the active window's accessibility tree",
        parameters={
            "properties": {
                "name": {"type": "string", "description": "The exact name of the UI element to click"},
            },
            "required": ["name"],
        },
        func=click_element,
    )

    # ==================================================================
    # Shell / PowerShell
    # ==================================================================
    registry.register(
        name="run_powershell",
        description="Run a safe PowerShell command. Allowed: dir, ls, Get-ChildItem, Get-Date, Get-Process, echo, ping, ipconfig, Test-Path, New-Item, Copy-Item, etc. Destructive commands are blocked.",
        parameters={
            "properties": {
                "cmd": {"type": "string", "description": "The PowerShell command to run"},
            },
            "required": ["cmd"],
        },
        func=run_powershell,
    )

    # ==================================================================
    # Web search & reading
    # ==================================================================
    registry.register(
        name="web_search",
        description="Search the web for information. Returns top results with titles, URLs, and snippets.",
        parameters={
            "properties": {
                "query": {"type": "string", "description": "The search query"},
            },
            "required": ["query"],
        },
        func=web_search,
    )

    registry.register(
        name="read_webpage",
        description="Fetch a URL and extract the main text content from the page",
        parameters={
            "properties": {
                "url": {"type": "string", "description": "The URL to read"},
            },
            "required": ["url"],
        },
        func=read_webpage,
    )

    # ==================================================================
    # File system
    # ==================================================================
    registry.register(
        name="list_directory",
        description="List files and folders in a directory",
        parameters={
            "properties": {
                "path": {"type": "string", "description": "The directory path to list"},
            },
            "required": ["path"],
        },
        func=list_directory,
    )

    registry.register(
        name="read_file",
        description="Read the contents of a text file",
        parameters={
            "properties": {
                "path": {"type": "string", "description": "The file path to read"},
            },
            "required": ["path"],
        },
        func=read_file,
    )

    registry.register(
        name="write_file",
        description="Write content to a file (creates it if it doesn't exist)",
        parameters={
            "properties": {
                "path": {"type": "string", "description": "The file path to write to"},
                "content": {"type": "string", "description": "The content to write"},
            },
            "required": ["path", "content"],
        },
        func=write_file,
    )

    registry.register(
        name="create_directory",
        description="Create a new directory (including parent directories)",
        parameters={
            "properties": {
                "path": {"type": "string", "description": "The directory path to create"},
            },
            "required": ["path"],
        },
        func=create_directory,
    )

    # ==================================================================
    # Workflows
    # ==================================================================
    registry.register(
        name="activate_workflow",
        description="Activate a named workflow (e.g. 'study_mode', 'work_mode'). This launches a predefined set of apps and URLs.",
        parameters={
            "properties": {
                "name": {"type": "string", "description": "The workflow name to activate"},
            },
            "required": ["name"],
        },
        func=activate_workflow,
    )

    registry.register(
        name="list_workflows",
        description="List all available workflow automations",
        parameters={
            "properties": {},
            "required": [],
        },
        func=list_workflows,
    )

    # ==================================================================
    # Utility
    # ==================================================================
    registry.register(
        name="wait",
        description="Wait for a specified number of seconds before the next action (max 30)",
        parameters={
            "properties": {
                "seconds": {"type": "number", "description": "Seconds to wait (max 30)"},
            },
            "required": ["seconds"],
        },
        func=lambda seconds: time.sleep(min(float(seconds), 30)) or f"Waited {seconds} seconds.",
    )

    # ==================================================================
    # Respond — how Mia speaks to the user
    # ==================================================================
    registry.register(
        name="respond",
        description="Speak a response to the user. Use this for ALL verbal replies, answers, and confirmations.",
        parameters={
            "properties": {
                "text": {"type": "string", "description": "The text to speak to the user"},
            },
            "required": ["text"],
        },
        func=lambda text: text,  # Agent handles TTS/display
    )

    return registry
