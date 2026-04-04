[![English](https://img.shields.io/badge/Language-English-blue?style=for-the-badge)](README.md)
[![한국어](https://img.shields.io/badge/Language-한국어-red?style=for-the-badge)](./docs/README_KO.md)


<div align="center">
  <img src="assets/logo_banner.png" alt="Decepticon Logo">
</div>

<h1 align="center">Decepticon — Autonomous Hacking Agent</h1>

<p align="center"><i>"Another AI hacker? Let us guess — it runs nmap and writes a report. Groundbreaking. Then what?"</i></p>

<div align="center">

<a href="https://github.com/PurpleAILAB/Decepticon/blob/main/LICENSE">
  <img src="https://img.shields.io/github/license/PurpleAILAB/Decepticon?style=for-the-badge&color=blue" alt="License: Apache 2.0">
</a>
<a href="https://github.com/PurpleAILAB/Decepticon/stargazers">
  <img src="https://img.shields.io/github/stars/PurpleAILAB/Decepticon?style=for-the-badge&color=yellow" alt="Stargazers">
</a>
<a href="https://github.com/PurpleAILAB/Decepticon/graphs/contributors">
  <img src="https://img.shields.io/github/contributors/PurpleAILAB/Decepticon?style=for-the-badge&color=orange" alt="Contributors">
</a>

<br/>

<a href="https://discord.gg/TZUYsZgrRG">
  <img src="https://img.shields.io/badge/Discord-Join%20Us-7289DA?logo=discord&logoColor=white&style=for-the-badge" alt="Join us on Discord">
</a>
<a href="https://purplelab.framer.ai">
  <img src="https://img.shields.io/badge/Website-purplelab.framer.ai-brightgreen?logo=vercel&logoColor=white&style=for-the-badge" alt="Website">
</a>
<a href="https://docs.decepticon.red">
  <img src="https://img.shields.io/badge/Docs-docs.decepticon.red-8B5CF6?logo=bookstack&logoColor=white&style=for-the-badge" alt="Documentation">
</a>

</div>

<br/>

<div align="center">
  <video src="https://github.com/user-attachments/assets/b3fd40d8-e859-4a39-97f4-bd825694ad96" width="800" controls></video>
</div>

## Install

**Prerequisites**: [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2. That's it.

```bash
curl -fsSL https://raw.githubusercontent.com/PurpleAILAB/Decepticon/main/scripts/install.sh | bash
```

Then configure your API key and start:

```bash
decepticon config    # Set your Anthropic or OpenAI API key
decepticon           # Launch
```

## Try the Demo

Configure your API key first, then run the demo — nothing else needed.

```bash
decepticon config    # Set your API key (one-time)
decepticon demo
```

Launches Metasploitable 2 as a target, loads a pre-built engagement, and runs the full kill chain automatically: port scan, vsftpd exploit, Sliver C2 implant deployment, credential harvesting via C2, and internal network reconnaissance.

---

> **Disclaimer** — Do not use this project on any system or network without explicit written authorization from the system owner. Unauthorized access to computer systems is illegal. You are solely responsible for your actions. The authors and contributors of this project assume no liability for misuse.

---

## What is Autonomous Hacking?

Let's be honest. The "AI + hacking" space is exhausting.

Every other week, someone drops a demo: *"Look, GPT can run nmap!"* Cool. Then what? It either ends up as a party trick that no one actually uses in production — or worse, it crosses a line nobody should cross.

> *"Yet another AI pentesting tool... cool demo. But when does it actually do something a real attacker would?"*

Fair question. Here's our answer.

**Autonomous Hacking** is the next evolution in offensive security. It's not about making hacking easier or more accessible. It's about making **real Red Team operations** executable at machine speed — with the rigor, documentation, and legal framework that separates professionals from script kiddies.

Traditional red teaming demands hundreds of hours of manual work — scanning, enumerating, pivoting, documenting — most of it repetitive, all of it exhausting. Meanwhile, the attack surface grows faster than any human team can cover.

Autonomous Hacking changes the equation. AI agents handle the grind: running scans, analyzing output, chaining techniques, and adapting in real time. The human sets the mission, defines the rules, and focuses on what machines still can't do — intuition, judgment, and creative thinking.

> *"Delegate the repetitive. Focus on the decisive."*

## "But wait — aren't you guys just the same?"

Great question. Short answer: **No.**

Here's the thing most people miss about offensive security — there's a massive difference between *hacking* and *Red Team Testing*.

Red Team Testing is a **regulated, authorized, professional discipline**. Before a single packet leaves the wire, there are documents. Agreements. Rules.

- **RoE (Rules of Engagement)** — Defines what you can and can't touch. Scope, timing, boundaries. Violate this and you're not a red teamer, you're a criminal.
- **ConOps (Concept of Operations)** — Threat actor profile, attack methodology, the "who are we pretending to be" document.
- **Deconfliction Plan** — Separates red team activity from real threats. Source IPs, user-agents, time windows, and a shared code for real-time deconfliction calls with the SOC.
- **OPPLAN (Operations Plan)** — The full mission plan. Objectives, kill chain phases, acceptance criteria. Every action maps to a purpose.

**Decepticon supports all of this. Obviously.**

Every engagement starts with proper documentation. Every objective is tracked. Every action operates within defined boundaries. The agent doesn't just hack — it operates under a formal operations plan, respects the Rules of Engagement, and produces auditable findings.

This isn't a toy. It's a professional Red Team platform that happens to be autonomous.

## Why Decepticon?

Penetration testing finds vulnerabilities. Red teaming answers a harder question: *can your organization survive a real attack?*

Most security tools stop at the scan report. Decepticon doesn't. It thinks in kill chains — reconnaissance, exploitation, privilege escalation, lateral movement, persistence — executing multi-stage operations the way a real adversary would, not the way a scanner does.

Four principles guide everything we build:

**Real Red Teaming, Not Checkbox Security**
Decepticon emulates actual adversary behavior — not just running CVE checks against a list of ports. It reads an operations plan, adapts to what it finds, and pursues objectives through whatever path opens up. The goal is to test your defenses the way they'll actually be tested.

**Interactive Shell Sessions**
Real offensive security tools are interactive — `sliver-client`, `msfconsole`, `evil-winrm`, `sqlmap`, `impacket-psexec`. They don't just take a command and exit. They drop you into a prompt, wait for input, and expect a conversation. Most AI agents can't handle this — they fire one-shot commands via `subprocess.run()` and call it a day. Decepticon runs every command inside persistent tmux sessions with automatic prompt detection. When a tool presents an interactive prompt (`sliver >`, `msf6 >`, `PS C:\>`), the agent detects it and sends follow-up commands — the same way a human operator would. Parallel named sessions, control signals (`C-c`, `C-z`), and stall detection are built in. No workarounds, no hacks. The agent actually *operates* the tools.

**Complete Isolation — Real Red Team Infrastructure**
Every command runs inside a hardened Kali Linux sandbox on a dedicated operational network (`sandbox-net`), fully isolated from the management infrastructure (`decepticon-net`). The C2 team server, victim targets, and the operator sandbox live on one network; the LLM gateway, agent API server, and database live on another. No cross-network access. LangGraph reaches the sandbox exclusively via Docker socket — not the network. You get the full offensive toolkit — nmap, Sliver C2, sqlmap, Impacket — without any risk of leaking credentials or touching the host.

**CLI-First**
Security work belongs in the terminal. Decepticon's interface is a real-time streaming CLI built with Ink — no browser tabs, no dashboards, no context switching. You see what the agent sees, as it happens.

## The Bigger Picture: Offense Serves Defense

Here's what most "offensive AI" projects get wrong: they treat the attack as the destination.

**Decepticon is not the destination. It's Step 1.**

> There are already plenty of offensive AI agents out there. The world doesn't need another "look, AI can hack things" demo.

What the world actually needs is a system that turns offensive capabilities into **defensive evolution**. That's the real vision:

1. **Step 1 — Autonomous Offensive Agent**: Build a world-class hacking agent that executes realistic Red Team operations. *We are here.*
2. **Step 2 — Infinite Offensive Feedback**: Deploy the agent to generate continuous, diverse attack scenarios — an endless stream of real-world threat simulation.
3. **Step 3 — Defensive Evolution**: Channel that feedback into Blue Team capabilities — detection rules, response playbooks, hardening strategies. The defense evolves because the offense never stops.

Think of it as an **Offensive Vaccine**. Just as a biological vaccine exposes the body to weakened pathogens to build immunity, Decepticon exposes your infrastructure to relentless AI-driven attacks to build resilience.

The true value isn't in the attack. It's in the defense system that emerges from surviving it.

## Features

### Engagement Planning

Every operation begins with documents, not commands. The **Soundwave** agent interviews the operator and generates a complete engagement package:

- **RoE (Rules of Engagement)** — Scope boundaries, authorized targets, timing constraints
- **ConOps (Concept of Operations)** — Threat actor profile, attack methodology, kill chain mapping
- **Deconfliction Plan** — Source IPs, user-agents, time windows, deconfliction codes for SOC coordination
- **OPPLAN (Operations Plan)** — Discrete objectives with acceptance criteria, organized by kill chain phase

These documents aren't just paperwork — they drive execution. The OPPLAN feeds directly into the autonomous loop, and the RoE is checked every iteration to enforce scope.

### Autonomous Kill Chain Execution

The orchestrator reads the OPPLAN and executes objectives through a **Ralph loop** — an autonomous iteration cycle that works like a real operator:

1. Load the OPPLAN from disk → pick the next pending objective
2. Build an iteration prompt with RoE guard rails + previous findings
3. Spawn a **fresh specialist agent** with a clean context window
4. Execute → parse objective PASSED/BLOCKED signal
5. Update OPPLAN status → append findings to disk → next objective

Each agent starts with zero accumulated context — no noise from previous iterations degrading reasoning. Findings persist to files, not to agent memory, so every iteration starts sharp. The orchestrator tracks objective dependencies and state transitions (`pending` → `in_progress` → `passed`/`blocked`), adapting the attack path based on what worked and what didn't.

### C2 Integration

Decepticon doesn't just exploit targets — it establishes persistent access through real C2 infrastructure. The **Sliver C2 team server** runs in its own container on the operational network:

- Implant generation, deployment, and session management via `sliver-client`
- mTLS, HTTPS, and DNS-based C2 channels
- Post-exploitation through C2 sessions: credential harvesting, lateral movement, internal recon
- Auto-configuration at first boot — operator config generated and mounted into the sandbox

C2 frameworks are profile-based (`COMPOSE_PROFILES=c2-sliver`). Swap the profile to change the C2 stack without touching anything else.

### Context Engineering

Long-running operations generate massive amounts of output. Without active context management, LLM performance degrades fast. Decepticon applies multi-tier output management inspired by Claude Code:

- **Inline** (≤15K chars) — returned directly in the tool result
- **Offload** (15K–100K) — saved to `/workspace/.scratch/`, summary + preview returned
- **Kill** (>5M) — size watchdog terminates the command before it floods context

On top of that: ANSI escape stripping, repetitive line compression (nmap/nuclei patterns), observation masking (old outputs replaced with summaries), and prompt caching with cache boundary markers. The result: agents stay sharp even after dozens of scans and exploits.

### Skill System

Domain knowledge is injected on-demand through a **progressive skill disclosure** system. Skills are Markdown files organized by kill chain phase with MITRE ATT&CK tags:

- Only skill descriptions (frontmatter) are loaded initially — not the full content
- When the agent needs a technique, the relevant skill is loaded just-in-time
- Skills cover: OSINT, active recon, web exploitation, AD attacks, privilege escalation, lateral movement, credential access, defense evasion, and OPSEC

This keeps context lean while giving agents access to deep domain knowledge when they need it.

### MITRE ATT&CK Integration

MITRE ATT&CK isn't a checkbox — it's woven into every layer of execution:

- **Objective-level tagging** — Every OPPLAN objective carries a `mitre` field with technique IDs (e.g., `T1190`, `T1003.001`). When the orchestrator tracks objective status, ATT&CK coverage tracks with it.
- **Skill-level mapping** — Each skill in the knowledge base declares its ATT&CK techniques in frontmatter. The middleware displays them inline in the agent's skill catalog, so the agent selects techniques with ATT&CK context before execution.
- **Threat actor profiling** — ConOps threat actors define `initial_access` vectors and `ttps` as ATT&CK technique IDs. The engagement methodology defaults to `PTES + MITRE ATT&CK framework`.

The result: every finding, every objective, and every technique maps back to the ATT&CK matrix. Reports don't need post-hoc tagging — the mapping is built into the operation from planning through execution.

### Multi-Model Routing

All LLM calls route through a **LiteLLM proxy** for provider abstraction. Three profiles control the cost/performance tradeoff:

| Profile | Orchestrator | Exploit | Recon | Use Case |
|---------|-------------|---------|-------|----------|
| **eco** | Opus 4.6 | Sonnet 4.6 | Haiku 4.5 | Production engagements |
| **max** | Opus 4.6 | Opus 4.6 | Sonnet 4.6 | High-value targets |
| **test** | Haiku 4.5 | Haiku 4.5 | Haiku 4.5 | Development/CI |

Each role has a primary model and automatic fallback (e.g., Opus → GPT-5.4, Sonnet → GPT-4.1). If the primary provider has an outage or rate limit, the agent seamlessly switches to the fallback — no manual intervention, no failed operations.

## Architecture

Decepticon separates **management infrastructure** from **operational infrastructure** — the same way a real red team separates its planning systems from its attack infrastructure.

```mermaid
graph TB
    subgraph HOST["Host Machine"]
        direction TB

        subgraph MGMT["decepticon-net — Management Infrastructure"]
            direction LR
            LITELLM["LiteLLM Gateway<br/>:4000"]
            POSTGRES["PostgreSQL<br/>:5432"]
            LANGGRAPH["LangGraph API<br/>:2024"]
            LITELLM --- POSTGRES
            LITELLM ---|LLM routing| LANGGRAPH
        end

        subgraph OPS["sandbox-net — Operational Infrastructure"]
            direction LR
            SANDBOX["Kali Sandbox<br/>nmap · sqlmap · Impacket<br/>sliver-client"]
            C2["Sliver C2 Team Server<br/>gRPC :31337 · mTLS :8888<br/>HTTPS :443"]
            VICTIMS["Victim Targets<br/>DVWA · Metasploitable 2"]
            SANDBOX ---|sliver-client| C2
            SANDBOX ---|attack traffic| VICTIMS
        end

        CLI["Ink CLI — Interactive Terminal UI"]
    end

    LANGGRAPH -.->|"Docker Socket<br/>(no network access)"| SANDBOX
    CLI -->|stream_mode=custom| LANGGRAPH

    style MGMT fill:#1a1a2e,stroke:#4a90d9,color:#fff
    style OPS fill:#1a1a2e,stroke:#e74c3c,color:#fff
    style LANGGRAPH fill:#4a90d9,stroke:#4a90d9,color:#fff
    style SANDBOX fill:#2ecc71,stroke:#2ecc71,color:#fff
    style C2 fill:#e74c3c,stroke:#e74c3c,color:#fff
    style VICTIMS fill:#95a5a6,stroke:#95a5a6,color:#fff
    style CLI fill:#9b59b6,stroke:#9b59b6,color:#fff
    style LITELLM fill:#f39c12,stroke:#f39c12,color:#fff
    style POSTGRES fill:#3498db,stroke:#3498db,color:#fff
```

**Why two networks?** The sandbox has zero access to the LLM gateway, database, or agent API. If a target compromises the sandbox, it reaches nothing of value — just like a real red team isolates its C2 infrastructure from its internal systems. LangGraph controls the sandbox exclusively through Docker socket (`docker exec`), not through the network.

**C2 Infrastructure**: The Sliver team server runs in its own container on the operational network. The sandbox has `sliver-client` pre-installed and auto-connects using a config generated at first boot (`/workspace/.sliver-configs/decepticon.cfg`). C2 is profile-based — swap `COMPOSE_PROFILES=c2-sliver` for a different framework without touching the rest of the stack.

**LLM Routing**: LiteLLM acts as a unified API gateway, routing to any LLM backend (Anthropic, OpenAI, local models) with usage tracking, rate limiting, and key management via PostgreSQL.

## Agents

Decepticon runs a **multi-agent system** where a central orchestrator delegates to specialist agents, each with its own tools, skills, and context window.

| Agent | Role |
|-------|------|
| **Decepticon** | Orchestrator. Reads the OPPLAN, coordinates the kill chain, delegates tasks to specialists. Owns objective tracking via OPPLAN tools. |
| **Soundwave** | Intelligence officer. Interviews the operator and generates engagement documents — RoE, ConOps, and Deconfliction Plan. Does not execute commands. |
| **Recon** | Reconnaissance and enumeration. Runs scans, discovers services, maps attack surface inside the sandbox. |
| **Exploit** | Exploitation. Attempts initial access through discovered vulnerabilities, credentials, or misconfigurations. |
| **Post-Exploit** | Post-exploitation. Credential access, privilege escalation, lateral movement, C2 management, and data collection. |

Each agent spawns with a **clean context window** per objective — no accumulated noise, no degraded reasoning. Findings persist to disk, not to memory, so every iteration starts sharp.

Every agent is built with an explicit **middleware stack** tailored to its role — skills for domain knowledge, filesystem access for the sandbox, model fallback for resilience, and prompt caching for efficiency. The orchestrator additionally has OPPLAN tools (add/get/list/update objectives) and sub-agent delegation via `task()`.

## CLI Commands

| Command | Description |
|---------|-------------|
| `decepticon` | Start all services and open the interactive CLI |
| `decepticon demo` | Run guided demo against Metasploitable 2 (full kill chain + Sliver C2) |
| `decepticon stop` | Stop all services |
| `decepticon update [-f]` | Pull latest images and sync configuration (`--force` to re-pull same version) |
| `decepticon status` | Show service status |
| `decepticon logs [service]` | Follow service logs (default: langgraph) |
| `decepticon config` | Edit API keys and settings |
| `decepticon victims` | Start vulnerable test targets (DVWA, Metasploitable) |
| `decepticon remove` | Uninstall Decepticon completely |
| `decepticon --version` | Show installed version |

## Interactive CLI

Once inside the CLI, you have two **screen modes** and a set of slash commands.

**Prompt mode** (default) shows a compact view — sub-agent sessions are collapsed, consecutive tool calls are grouped, and only the latest bash output is expanded. **Transcript mode** (`ctrl+o`) expands everything: full event history, sub-agent details, and complete tool outputs.

| Shortcut | Action |
|----------|--------|
| `ctrl+o` | Toggle between prompt and transcript mode |
| `ctrl+c` | Cancel running stream / exit transcript / exit app |
| `Esc` | Exit transcript mode |

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and shortcuts |
| `/clear` | Clear conversation history |
| `/quit` | Exit Decepticon CLI |

## Vision & Philosophy

This README covers the essentials — but there's a deeper story behind why Decepticon exists, where it's headed, and the philosophy that drives every design decision.

**[Read the full vision and philosophy at docs.decepticon.red](https://docs.decepticon.red)**

Topics covered in the documentation:
- **Core Philosophy** — Reasoning over signatures, hybrid intelligence, stealth as foundation
- **Pentesting vs. Red Teaming** — Why the distinction matters and where Decepticon sits
- **History & Evolution** — From Purple Team AI (2021) through RL and GANs to today's autonomous agents
- **Target Architecture** — Multi-agent hybrid architecture, C2-based stealth execution
- **Why Open Source** — Collective intelligence and the Red/Blue Team feedback loop

## Contributing

We welcome contributions. Whether you're a security researcher, an AI engineer, or someone who cares about making defense better — there's a place for you here.

**Developer Setup** (for contributors):

```bash
git clone https://github.com/PurpleAILAB/Decepticon.git
cd Decepticon

# Python agents
uv sync --dev

# CLI client
cd clients/cli && npm install && cd ../..

# Run locally
docker compose up -d --build
cd clients/cli && npm run dev
```

1. Fork the repository
2. Create a feature branch
3. Commit with clear messages
4. Open a Pull Request

For architecture details and contribution guidelines, visit the [documentation](https://docs.decepticon.red).

## Community

Join the [Discord](https://discord.gg/TZUYsZgrRG) — ask questions, share engagement logs, discuss techniques, or just connect with others who believe defense starts with understanding offense.

## License

[Apache-2.0](LICENSE)

---

<div align="center">
  <img src="assets/main.png" alt="Decepticon">
</div>
