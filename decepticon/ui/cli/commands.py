"""Slash command handlers for the CLI REPL."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from decepticon.ui.cli.console import console

if TYPE_CHECKING:
    from decepticon.core.streaming import UIRenderer


def ensure_auth() -> bool:
    """Check if .env has a valid LLM API key.

    Returns True if ready, False if no key found (prints instructions).
    """
    from decepticon.core.config import _project_root

    env_file = _project_root() / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("#"):
                continue
            for prefix in ("ANTHROPIC_API_KEY=", "OPENAI_API_KEY="):
                if line.startswith(prefix):
                    value = line[len(prefix) :].strip()
                    if value and "your-" not in value and "here" not in value:
                        return True

    console.print("[red]No LLM API key found.[/red]")
    console.print(f"[yellow]Set your API key in:[/yellow] {env_file}")
    console.print("[dim]  ANTHROPIC_API_KEY=sk-ant-...  or  OPENAI_API_KEY=sk-...[/dim]")
    console.print("[dim]  Then restart: docker compose up -d --force-recreate litellm[/dim]\n")
    return False


def switch_agent(name: str, renderer: UIRenderer):
    """Create a fresh agent by name and return (engine, config).

    Raises on failure so the caller can display the error.
    """
    from decepticon.core.streaming import StreamingEngine

    if name == "recon":
        from decepticon.agents import create_recon_agent

        agent = create_recon_agent()
    elif name == "planning":
        from decepticon.agents import create_planner_agent

        agent = create_planner_agent()
    elif name == "exploit":
        from decepticon.agents import create_exploit_agent

        agent = create_exploit_agent()
    elif name == "postexploit":
        from decepticon.agents import create_postexploit_agent

        agent = create_postexploit_agent()
    elif name == "decepticon":
        from decepticon.agents import create_decepticon_agent

        agent = create_decepticon_agent()
    else:
        raise ValueError(f"Unknown agent: {name}")

    new_config = {"configurable": {"thread_id": f"cli-{uuid.uuid4().hex[:8]}"}}
    new_engine = StreamingEngine(agent=agent, renderer=renderer)
    return new_engine, new_config
