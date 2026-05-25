"""Runtime infrastructure for the Decepticon orchestrator process.

Currently exposes the append-only engagement event log; future
primitives (graceful shutdown, resume) will live alongside it.
"""

from decepticon.runtime.event_log import (
    EngagementEvent,
    EventLog,
    EventType,
    read_events,
)

__all__ = [
    "EngagementEvent",
    "EventLog",
    "EventType",
    "read_events",
]
