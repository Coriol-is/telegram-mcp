"""Telegram MCP Server."""

from importlib import import_module
from typing import Any

from .client import client, logger, start_client

__all__ = ["app", "client", "logger", "main", "mcp", "start_client"]


def __getattr__(name: str) -> Any:
    if name == "app":
        return getattr(import_module(".api", __name__), name)
    if name in {"main", "mcp"}:
        return getattr(import_module(".server", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
