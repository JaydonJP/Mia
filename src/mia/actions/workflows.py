"""
Workflow engine - named automation sequences loaded from config/workflows.yaml.
"""

from __future__ import annotations

import time
import yaml
from pathlib import Path

from .apps import launch_app, open_url


_WORKFLOWS: dict | None = None


def _load_workflows() -> dict:
    global _WORKFLOWS
    if _WORKFLOWS is not None:
        return _WORKFLOWS

    config_path = Path(__file__).resolve().parents[3] / "config" / "workflows.yaml"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        _WORKFLOWS = data.get("workflows", {})
    else:
        _WORKFLOWS = {}

    return _WORKFLOWS


def list_workflows() -> str:
    """List all available workflows."""
    workflows = _load_workflows()
    if not workflows:
        return "No workflows defined. Add them in config/workflows.yaml."

    lines = ["Available workflows:"]
    for name, wf in workflows.items():
        desc = wf.get("description", "No description")
        lines.append(f"  - {name}: {desc}")
    return "\n".join(lines)


def activate_workflow(name: str) -> str:
    """Activate a named workflow and execute all actions in sequence."""
    workflows = _load_workflows()
    wf_key = name.strip().lower().replace(" ", "_")

    workflow = workflows.get(wf_key)
    if not workflow:
        for key, val in workflows.items():
            if wf_key in key.lower() or key.lower() in wf_key:
                workflow = val
                wf_key = key
                break

    if not workflow:
        available = ", ".join(workflows.keys()) if workflows else "none"
        return f"Workflow '{name}' not found. Available: {available}"

    actions = workflow.get("actions", [])
    if not actions:
        return f"Workflow '{wf_key}' has no actions defined."

    results = [f"Activating workflow: {wf_key}"]
    for action in actions:
        action_type = action.get("type", "")
        target = action.get("target", "")
        try:
            delay = min(max(float(action.get("delay", 1.5)), 0), 30)
        except (TypeError, ValueError):
            delay = 1.5

        if action_type == "launch_app":
            result = launch_app(target)
            results.append(f"  -> {result}")
        elif action_type == "open_url":
            result = open_url(target)
            results.append(f"  -> {result}")
        else:
            results.append(f"  -> Unknown action type: {action_type}")

        time.sleep(delay)

    return "\n".join(results)


def reload_workflows() -> str:
    """Reload workflow definitions from disk."""
    global _WORKFLOWS
    _WORKFLOWS = None
    _load_workflows()
    count = len(_WORKFLOWS) if _WORKFLOWS else 0
    return f"Reloaded {count} workflows from config."
