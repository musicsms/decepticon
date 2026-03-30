"""Agent system prompt assembly.

Shared prompt fragments (e.g., bash.md) are appended to agent-specific prompts
at load time so every agent has consistent tool guidance without duplication.

Usage:
    load_prompt("recon", shared=["bash", "skills"])
    load_prompt("planning", shared=["skills"])
    load_prompt("postexploit", shared=["bash", "skills"])
"""

from functools import lru_cache
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


@lru_cache(maxsize=16)
def _read_fragment(name: str) -> str:
    """Read and cache a prompt fragment file."""
    path = _PROMPTS_DIR / f"{name}.md"
    if not path.exists():
        msg = f"Shared prompt fragment not found: {path}"
        raise FileNotFoundError(msg)
    return path.read_text(encoding="utf-8")


def load_prompt(name: str, *, shared: list[str] | None = None) -> str:
    """Load an agent system prompt with optional shared fragments appended.

    Args:
        name: Prompt filename without extension (e.g., "recon", "exploit").
        shared: List of shared fragment names to append (e.g., ["bash"]).
            Each name maps to ``<name>.md`` in the prompts directory.

    Returns:
        Assembled system prompt string.
    """
    prompt = _read_fragment(name)
    for fragment_name in shared or []:
        prompt += "\n\n" + _read_fragment(fragment_name)
    return prompt
