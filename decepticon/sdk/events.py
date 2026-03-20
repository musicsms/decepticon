"""Custom event types for LangGraph Platform streaming.

These events are emitted by agents and consumed by clients (Ink CLI, Web UI)
via the LangGraph SDK streaming interface.
"""

from enum import StrEnum


class EventType(StrEnum):
    """Custom event types emitted during agent execution."""

    SUBAGENT_START = "subagent_start"
    SUBAGENT_END = "subagent_end"
    PROGRESS = "progress"
