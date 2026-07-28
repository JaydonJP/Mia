"""
File system operations - sandboxed to user-approved directories.

The allowed directories are configured in ``config/mia.yaml`` under
``filesystem.allowed_dirs``. If no config is present, the user's home
directory and Mia's launch directory are allowed.
"""

from __future__ import annotations

import os
from pathlib import Path


_ALLOWED_DIRS: list[str] | None = None


def _get_allowed_dirs() -> list[str]:
    global _ALLOWED_DIRS
    if _ALLOWED_DIRS is not None:
        return _ALLOWED_DIRS

    try:
        import yaml

        config_path = Path(__file__).resolve().parents[3] / "config" / "mia.yaml"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
            dirs = cfg.get("filesystem", {}).get("allowed_dirs", [])
            _ALLOWED_DIRS = [os.path.expandvars(os.path.expanduser(d)) for d in dirs]
        else:
            _ALLOWED_DIRS = []
    except Exception:
        _ALLOWED_DIRS = []

    for default_dir in (os.path.expanduser("~"), os.getcwd()):
        if default_dir not in _ALLOWED_DIRS:
            _ALLOWED_DIRS.append(default_dir)

    return _ALLOWED_DIRS


def _is_path_allowed(path: str) -> bool:
    """Check if the resolved path falls within an allowed directory."""
    resolved = os.path.normcase(os.path.realpath(path))
    for allowed in _get_allowed_dirs():
        allowed_real = os.path.normcase(os.path.realpath(allowed))
        try:
            if os.path.commonpath([resolved, allowed_real]) == allowed_real:
                return True
        except ValueError:
            continue
    return False


def _expand_path(path: str) -> str:
    if not path or path.strip() in {".", ""}:
        return os.getcwd()
    return os.path.expandvars(os.path.expanduser(path))


def _parent_for_write(path: str) -> str:
    parent = os.path.dirname(path)
    return parent if parent else os.getcwd()


def list_directory(path: str) -> str:
    """List files and folders in a directory."""
    path = _expand_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: '{path}' is outside allowed directories."
    if not os.path.isdir(path):
        return f"Not a directory: '{path}'"

    try:
        entries = sorted(os.listdir(path))
        if not entries:
            return f"Directory '{path}' is empty."

        lines = []
        for entry in entries[:100]:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                lines.append(f"  [DIR]  {entry}/")
            else:
                size_str = _human_size(os.path.getsize(full))
                lines.append(f"  [FILE] {entry}  ({size_str})")

        header = f"Contents of {path} ({len(entries)} items):"
        if len(entries) > 100:
            header += f" (showing first 100 of {len(entries)})"
        return header + "\n" + "\n".join(lines)
    except PermissionError:
        return f"Permission denied: cannot read '{path}'."
    except Exception as e:
        return f"Error listing directory: {e}"


def read_file(path: str) -> str:
    """Read the contents of a text file."""
    path = _expand_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: '{path}' is outside allowed directories."
    if not os.path.isfile(path):
        return f"File not found: '{path}'"

    try:
        size = os.path.getsize(path)
        if size > 500_000:
            return f"File too large ({_human_size(size)}). Maximum is 500 KB."

        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(10_000)

        truncated = " ...[truncated]" if size > 10_000 else ""
        return f"Contents of {os.path.basename(path)}:\n\n{content}{truncated}"
    except PermissionError:
        return f"Permission denied: cannot read '{path}'."
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    path = _expand_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: '{path}' is outside allowed directories."

    try:
        os.makedirs(_parent_for_write(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Written {len(content)} chars to {path}"
    except PermissionError:
        return f"Permission denied: cannot write to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"


def create_directory(path: str) -> str:
    """Create a directory and its parents if needed."""
    path = _expand_path(path)
    if not _is_path_allowed(path):
        return f"Access denied: '{path}' is outside allowed directories."

    try:
        os.makedirs(path, exist_ok=True)
        return f"Created directory: {path}"
    except PermissionError:
        return f"Permission denied: cannot create '{path}'."
    except Exception as e:
        return f"Error creating directory: {e}"


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"
