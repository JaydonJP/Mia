import subprocess
import uiautomation as auto
import time

def launch_app(name: str):
    try:
        # Simplest generic launcher for Windows 10/11
        # Start menu search simulation could also work, or start process
        subprocess.Popen(["cmd", "/c", "start", name], shell=True)
        return f"Attempted to launch {name}"
    except Exception as e:
        return f"Failed to launch app: {e}"

def focus_window(title: str):
    try:
        # Search for window
        for win in auto.GetRootControl().GetChildren():
            if win.ControlTypeName == 'WindowControl' and title.lower() in win.Name.lower():
                win.SetFocus()
                return f"Focused window: {win.Name}"
        return f"Window containing '{title}' not found."
    except Exception as e:
        return f"Failed to focus window: {e}"
