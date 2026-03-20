"""prompt_toolkit-based input session with pinned prompt and history.

The key technique: ``patch_stdout()`` replaces ``sys.stdout`` with a
``StdoutProxy`` that pushes all writes *above* the prompt line.  Since
Rich's ``console.print()`` writes to ``sys.stdout``, agent output
automatically appears above the input area — the prompt stays pinned
at the terminal bottom.

Based on the nanobot reference implementation pattern.
"""

from __future__ import annotations

import os
import select
import sys
from pathlib import Path
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout as _patch_stdout

# ── Module state ──────────────────────────────────────────────────────
_session: PromptSession[str] | None = None
_saved_term_attrs: Any = None

# Slash commands for tab completion (label → description)
_SLASH_COMMANDS: dict[str, str] = {
    "/help": "Show available commands",
    "/quit": "Exit Decepticon",
    "/exit": "Exit Decepticon",
    "/clear": "Clear screen & conversation",
    "/compact": "Compact conversation context",
    "/plan": "Switch to Planning Agent",
    "/recon": "Switch to Recon Agent",
    "/exploit": "Switch to Exploit Agent",
    "/postexploit": "Switch to PostExploit Agent",
    "/decepticon": "Switch to Decepticon Orchestrator",
}


class SlashCommandCompleter(Completer):
    """Tab-complete slash commands at the start of input."""

    def get_completions(self, document, complete_event):  # noqa: ANN001
        text = document.text_before_cursor.lstrip()
        # Only complete when the entire input so far is the slash command prefix
        if not text.startswith("/"):
            return
        # Don't complete if there's already a space (user typing args)
        if " " in text:
            return
        for cmd, desc in _SLASH_COMMANDS.items():
            if cmd.startswith(text):
                yield Completion(cmd, start_position=-len(text), display_meta=desc)


def _save_terminal_state() -> None:
    """Save termios settings so we can restore on exit (WSL2 compatible)."""
    global _saved_term_attrs
    try:
        import termios

        fd = sys.stdin.fileno()
        if os.isatty(fd):
            _saved_term_attrs = termios.tcgetattr(fd)
    except Exception:
        pass


def restore_terminal() -> None:
    """Restore terminal to original state (echo, line buffering)."""
    if _saved_term_attrs is None:
        return
    try:
        import termios

        termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, _saved_term_attrs)
    except Exception:
        pass


def flush_pending_tty_input() -> None:
    """Drop unread keypresses typed while the agent was generating output."""
    try:
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return
    except Exception:
        return

    # Prefer termios flush (instant, reliable)
    try:
        import termios

        termios.tcflush(fd, termios.TCIFLUSH)
        return
    except Exception:
        pass

    # Fallback: drain with non-blocking reads
    try:
        while True:
            ready, _, _ = select.select([fd], [], [], 0)
            if not ready:
                break
            if not os.read(fd, 4096):
                break
    except Exception:
        return


def init_prompt() -> None:
    """Create the PromptSession with persistent file history."""
    global _session
    _save_terminal_state()

    history_path = Path.home() / ".config" / "decepticon" / "history"
    history_path.parent.mkdir(parents=True, exist_ok=True)

    _session = PromptSession(
        history=FileHistory(str(history_path)),
        auto_suggest=AutoSuggestFromHistory(),
        completer=SlashCommandCompleter(),
        enable_history_search=True,  # Ctrl+R
        enable_open_in_editor=False,
        multiline=False,  # Enter = submit
    )


# Re-export patch_stdout for use as context manager in app.py
patch_stdout = _patch_stdout


async def read_input(agent_name: str) -> str:
    """Read one line of user input with the prompt pinned at bottom.

    Must be called inside a ``patch_stdout()`` context and after
    ``init_prompt()``.
    """
    if _session is None:
        raise RuntimeError("Call init_prompt() first")

    flush_pending_tty_input()

    try:
        result = await _session.prompt_async(
            HTML(f"<b fg='ansired'>you</b> <style fg='ansigray'>({agent_name})</style>&gt; "),
            bottom_toolbar=lambda: HTML(
                f" <b>{agent_name}</b> | /help for commands | Ctrl+C to interrupt"
            ),
        )
    except EOFError as exc:
        raise KeyboardInterrupt from exc

    return result
