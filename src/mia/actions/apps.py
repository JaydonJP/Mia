"""
App launcher & window management for Windows.

Multi-strategy approach to reliably launch applications:
1. Known app registry (common apps → shell commands / exe paths)
2. Start Menu shortcut search (.lnk files)
3. PATH lookup via `where`
4. Fallback to `cmd /c start`
5. Post-launch verification
"""

from __future__ import annotations

import os
import re
import glob
import shutil
import subprocess
import time
import webbrowser

# ------------------------------------------------------------------
# Known app registry — maps friendly names to launch commands
# ------------------------------------------------------------------
APP_REGISTRY: dict[str, list[str]] = {
    # Browsers
    "chrome": ["start", "chrome"],
    "google chrome": ["start", "chrome"],
    "firefox": ["start", "firefox"],
    "edge": ["start", "msedge"],
    "microsoft edge": ["start", "msedge"],
    "brave": ["start", "brave"],

    # Communication
    "discord": ["start", "discord:"],  # URI protocol
    "slack": ["start", "slack:"],
    "teams": ["start", "msteams:"],
    "microsoft teams": ["start", "msteams:"],
    "telegram": ["start", "tg:"],
    "whatsapp": ["start", "whatsapp:"],
    "zoom": ["start", "zoommtg:"],

    # Productivity
    "notepad": ["notepad.exe"],
    "notepad++": ["start", "notepad++"],
    "vscode": ["code"],
    "vs code": ["code"],
    "visual studio code": ["code"],
    "word": ["start", "winword"],
    "excel": ["start", "excel"],
    "powerpoint": ["start", "powerpnt"],
    "onenote": ["start", "onenote:"],
    "notion": ["start", "notion:"],
    "obsidian": ["start", "obsidian:"],

    # Media
    "spotify": ["start", "spotify:"],
    "vlc": ["start", "vlc"],

    # System
    "explorer": ["explorer.exe"],
    "file explorer": ["explorer.exe"],
    "cmd": ["cmd.exe"],
    "command prompt": ["cmd.exe"],
    "powershell": ["powershell.exe"],
    "terminal": ["wt.exe"],
    "windows terminal": ["wt.exe"],
    "task manager": ["taskmgr.exe"],
    "calculator": ["calc.exe"],
    "settings": ["start", "ms-settings:"],
    "control panel": ["control.exe"],
    "paint": ["mspaint.exe"],
    "snipping tool": ["snippingtool.exe"],
}


def launch_app(name: str) -> str:
    """Launch an application by name. Tries multiple strategies."""
    app_key = name.strip().lower()

    # Strategy 1: Known app registry
    if app_key in APP_REGISTRY:
        cmd = APP_REGISTRY[app_key]
        try:
            if cmd[0] == "start":
                # Use cmd /c start for URI protocols and named apps
                subprocess.Popen(
                    ["cmd", "/c", "start", ""] + cmd[1:],
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.Popen(
                    cmd,
                    shell=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return f"Launched {name} (via known app registry)"
        except FileNotFoundError:
            pass  # Fall through to next strategy
        except Exception as e:
            pass  # Fall through

    # Strategy 2: Search Start Menu shortcuts
    result = _search_start_menu(app_key)
    if result:
        try:
            os.startfile(result)
            return f"Launched {name} (via Start Menu shortcut: {os.path.basename(result)})"
        except Exception as e:
            pass  # Fall through

    # Strategy 3: Check if it's on PATH
    exe_path = shutil.which(app_key) or shutil.which(app_key + ".exe")
    if exe_path:
        try:
            subprocess.Popen(
                [exe_path],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return f"Launched {name} (found on PATH: {exe_path})"
        except Exception:
            pass

    # Strategy 4: Fallback — cmd /c start
    try:
        subprocess.Popen(
            ["cmd", "/c", "start", "", app_key],
            shell=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return f"Launched {name} (via start command fallback)"
    except Exception as e:
        return f"Failed to launch {name}: {e}"


def _search_start_menu(query: str) -> str | None:
    """Search Start Menu for a .lnk shortcut matching the query."""
    search_dirs = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]

    best_match = None
    best_score = 0

    for search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for lnk_path in glob.glob(os.path.join(search_dir, "**", "*.lnk"), recursive=True):
            filename = os.path.splitext(os.path.basename(lnk_path))[0].lower()
            # Score: exact match > starts with > contains
            if filename == query:
                return lnk_path  # Perfect match
            elif query in filename:
                score = len(query) / len(filename)  # Prefer shorter filenames
                if score > best_score:
                    best_score = score
                    best_match = lnk_path

    return best_match


def open_url(url: str) -> str:
    """Open a URL in the default browser."""
    try:
        # Ensure URL has a protocol
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Opened URL: {url}"
    except Exception as e:
        return f"Failed to open URL: {e}"


def focus_window(title: str) -> str:
    """Bring a window to the foreground by partial title match."""
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass

    try:
        import uiautomation as auto
        root = auto.GetRootControl()
        for win in root.GetChildren():
            if (
                hasattr(win, "ControlTypeName")
                and win.ControlTypeName == "WindowControl"
                and title.lower() in (win.Name or "").lower()
            ):
                win.SetFocus()
                return f"Focused window: {win.Name}"
        return f"Window containing '{title}' not found."
    except Exception as e:
        return f"Failed to focus window: {e}"
