# Agents

Decepticon runs a **multi-agent system** where a central orchestrator delegates to specialist agents, each with its own tools, skills, and context window.

## Agent Roles

| Agent | Role |
|-------|------|
| **Decepticon** | Orchestrator. Reads the OPPLAN, coordinates the kill chain, delegates tasks to specialists. Owns objective tracking via OPPLAN tools. |
| **Soundwave** | Intelligence officer. Interviews the operator and generates engagement documents — RoE, ConOps, and Deconfliction Plan. Does not execute commands. |
| **Recon** | Reconnaissance and enumeration. Runs scans, discovers services, maps attack surface inside the sandbox. |
| **Exploit** | Exploitation. Attempts initial access through discovered vulnerabilities, credentials, or misconfigurations. |
| **Post-Exploit** | Post-exploitation. Credential access, privilege escalation, lateral movement, C2 management, and data collection. |

## Clean Context Per Objective

Each agent spawns with a **clean context window** per objective — no accumulated noise, no degraded reasoning. Findings persist to disk, not to memory, so every iteration starts sharp.

## Middleware Stack

Every agent is built with an explicit **middleware stack** tailored to its role:

| Middleware | Purpose |
|-----------|---------|
| **SkillsMiddleware** | Progressive skill disclosure with MITRE ATT&CK tags and phase grouping |
| **FilesystemMiddleware** | Sandbox file read/write/edit/glob operations via CompositeBackend |
| **ModelFallbackMiddleware** | Automatic provider failover (e.g., Anthropic → OpenAI) |
| **SummarizationMiddleware** | Observation masking — replaces old verbose outputs with summaries |
| **PromptCachingMiddleware** | Cache boundary markers for Anthropic prompt caching |
| **PatchToolCallsMiddleware** | Fixes malformed tool calls from LLM output |
| **SafeCommandMiddleware** | Blocks session-destroying commands (pkill, nsenter, docker exec) |

The orchestrator additionally has:
- **OPPLANMiddleware** — CRUD tools for objective management (add/get/list/update), dynamic battle tracker injection, state transition validation with dependency checking
- **SubAgentMiddleware** — `task()` tool for delegating work to specialist agents with real-time streaming
