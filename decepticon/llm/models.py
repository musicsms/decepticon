"""LLM model definitions — per-role model assignments with profile-based presets.

Each agent role gets a primary model and optional fallback. Three profiles
control the cost/performance tradeoff:

  default — Balanced Anthropic-first ensemble (production engagements)
  high    — Maximum performance, Opus everywhere (high-value targets)
  test    — Haiku-only, cheapest possible (development and CI)

Profile selection: DECEPTICON_MODEL_PROFILE=high (env var) or config.

Profiles (March 2026):

  default:
    Orchestrator  Opus 4.6        → GPT-5.4         $5/$25
    Planner       Opus 4.6        → GPT-5.4         $5/$25
    Exploit       Sonnet 4.6      → GPT-4.1         $3/$15
    Recon         Haiku 4.5       → Gemini 2.5 Flash $1/$5
    PostExploit   Sonnet 4.6      → GPT-4.1         $3/$15

  high:
    Orchestrator  Opus 4.6        → GPT-5.4         $5/$25
    Planner       Opus 4.6        → Sonnet 4.6      $5/$25
    Exploit       Opus 4.6        → Sonnet 4.6      $5/$25
    Recon         Sonnet 4.6      → Opus 4.6        $3/$15
    PostExploit   Opus 4.6        → Sonnet 4.6      $5/$25

  test:
    All roles     Haiku 4.5       → (none)           $1/$5

Model names use LiteLLM provider-prefix format for direct proxy routing.
Fallbacks activate via ModelFallbackMiddleware on API failure (outage, rate limit).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class ModelProfile(StrEnum):
    """Model cost/performance profile."""

    DEFAULT = "default"
    HIGH = "high"
    TEST = "test"


# ── Model constants ──────────────────────────────────────────────────────
OPUS = "anthropic/claude-opus-4-6"
SONNET = "anthropic/claude-sonnet-4-6"
HAIKU = "anthropic/claude-haiku-4-5"
GPT_5 = "openai/gpt-5.4"
GPT_4 = "openai/gpt-4.1"
GEMINI_FLASH = "gemini/gemini-2.5-flash"


class ProxyConfig(BaseModel):
    """LiteLLM proxy connection settings."""

    url: str = "http://localhost:4000"
    api_key: str = "sk-decepticon-master"
    timeout: int = 120
    max_retries: int = 2


class ModelAssignment(BaseModel):
    """Primary + fallback model for an agent role."""

    primary: str
    fallback: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class LLMModelMapping(BaseModel):
    """Role → model assignment mapping.

    Model names use LiteLLM provider-prefix format for direct routing.
    Use from_profile() to get a preset configuration.
    """

    # ── Strategic tier ──────────────────────────────────────────────
    # Reasoning-heavy, few iterations, quality > cost

    decepticon: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS, fallback=GPT_5, temperature=0.4,
        )
    )

    planning: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS, fallback=GPT_5, temperature=0.4,
        )
    )

    # ── Precision tier ──────────────────────────────────────────────
    # High-stakes execution, moderate iterations, precision critical

    exploit: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET, fallback=GPT_4, temperature=0.3,
        )
    )

    # ── Tactical tier ───────────────────────────────────────────────
    # Tool-heavy, many iterations, speed + cost efficiency matter

    recon: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=HAIKU, fallback=GEMINI_FLASH, temperature=0.3,
        )
    )

    postexploit: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET, fallback=GPT_4, temperature=0.3,
        )
    )

    def get_assignment(self, role: str) -> ModelAssignment:
        """Get model assignment for a role.

        Raises KeyError if role not found.
        """
        if not hasattr(self, role):
            raise KeyError(f"No model assignment for role: {role}")
        return getattr(self, role)

    @classmethod
    def from_profile(cls, profile: ModelProfile | str) -> LLMModelMapping:
        """Create a model mapping from a named profile.

        Profiles:
          default — Balanced Anthropic-first (Opus/Sonnet/Haiku mix)
          high    — Maximum performance (Opus + Sonnet everywhere)
          test    — Cheapest possible (Haiku-only, no fallbacks)
        """
        profile = ModelProfile(profile)

        if profile == ModelProfile.DEFAULT:
            return cls()

        if profile == ModelProfile.HIGH:
            return cls(
                decepticon=ModelAssignment(
                    primary=OPUS, fallback=GPT_5, temperature=0.4,
                ),
                planning=ModelAssignment(
                    primary=OPUS, fallback=SONNET, temperature=0.4,
                ),
                exploit=ModelAssignment(
                    primary=OPUS, fallback=SONNET, temperature=0.3,
                ),
                recon=ModelAssignment(
                    primary=SONNET, fallback=OPUS, temperature=0.3,
                ),
                postexploit=ModelAssignment(
                    primary=OPUS, fallback=SONNET, temperature=0.3,
                ),
            )

        if profile == ModelProfile.TEST:
            return cls(
                decepticon=ModelAssignment(
                    primary=HAIKU, temperature=0.4,
                ),
                planning=ModelAssignment(
                    primary=HAIKU, temperature=0.4,
                ),
                exploit=ModelAssignment(
                    primary=HAIKU, temperature=0.3,
                ),
                recon=ModelAssignment(
                    primary=HAIKU, temperature=0.3,
                ),
                postexploit=ModelAssignment(
                    primary=HAIKU, temperature=0.3,
                ),
            )

        raise ValueError(f"Unknown profile: {profile}")
