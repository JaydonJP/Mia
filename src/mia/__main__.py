"""
Mia — AI Desktop Assistant

Entry point for the CLI. Run with:
    python -m mia              (interactive CLI — default)
    python -m mia --server     (start FastAPI backend)
    python -m mia --mode cloud (override LLM mode)
"""

from __future__ import annotations

import argparse
import sys
import yaml
from pathlib import Path


def load_config() -> dict:
    config_path = Path(__file__).parent.parent.parent / "config" / "mia.yaml"
    if config_path.exists():
        with open(config_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}


def run_cli(config: dict, mode_override: str | None = None):
    """Interactive CLI REPL — the primary interface for Mia."""
    from .core.agent import Agent
    from .ui.console import MiaConsole

    console = MiaConsole()

    # Initialize agent
    agent = Agent(config)

    # Override mode if specified
    if mode_override:
        agent.router.set_mode(mode_override)

    # Wire up console logging
    original_log = agent._log

    def console_log(category: str, message: str):
        console.log(category, message)
        # Also emit to event log (the original _log does this)
        agent.event_log.emit("activity", {"category": category, "message": message})

    agent.on_log = console.log  # Set the callback; agent._log will call it

    # Print banner
    console.print_banner(
        mode=agent.router.mode,
        model=agent.router.get_model_name(),
    )

    # Load recent context from DB
    agent.memory.load_from_db(n=6)
    if agent.memory.history:
        console.log("System", f"Loaded {len(agent.memory.history)} messages from previous sessions")

    # REPL loop
    while True:
        user_input = console.get_input()
        if not user_input:
            continue

        # Handle built-in commands
        cmd = user_input.lower().strip()

        if cmd in ("quit", "exit"):
            console.log("System", "Goodbye!")
            break

        if cmd == "help":
            console.print_help()
            continue

        if cmd.startswith("mode "):
            new_mode = cmd.split(" ", 1)[1].strip()
            if new_mode in ("local", "cloud", "auto"):
                agent.router.set_mode(new_mode)
                console.log("System", f"Mode switched to: {new_mode}")
                console.log("System", f"Active model: {agent.router.get_model_name()}")
            else:
                console.print_error("Invalid mode. Use: local, cloud, auto")
            continue

        if cmd == "model":
            console.log("System", f"Mode: {agent.router.mode}")
            console.log("System", f"Model: {agent.router.get_model_name()}")
            continue

        if cmd == "clear":
            agent.memory.clear()
            console.log("System", "Conversation history cleared.")
            continue

        if cmd == "tools":
            tools = agent.executor.list_tools()
            console.log("System", f"Available tools ({len(tools)}): {', '.join(tools)}")
            continue

        if cmd == "workflows":
            from .actions.workflows import list_workflows
            console.console.print(list_workflows())
            continue

        # Process as a message to Mia
        console.start_spinner("Thinking...")
        try:
            response = agent.process(user_input)
            console.stop_spinner()
            console.print_response(response)
        except KeyboardInterrupt:
            console.stop_spinner()
            console.log("System", "Request cancelled.")
        except Exception as e:
            console.stop_spinner()
            console.print_error(str(e))


def run_server():
    """Start the FastAPI backend."""
    from .server import start_server
    start_server()


def main():
    parser = argparse.ArgumentParser(description="Mia — AI Desktop Assistant")
    parser.add_argument(
        "--server", action="store_true",
        help="Start the FastAPI backend server instead of the CLI",
    )
    parser.add_argument(
        "--mode", choices=["local", "cloud", "auto"],
        help="Override the LLM mode (local, cloud, auto)",
    )
    args = parser.parse_args()

    config = load_config()

    if args.server:
        run_server()
    else:
        run_cli(config, mode_override=args.mode)


if __name__ == "__main__":
    main()
