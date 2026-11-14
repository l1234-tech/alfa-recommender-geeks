"""Runtime configuration read from environment variables.

Kept deliberately small: no external settings dependency for the MVP.
"""
from __future__ import annotations

import os
from dataclasses import dataclass


def _flag(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Ranking strategy forwarded to the recommender engine: "baseline" or "hybrid".
    strategy: str = os.getenv("RECO_STRATEGY", "baseline")
    # Default and hard-cap for the number of returned recommendations.
    default_limit: int = int(os.getenv("RECO_DEFAULT_LIMIT", "5"))
    max_limit: int = int(os.getenv("RECO_MAX_LIMIT", "20"))
    # Force the built-in fallback scorer even if the ML package is importable.
    force_builtin: bool = _flag("RECO_FORCE_BUILTIN", False)


settings = Settings()
