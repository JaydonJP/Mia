import yaml
import re
from pathlib import Path

class Redactor:
    def __init__(self, config_path="config/sensitive_apps.yaml"):
        self.blocklist = []
        try:
            path = Path(__file__).parent.parent.parent.parent / config_path
            with open(path, "r") as f:
                data = yaml.safe_load(f)
                self.blocklist = data.get("blocklist", [])
        except Exception as e:
            print(f"Failed to load sensitive apps list: {e}")
            
    def is_sensitive(self, title):
        if not title:
            return False
        return any(b.lower() in title.lower() for b in self.blocklist)
        
    def redact_tree(self, tree):
        """Redact sensitive fields from the UI tree before sending to cloud."""
        if "elements" in tree:
            for elem in tree["elements"]:
                name = elem.get("name", "").lower()
                # Redact passwords, credit cards, SSNs, etc.
                if any(k in name for k in ["password", "credit card", "ccv", "ssn", "secret"]):
                    elem["value"] = "[REDACTED]"
        return tree
