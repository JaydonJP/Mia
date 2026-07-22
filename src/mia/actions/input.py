import keyboard
import uiautomation as auto
import pythoncom
import time

def type_text(text: str):
    keyboard.write(text, delay=0.01)
    return f"Typed: {text}"

def hotkey(keys: str):
    keyboard.send(keys)
    return f"Pressed hotkey: {keys}"
    
def click_element(name: str):
    try:
        pythoncom.CoInitialize()
    except Exception:
        pass
    
    window = auto.GetForegroundControl()
    if not window:
        return "No active window to click in."
    
    try:
        # Search up to depth 3 to avoid hanging
        control = window.Control(searchDepth=3, Name=name)
        if control.Exists(2, 0.5):
            control.Click()
            return f"Clicked element: {name}"
        return f"Element '{name}' not found."
    except Exception as e:
        return f"Failed to click: {e}"
