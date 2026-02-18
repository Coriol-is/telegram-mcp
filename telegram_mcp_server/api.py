"""Telegram MCP REST API."""

import inspect
import os
from contextlib import asynccontextmanager
from typing import Any, Awaitable, Callable, Dict

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import server as mcp_server
from .client import client, logger, start_client


class ToolCallRequest(BaseModel):
    args: Dict[str, Any] = {}


def _extract_tool_function(tool_name: str) -> Callable[..., Awaitable[Any]] | None:
    tools = _build_tool_registry()
    return tools.get(tool_name)


def _extract_func_from_entry(entry: Any) -> Callable[..., Awaitable[Any]] | None:
    """Extract callable function from an entry object."""
    for field in ("fn", "func", "handler", "call"):
        func = getattr(entry, field, None)
        if callable(func) and inspect.iscoroutinefunction(func):
            return func
    return None


def _process_dict_container(
    container: Dict[str, Any], registry: Dict[str, Callable[..., Awaitable[Any]]]
) -> None:
    """Process a dictionary container of tools."""
    for name, entry in container.items():
        if callable(entry):
            if inspect.iscoroutinefunction(entry):
                registry[name] = entry
            continue
        func = _extract_func_from_entry(entry)
        if func and inspect.iscoroutinefunction(func):
            registry[name] = func


def _process_list_container(
    container: list, registry: Dict[str, Callable[..., Awaitable[Any]]]
) -> None:
    """Process a list container of tools."""
    for entry in container:
        name = getattr(entry, "name", None)
        func = _extract_func_from_entry(entry)
        if name and func and inspect.iscoroutinefunction(func):
            registry[name] = func


def _extract_tools_from_mcp() -> Dict[str, Callable[..., Awaitable[Any]]]:
    registry: Dict[str, Callable[..., Awaitable[Any]]] = {}
    candidates = ["tools", "_tools", "tool_registry", "_tool_registry"]
    for attr in candidates:
        container = getattr(mcp_server.mcp, attr, None)
        if not container:
            continue
        if isinstance(container, dict):
            _process_dict_container(container, registry)
        elif isinstance(container, list):
            _process_list_container(container, registry)
        if registry:
            break
    return registry


def _extract_tools_from_module() -> Dict[str, Callable[..., Awaitable[Any]]]:
    registry: Dict[str, Callable[..., Awaitable[Any]]] = {}
    for name, obj in mcp_server.__dict__.items():
        if name.startswith("_"):
            continue
        if not callable(obj):
            continue
        if not inspect.iscoroutinefunction(obj):
            continue
        registry[name] = obj
    return registry


def _build_tool_registry() -> Dict[str, Callable[..., Awaitable[Any]]]:
    registry = _extract_tools_from_mcp()
    if registry:
        return registry
    return _extract_tools_from_module()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await start_client()
    try:
        yield
    finally:
        try:
            await client.disconnect()
        except Exception as exc:
            logger.warning("Failed to disconnect Telegram client: %s", exc)


app = FastAPI(
    title="Telegram MCP REST API",
    description="REST API exposing Telegram MCP tools",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tools")
async def list_tools() -> Dict[str, Any]:
    tools = sorted(_build_tool_registry().keys())
    return {"count": len(tools), "tools": tools}


@app.post(
    "/tools/{tool_name}",
    responses={
        400: {"description": "Invalid tool arguments"},
        404: {"description": "Unknown tool"},
        500: {"description": "Tool execution failed"},
    },
)
async def call_tool(tool_name: str, payload: ToolCallRequest) -> Dict[str, Any]:
    func = _extract_tool_function(tool_name)
    if not func:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
    try:
        result = await func(**payload.args)
        return {"tool": tool_name, "result": result}
    except TypeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Tool execution failed: %s", tool_name)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def main() -> None:
    host = os.getenv("TELEGRAM_MCP_API_HOST", "0.0.0.0")  # nosec B104 - intentional for API server
    port = int(os.getenv("TELEGRAM_MCP_API_PORT", "8000"))
    uvicorn.run("telegram_mcp_server.api:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
