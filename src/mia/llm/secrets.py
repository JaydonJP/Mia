from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_secrets_env() -> list[str]:
    """Load secrets from supported locations without overriding existing env vars."""
    loaded_from: list[str] = []
    repo_root = Path(__file__).resolve().parents[3]
    candidates = [
        Path(os.path.expanduser("~/.mia/secrets.env")),
        repo_root / "config" / "secrets.env",
        repo_root / ".env",
    ]

    for candidate in candidates:
        if candidate.exists():
            load_dotenv(candidate, override=False)
            loaded_from.append(str(candidate))

    return loaded_from
