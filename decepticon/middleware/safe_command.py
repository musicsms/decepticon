"""SafeCommandMiddleware — blocks bash commands that destroy the sandbox session.

Commands like `pkill bash` or `killall tmux` kill the tmux server process inside
the Docker container, causing an unrecoverable "no server running" error.  This
middleware intercepts `bash` tool calls *before* execution and returns an error
ToolMessage with a safe alternative suggestion.

Implemented as an AgentMiddleware so it applies uniformly to every agent that
has it in its middleware stack — no per-tool-function patching needed.
"""

from __future__ import annotations

import re
from typing import Any, Awaitable, Callable

from langchain.agents.middleware import AgentMiddleware
from langchain_core.messages import ToolMessage
from langgraph.prebuilt.tool_node import ToolCallRequest
from langgraph.types import Command

# ─── Patterns that would kill the sandbox tmux session ────────────────────

_DANGEROUS_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # ── Session destruction ────────────────────────────────────────────────
    (
        re.compile(r"\bpkill\s+(-\d+\s+)?(-f\s+)?bash\b"),
        "pkill bash kills the tmux session itself. "
        "Use `kill <specific-pid>` or `pkill -f '<your-script-name>'` instead.",
    ),
    (
        re.compile(r"\bkillall\s+(-\d+\s+)?bash\b"),
        "killall bash kills the tmux session itself. Use `kill <specific-pid>` instead.",
    ),
    (
        re.compile(r"\bpkill\s+(-\d+\s+)?(-f\s+)?tmux\b"),
        "pkill tmux destroys the sandbox session. "
        "Use `tmux kill-session -t <name>` for a specific session.",
    ),
    (
        re.compile(r"\bkillall\s+(-\d+\s+)?tmux\b"),
        "killall tmux destroys all sandbox sessions. "
        "Use `tmux kill-session -t <name>` for a specific session.",
    ),
    (
        re.compile(r"\bkill\s+-9\s+(-1|0)\b"),
        "kill -9 -1/0 sends SIGKILL to all processes, destroying the session. "
        "Use `kill <specific-pid>` instead.",
    ),
    # ── Sandbox escape prevention (Claude Code best practice) ─────────────
    (
        re.compile(r"\bdocker\s+(exec|run|cp|build|compose)\b"),
        "Docker CLI commands are blocked — you are INSIDE the sandbox container. "
        "All commands execute directly in the Kali Linux environment.",
    ),
    (
        re.compile(r"\bcat\s+/proc/1/(environ|cmdline|maps)\b"),
        "Reading /proc/1/ exposes host process information. "
        "Use /proc/self/ for current process info instead.",
    ),
    (
        re.compile(r"\bnsenter\b"),
        "nsenter can escape container namespaces. This is blocked for sandbox safety.",
    ),
    (
        re.compile(r"\bmount\s.*\bproc\b|\bmount\s.*\bsys\b|\bmount\s+-t\s+(proc|sys)"),
        "Mounting /proc or /sys filesystems is blocked for sandbox safety.",
    ),
    (
        re.compile(r"\biptables\b|\bip6tables\b|\bnftables\b"),
        "Firewall rule modification is blocked — may violate Rules of Engagement. "
        "Document the finding and request RoE amendment if needed.",
    ),
    (
        re.compile(r"\bip\s+(route|rule)\s+(add|del|flush)\b"),
        "Routing table modification is blocked — may violate Rules of Engagement. "
        "Use the network as-is or document the limitation.",
    ),
]


class SafeCommandMiddleware(AgentMiddleware):
    """Block bash tool calls that would destroy the sandbox tmux session.

    Sits in the middleware stack and intercepts ``bash`` tool calls before
    they reach the actual tool.  If the command matches a dangerous pattern
    (e.g. ``pkill bash``), returns a ``ToolMessage(status="error")`` with a
    safe alternative — the tool is never executed.

    Usage::

        middleware = [
            SafeCommandMiddleware(),   # ← early in the stack
            SkillsMiddleware(...),
            FilesystemMiddleware(...),
            ...
        ]
    """

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        """Intercept bash calls and block session-destroying commands."""
        tool_name = request.tool_call["name"]

        if tool_name == "bash":
            args = request.tool_call.get("args", {})
            command = args.get("command", "")
            is_input = args.get("is_input", False)

            # Only check new commands, not interactive input to a running process
            if command and not is_input:
                for pattern, message in _DANGEROUS_PATTERNS:
                    if pattern.search(command):
                        return ToolMessage(
                            content=f"[BLOCKED] {message}",
                            tool_call_id=request.tool_call["id"],
                            name=tool_name,
                            status="error",
                        )

        return await handler(request)

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        """Synchronous fallback for non-async agent runtimes."""
        tool_name = request.tool_call["name"]

        if tool_name == "bash":
            args = request.tool_call.get("args", {})
            command = args.get("command", "")
            is_input = args.get("is_input", False)

            if command and not is_input:
                for pattern, message in _DANGEROUS_PATTERNS:
                    if pattern.search(command):
                        return ToolMessage(
                            content=f"[BLOCKED] {message}",
                            tool_call_id=request.tool_call["id"],
                            name=tool_name,
                            status="error",
                        )

        return handler(request)
