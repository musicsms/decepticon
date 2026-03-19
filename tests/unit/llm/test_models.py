"""Unit tests for decepticon.llm.models"""

import pytest

from decepticon.llm.models import (
    GPT_5,
    HAIKU,
    OPUS,
    SONNET,
    LLMModelMapping,
    ModelAssignment,
    ModelProfile,
    ProxyConfig,
)


class TestModelAssignment:
    def test_defaults(self):
        assignment = ModelAssignment(primary="test-model")
        assert assignment.primary == "test-model"
        assert assignment.fallback is None
        assert assignment.temperature == 0.7
        assert assignment.max_tokens is None

    def test_with_fallback(self):
        assignment = ModelAssignment(
            primary="model-a",
            fallback="model-b",
            temperature=0.3,
        )
        assert assignment.fallback == "model-b"
        assert assignment.temperature == 0.3

    def test_temperature_bounds(self):
        with pytest.raises(Exception):
            ModelAssignment(primary="x", temperature=3.0)
        with pytest.raises(Exception):
            ModelAssignment(primary="x", temperature=-0.1)


class TestLLMModelMapping:
    def test_default_roles_exist(self):
        mapping = LLMModelMapping()
        assert mapping.decepticon is not None
        assert mapping.recon is not None
        assert mapping.exploit is not None
        assert mapping.planning is not None
        assert mapping.postexploit is not None

    def test_get_assignment_valid(self):
        mapping = LLMModelMapping()
        assignment = mapping.get_assignment("recon")
        assert assignment.primary == HAIKU

    def test_get_assignment_invalid(self):
        mapping = LLMModelMapping()
        with pytest.raises(KeyError):
            mapping.get_assignment("nonexistent")

    def test_strategic_agents_use_opus(self):
        """Orchestrator and planner need strongest reasoning — Opus 4.6."""
        mapping = LLMModelMapping()
        for role in ("decepticon", "planning"):
            assert mapping.get_assignment(role).primary == OPUS

    def test_precision_agent_uses_sonnet(self):
        """Exploit needs precision + tool calling balance — Sonnet 4.6."""
        mapping = LLMModelMapping()
        assert mapping.get_assignment("exploit").primary == SONNET

    def test_tactical_agents_cross_provider_fallback(self):
        """Tactical agents fall back across providers for resilience."""
        mapping = LLMModelMapping()
        # Recon: Anthropic (Haiku) primary → Gemini fallback
        recon = mapping.get_assignment("recon")
        assert "anthropic" in recon.primary
        assert "gemini" in recon.fallback
        # PostExploit: Anthropic primary → OpenAI fallback
        post = mapping.get_assignment("postexploit")
        assert "anthropic" in post.primary
        assert "openai" in post.fallback

    def test_all_roles_have_fallback(self):
        """Every role has a fallback for resilience (default profile)."""
        mapping = LLMModelMapping()
        for role in ("decepticon", "planning", "exploit", "recon", "postexploit"):
            assert mapping.get_assignment(role).fallback is not None


class TestModelProfile:
    """Profile-based model preset tests."""

    def test_default_profile_matches_bare_constructor(self):
        default = LLMModelMapping.from_profile("default")
        bare = LLMModelMapping()
        for role in ("decepticon", "planning", "exploit", "recon", "postexploit"):
            assert default.get_assignment(role).primary == bare.get_assignment(role).primary
            assert default.get_assignment(role).fallback == bare.get_assignment(role).fallback

    def test_high_profile_uses_opus_everywhere(self):
        """High profile puts Opus on all roles except recon (Sonnet)."""
        high = LLMModelMapping.from_profile(ModelProfile.HIGH)
        for role in ("decepticon", "planning", "exploit", "postexploit"):
            assert high.get_assignment(role).primary == OPUS
        # Recon uses Sonnet for tool-calling speed at high quality
        assert high.get_assignment("recon").primary == SONNET

    def test_high_profile_anthropic_only_fallbacks(self):
        """High profile fallbacks stay within Anthropic where possible."""
        high = LLMModelMapping.from_profile("high")
        # Planning, exploit, postexploit fall back to Sonnet (Anthropic)
        for role in ("planning", "exploit", "postexploit"):
            assert high.get_assignment(role).fallback == SONNET
        # Recon falls back to Opus
        assert high.get_assignment("recon").fallback == OPUS
        # Orchestrator falls back to GPT-5.4 (cross-provider resilience)
        assert high.get_assignment("decepticon").fallback == GPT_5

    def test_test_profile_all_haiku(self):
        """Test profile uses Haiku everywhere for minimum cost."""
        test = LLMModelMapping.from_profile("test")
        for role in ("decepticon", "planning", "exploit", "recon", "postexploit"):
            assignment = test.get_assignment(role)
            assert assignment.primary == HAIKU
            assert assignment.fallback is None

    def test_profile_from_string(self):
        """Profile can be created from string value."""
        for name in ("default", "high", "test"):
            mapping = LLMModelMapping.from_profile(name)
            assert mapping is not None

    def test_invalid_profile_raises(self):
        with pytest.raises(ValueError):
            LLMModelMapping.from_profile("nonexistent")

    def test_profile_enum_values(self):
        assert ModelProfile.DEFAULT == "default"
        assert ModelProfile.HIGH == "high"
        assert ModelProfile.TEST == "test"


class TestProxyConfig:
    def test_defaults(self):
        config = ProxyConfig()
        assert config.url == "http://localhost:4000"
        assert config.timeout == 120
        assert config.max_retries == 2
