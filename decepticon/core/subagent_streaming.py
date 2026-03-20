"""Sub-agent streaming — live event emission during sub-agent execution.

When the Decepticon orchestrator delegates to a sub-agent via task(),
SubAgentMiddleware calls runnable.invoke() which normally runs silently.

This module wraps the runnable so that invoke() uses stream() internally,
emitting tool calls, results, and AI messages through two channels:

  1. UIRenderer context var — for the Python CLI (StreamingEngine)
  2. LangGraph stream writer — for LangGraph Platform HTTP API (custom events)

Architecture:
  StreamingRunnable wraps a compiled LangGraph agent
  → intercepts invoke() → uses stream(mode="values") internally
  → emits events via both channels
  → returns same result as invoke() for SubAgentMiddleware compatibility
"""

from __future__ import annotations

import contextvars
import time
from typing import Any, Callable

# Context variable for the active renderer — set by StreamingEngine.run()
_active_renderer: contextvars.ContextVar[Any] = contextvars.ContextVar(
    "subagent_renderer", default=None
)


def set_subagent_renderer(renderer: Any) -> contextvars.Token:
    """Set the active renderer for sub-agent streaming. Returns token for reset."""
    return _active_renderer.set(renderer)


def clear_subagent_renderer(token: contextvars.Token) -> None:
    """Reset the renderer context var."""
    _active_renderer.reset(token)


def _get_writer() -> Callable | None:
    """Get the LangGraph stream writer if available (for HTTP API streaming)."""
    try:
        from langgraph.config import get_stream_writer

        return get_stream_writer()
    except Exception:
        return None


class StreamingRunnable:
    """Wraps a compiled LangGraph agent to stream events during invoke().

    Drop-in replacement for the runnable field in CompiledSubAgent.

    Two streaming channels:
      - UIRenderer (contextvars): Used by Python CLI's StreamingEngine
      - get_stream_writer(): Used by LangGraph Platform HTTP API (custom events)

    If neither channel is available, falls back to plain invoke().

    All attribute access except invoke() is delegated to the underlying runnable.
    """

    def __init__(self, runnable: Any, name: str):
        self._runnable = runnable
        self._name = name

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        """Stream sub-agent execution, emitting events to available channels."""
        renderer = _active_renderer.get(None)
        has_renderer = renderer is not None and hasattr(renderer, "on_subagent_start")

        # Capture the parent graph's stream writer BEFORE entering sub-agent execution
        writer = _get_writer()

        # Neither channel available — fall back to normal invoke
        if not has_renderer and writer is None:
            return self._runnable.invoke(input, config, **kwargs)

        from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

        # Extract prompt from input for display
        prompt = ""
        if isinstance(input, dict) and "messages" in input:
            msgs = input["messages"]
            if msgs and isinstance(msgs, list):
                for m in reversed(msgs):
                    if isinstance(m, HumanMessage):
                        prompt = str(m.content)[:200]
                        break

        # ── Emit: subagent_start ──
        if has_renderer:
            renderer.on_subagent_start(self._name, prompt)
        if writer:
            writer({"type": "subagent_start", "agent": self._name, "prompt": prompt})

        start = time.monotonic()

        last_state = None
        last_count = 0
        active_tool_calls: dict[str, dict] = {}

        try:
            for state in self._runnable.stream(
                input, config=config, stream_mode="values", **kwargs
            ):
                last_state = state
                messages = state.get("messages", [])
                new_messages = messages[last_count:]
                last_count = len(messages)

                for msg in new_messages:
                    if isinstance(msg, HumanMessage):
                        continue

                    if isinstance(msg, AIMessage):
                        text = msg.content
                        if isinstance(text, list):
                            text = " ".join(
                                block.get("text", "")
                                if isinstance(block, dict)
                                else str(block)
                                for block in text
                            ).strip()
                        if text:
                            text = (
                                text.replace("<result>", "")
                                .replace("</result>", "")
                                .strip()
                            )
                            if text:
                                # ── Emit: subagent_message ──
                                if has_renderer:
                                    renderer.on_subagent_message(self._name, text)
                                if writer:
                                    writer({"type": "subagent_message", "agent": self._name, "text": text})

                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tc in msg.tool_calls:
                                active_tool_calls[tc["id"]] = tc
                                # Serialize args safely for JSON
                                tc_args = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in tc["args"].items()}
                                # ── Emit: subagent_tool_call ──
                                if has_renderer:
                                    renderer.on_subagent_tool_call(
                                        self._name, tc["name"], tc["args"]
                                    )
                                if writer:
                                    writer({"type": "subagent_tool_call", "agent": self._name, "tool": tc["name"], "args": tc_args})

                    elif isinstance(msg, ToolMessage):
                        tc = active_tool_calls.get(msg.tool_call_id)
                        tool_name = tc["name"] if tc else "unknown"
                        tool_args = tc["args"] if tc else {}
                        content = str(msg.content)
                        status = getattr(msg, "status", "success") or "success"
                        tc_args = {k: str(v) if not isinstance(v, (str, int, float, bool)) else v for k, v in tool_args.items()}
                        # ── Emit: subagent_tool_result ──
                        if has_renderer:
                            renderer.on_subagent_tool_result(
                                self._name, tool_name, tool_args, content
                            )
                        if writer:
                            writer({
                                "type": "subagent_tool_result",
                                "agent": self._name,
                                "tool": tool_name,
                                "args": tc_args,
                                "content": content,
                                "status": status,
                            })

        except KeyboardInterrupt:
            elapsed = time.monotonic() - start
            if has_renderer:
                renderer.on_subagent_end(self._name, elapsed, cancelled=True)
            if writer:
                writer({"type": "subagent_end", "agent": self._name, "elapsed": elapsed, "cancelled": True})
            raise
        except Exception:
            elapsed = time.monotonic() - start
            if has_renderer:
                renderer.on_subagent_end(self._name, elapsed, error=True)
            if writer:
                writer({"type": "subagent_end", "agent": self._name, "elapsed": elapsed, "error": True})
            raise

        elapsed = time.monotonic() - start
        # ── Emit: subagent_end ──
        if has_renderer:
            renderer.on_subagent_end(self._name, elapsed)
        if writer:
            writer({"type": "subagent_end", "agent": self._name, "elapsed": elapsed})

        if last_state is None:
            # Fallback — stream yielded nothing (shouldn't happen)
            return self._runnable.invoke(input, config, **kwargs)

        return last_state

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attribute access to the underlying runnable."""
        return getattr(self._runnable, name)
