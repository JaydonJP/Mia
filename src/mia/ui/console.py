"""
Rich terminal UI for Mia — spinners, colored logs, and styled output.

Provides the MiaConsole class that the agent uses to display:
- Animated thinking spinners
- Color-coded log messages
- Styled response panels
- User input prompts
"""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.spinner import Spinner
from rich.live import Live
from rich.theme import Theme
from rich.markdown import Markdown
import time
import threading


# Custom theme for Mia
MIA_THEME = Theme({
    "system": "bold cyan",
    "tool": "bold yellow",
    "llm": "bold green",
    "error": "bold red",
    "network": "bold blue",
    "mia": "bold magenta",
    "user": "bold white",
    "dim": "dim white",
})


class MiaConsole:
    """Rich-powered terminal interface for Mia."""

    def __init__(self):
        self.console = Console(theme=MIA_THEME)
        self._spinner_live: Live | None = None
        self._spinner_lock = threading.Lock()

    # ------------------------------------------------------------------
    # Banner
    # ------------------------------------------------------------------
    def print_banner(self, mode: str = "local", model: str = "unknown"):
        banner = Text()
        banner.append("\n ╔══════════════════════════════════════════╗\n", style="bold cyan")
        banner.append(" ║", style="bold cyan")
        banner.append("         M I A  •  AI Assistant          ", style="bold magenta")
        banner.append("║\n", style="bold cyan")
        banner.append(" ╠══════════════════════════════════════════╣\n", style="bold cyan")
        banner.append(" ║", style="bold cyan")
        banner.append(f"  Mode: {mode:<10}  Model: {model:<17}", style="white")
        banner.append("║\n", style="bold cyan")
        banner.append(" ║", style="bold cyan")
        banner.append("  Type 'quit' to exit, 'help' for commands ", style="dim white")
        banner.append("║\n", style="bold cyan")
        banner.append(" ╚══════════════════════════════════════════╝\n", style="bold cyan")
        self.console.print(banner)

    # ------------------------------------------------------------------
    # Logging (called by the agent)
    # ------------------------------------------------------------------
    def log(self, category: str, message: str) -> None:
        """Print a color-coded log line."""
        style_map = {
            "System": "system",
            "Tool": "tool",
            "LLM": "llm",
            "Error": "error",
            "Network": "network",
        }
        style = style_map.get(category, "dim")
        prefix = f"[{category}]"
        self.console.print(f"  {prefix:>12} {message}", style=style)

    # ------------------------------------------------------------------
    # Spinner (thinking indicator)
    # ------------------------------------------------------------------
    def start_spinner(self, text: str = "Thinking...") -> None:
        """Start an animated spinner. Call stop_spinner() when done."""
        with self._spinner_lock:
            if self._spinner_live is not None:
                return  # Already spinning
            self._spinner_live = Live(
                Spinner("dots", text=f"  [bold cyan]{text}[/]"),
                console=self.console,
                refresh_per_second=10,
                transient=True,
            )
            self._spinner_live.start()

    def stop_spinner(self) -> None:
        """Stop the animated spinner."""
        with self._spinner_lock:
            if self._spinner_live:
                self._spinner_live.stop()
                self._spinner_live = None

    # ------------------------------------------------------------------
    # Responses
    # ------------------------------------------------------------------
    def print_response(self, text: str) -> None:
        """Display Mia's response in a styled panel."""
        self.stop_spinner()
        panel = Panel(
            Markdown(text),
            title="[bold magenta]Mia[/]",
            border_style="magenta",
            padding=(0, 2),
        )
        self.console.print(panel)

    def print_error(self, text: str) -> None:
        """Display an error message."""
        self.stop_spinner()
        self.console.print(f"  [bold red]✗ Error:[/] {text}")

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def get_input(self) -> str:
        """Get user input with a styled prompt."""
        try:
            return self.console.input("\n [bold white]You >[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            return "quit"

    # ------------------------------------------------------------------
    # Help
    # ------------------------------------------------------------------
    def print_help(self):
        help_text = """
[bold cyan]Available Commands:[/]
  [bold]quit / exit[/]     — Exit Mia
  [bold]mode <m>[/]        — Switch mode (local / cloud / auto)
  [bold]model[/]           — Show current model info
  [bold]clear[/]           — Clear conversation history
  [bold]tools[/]           — List available tools
  [bold]workflows[/]       — List available workflows
  [bold]help[/]            — Show this help

[dim]Anything else is treated as a message to Mia.[/]
"""
        self.console.print(help_text)
