import uiautomation as auto
import json

class AccessibilityTree:
    def __init__(self):
        # Set faster timeout for uiautomation
        auto.SetGlobalSearchTimeout(1)

    def get_active_window_tree(self):
        """Get a simplified JSON tree of the active window's UI elements."""
        window = auto.GetForegroundControl()
        if not window:
            return {"error": "No active window found"}

        tree = {
            "title": window.Name,
            "type": window.ControlTypeName,
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
                        tree["elements"].append({
                            "name": control.Name,
                            "type": control.ControlTypeName.replace("Control", ""),
                            "value": control.GetValuePattern().Value if hasattr(control, "GetValuePattern") and control.GetValuePattern() else None
                        })
        except Exception as e:
            tree["error"] = f"Failed to traverse tree: {e}"

        return tree

    def get_tree_summary(self):
        """Returns the tree as a JSON string for the LLM."""
        tree = self.get_active_window_tree()
        return json.dumps(tree, indent=2)
