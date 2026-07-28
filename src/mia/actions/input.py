def type_text(text: str):
    try:
        import keyboard
        keyboard.write(text, delay=0.01)
        return f"Typed: {text}"
    except Exception as e:
        return f"Failed to type text: {e}"

def hotkey(keys: str):
    try:
        import keyboard
        keyboard.send(keys)
        return f"Pressed hotkey: {keys}"
    except Exception as e:
        return f"Failed to press hotkey: {e}"
    
def click_element(name: str):
    try:
        import pythoncom
        pythoncom.CoInitialize()
    except Exception:
        pass
    
    try:
        import uiautomation as auto
    except Exception as e:
        return f"UI automation is unavailable: {e}"

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
