"""
Safe PowerShell command execution with an allowlist.
"""

from __future__ import annotations

import subprocess
import re

# Commands considered safe for automatic execution
SAFE_PREFIXES = [
    # File system queries
    "dir", "ls", "Get-ChildItem", "Get-Item", "Get-Content", "Test-Path",
    "Resolve-Path",
    # File operations (create, copy, move — NOT delete)
    "New-Item", "Copy-Item", "Move-Item", "Set-Content",
    # System info
    "Get-Process", "Get-Date", "Get-ComputerInfo", "systeminfo",
    "Get-Volume", "Get-Disk",
    # Network
    "ping", "ipconfig", "nslookup", "Test-NetConnection",
    # Misc safe
    "echo", "Write-Output", "hostname", "whoami",
]

# Explicitly blocked patterns (even if they start with a safe prefix)
BLOCKED_PATTERNS = [
    "Remove-Item", "Remove-", "Delete", "Format-",
    "Stop-Process", "Stop-Computer", "Restart-Computer",
    "Invoke-WebRequest", "Invoke-RestMethod", "Start-Process",
    "Set-ExecutionPolicy", "Disable-", "Enable-",
    "rm ", "rm\t", "del ", "del\t", "rmdir",
]

CHAINING_PATTERNS = [";", "|", "&&", "||"]


def run_powershell(cmd: str) -> str:
    """Run a PowerShell command if it passes the safety check."""
    stripped = cmd.strip()
    if not stripped:
        return "Command blocked by safety policy: empty command."

    for pattern in CHAINING_PATTERNS:
        if pattern in stripped:
            return f"Command blocked by safety policy: command chaining is not allowed ('{pattern}')."

    # Check blocked patterns first
    for pattern in BLOCKED_PATTERNS:
        if pattern.lower() in stripped.lower():
            return f"Command blocked by safety policy: contains '{pattern}'. Use a safe command or ask the user to run it manually."

    # Check if command starts with an allowed prefix
    command_name = re.split(r"\s+", stripped, maxsplit=1)[0]
    is_safe = any(command_name.lower() == prefix.lower() for prefix in SAFE_PREFIXES)
    if not is_safe:
        return (
            f"Command '{stripped[:60]}...' blocked by safety policy. "
            f"Allowed prefixes: {', '.join(SAFE_PREFIXES[:8])}..."
        )

    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = result.stdout if result.returncode == 0 else result.stderr
        if not out.strip():
            out = "(no output)" if result.returncode == 0 else f"Exit code: {result.returncode}"
        # Truncate
        if len(out) > 3000:
            out = out[:3000] + "\n...[truncated]"
        return out
    except subprocess.TimeoutExpired:
        return "Command timed out after 15 seconds."
    except Exception as e:
        return f"Shell execution failed: {e}"
