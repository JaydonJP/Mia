import json


class AccessibilityTree:
    def __init__(self):
        # Set faster timeout for uiautomation
        try:
            import uiautomation as auto
            auto.SetGlobalSearchTimeout(1)
        except Exception:
            pass

    def _ensure_com(self):
        """Initialize COM on the current thread. Required when called from
        non-main threads (e.g. FastAPI/uvicorn worker threads)."""
        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass  # Already initialized on this thread

    def get_active_window_tree(self):
        """Get a simplified JSON tree of the active window's UI elements."""
        self._ensure_com()
        
        try:
            import uiautomation as auto
            window = auto.GetForegroundControl()
        except Exception as e:
            return {"title": "Unknown", "type": "Unknown", "elements": [], "error": f"COM error: {e}"}
        
        if not window:
            return {"title": "Unknown", "type": "Unknown", "elements": []}

        tree = {
            "title": window.Name or "Untitled",
            "type": window.ControlTypeName or "Unknown",
            "elements": []
        }

        # Traverse the first few levels of the tree to extract clickable/typable elements
        try:
            for control, depth in auto.WalkControl(window, maxDepth=3):
                if depth == 0:
                    continue
                # Only include elements that might be interactive or contain info
                if control.ControlTypeName in ['ButtonControl', 'EditControl', 'TextControl', 'DocumentControl', 'TabItemControl', 'ListItemControl', 'HyperlinkControl']:
                    # Filter out empty elements to save tokens
                    if control.Name and control.Name.strip():
                        value = None
                        try:
                            vp = control.GetValuePattern()
                            if vp:
                                value = vp.Value
                        except Exception:
                            pass
                        tree["elements"].append({
                            "name": control.Name,
                            "type": control.ControlTypeName.replace("Control", ""),
                            "value": value
                        })
        except Exception as e:
            tree["error"] = f"Failed to traverse tree: {e}"

        return tree

    def get_tree_summary(self):
        """Returns the tree as a JSON string for the LLM."""
        tree = self.get_active_window_tree()
        return json.dumps(tree, indent=2)
