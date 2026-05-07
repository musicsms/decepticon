# XBOW Validation Benchmark — Cross-Project Comparison

Side-by-side numbers for AI / LLM pentesting agents that have **publicly released results on the XBOW Validation Benchmark** (104 web-app CTF
challenges across 3 difficulty tiers — [`xbow-engineering/validation-benchmarks`](https://github.com/xbow-engineering/validation-benchmarks)).

> **Decepticon mode & status** — **black-box** (no source code, configs, or hints — purely network-reachable surface, like a real external
> attacker). L1 and L3 sweeps complete; **L2 sweep is in progress**, so the Decepticon overall number is interim.
> Live per-challenge data: [`benchmark/results/README.md`](../benchmark/results/README.md).
>
> **Companion memo** — A Google Doc memo (private link) was provided as a reference but could not be fetched (403 — share permission
> required). Numbers below come from public sources and the user-supplied tables.

---

## Headline — Overall Pass Rate

```mermaid
xychart-beta horizontal
    title "XBOW pass rate (104 challenges) — projects that published their results"
    x-axis ["Shannon (white-box)","Strix","XBOW","PentestGPT","Red-MIRROR","Cyber-AutoAgent","MAPTA","Decepticon (L1+L3, L2 ongoing)","PentestAgent","AutoPT","VulnBot"]
    y-axis "%" 0 --> 100
    bar [96.15, 96.0, 86.5, 86.5, 86.0, 84.62, 76.9, 92.5, 50.0, 46.0, 6.0]
```

> Decepticon shown on **L1 + L3 only** (49 / 53 = 92.5 %) until the L2 sweep finishes. Shannon's 96.15 % is **white-box, hint-removed** —
> not directly comparable to the black-box numbers next to it.

---

## Comparison Matrix — XBOW Publishers Only

| System | XBOW Score | Mode | Architecture | Source |
|---|---|---|---|---|
| **Shannon Lite** (KeygraphHQ) | **96.15 %** (100 / 104) | white-box, hint-removed | autonomous, source-aware | [github.com/KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon) |
| **Strix** (usestrix) | **96 %** (100 / 104) | black-box | multi-agent, browser + HTTP proxy + terminal | [github.com/usestrix/strix](https://github.com/usestrix/strix) |
| **XBOW** (commercial) | **86.5 %** (90 / 104) | black-box | proprietary multi-agent + validators | [xbow.com](https://xbow.com/) |
| **PentestGPT** (USENIX '24) | **86.5 %** (90 / 104) | black-box | agentic framework | [github.com/GreyDGL/PentestGPT](https://github.com/GreyDGL/PentestGPT) |
| **Red-MIRROR** | **86.0 %** | black-box | multi-agent + RAG + dual-phase reflection | arXiv [2603.27127](https://arxiv.org/abs/2603.27127) |
| **Cyber-AutoAgent** (westonbrown) | **84.62 %** (~88 / 104) [latest]; 81 % (v0.1.1); 45.92 % (v0.1.0, 45/98) | black-box | meta-agent + Strands framework | [github.com/westonbrown/Cyber-AutoAgent](https://github.com/westonbrown/Cyber-AutoAgent) |
| **MAPTA** | **76.9 %** (80 / 104) | black-box | multi-agent (planner / executor / verifier) | arXiv [2508.20816](https://arxiv.org/abs/2508.20816) |
| **Decepticon** *(this repo)* | **L1+L3: 92.5 %** (49 / 53) · L2 in progress | black-box | LangGraph multi-agent kill-chain | [github.com/PurpleAILAB/Decepticon](https://github.com/PurpleAILAB/Decepticon) |
| **PentestAgent** | 50.0 % | black-box | single-agent w/ playbooks | re-tested in Red-MIRROR; paper arXiv 2411.05185 |
| **AutoPT** | 46.0 % | black-box | LangChain + GPT-4o single-agent | re-tested in Red-MIRROR |
| **VulnBot** | 6.0 % | black-box | scripted multi-agent baseline | re-tested in Red-MIRROR; paper arXiv [2501.13411](https://arxiv.org/abs/2501.13411) |

---

## Per-Difficulty — Where Published

| System | L1 (Easy) | L2 (Medium) | L3 (Hard) | Total |
|---|---|---|---|---|
| **Strix**         | **45 / 45 — 100 %** | **49 / 51 — 96 %** | 6 / 8 — 75 %  | 100 / 104 — 96 %    |
| **Shannon Lite**  | not split           | not split          | not split     | 100 / 104 — 96.15 % |
| **XBOW**          | 42 / 46 — 91.1 %    | 43 / 50 — 74.5 %   | 5 / 8 — 62.5 % | 90 / 104 — 86.5 %  |
| **Decepticon**    | **42 / 45 — 93.3 %** | 9 / 51 — **17.6 % (in progress)** | **7 / 8 — 87.5 %** | 58 / 104 — 55.8 % (interim) |

XBOW also published per-level cost / time:

| Level | Avg cost | Avg time |
|---|---|---|
| L1 | $0.65 | 4.4 m |
| L2 | $1.33 | 6.9 m |
| L3 | $3.03 | 12.9 m |

```mermaid
xychart-beta
    title "Pass rate by difficulty — Strix · XBOW · Decepticon"
    x-axis ["L1 (Easy)", "L2 (Medium)", "L3 (Hard)"]
    y-axis "%" 0 --> 100
    line [100, 96, 75]
    line [91.1, 74.5, 62.5]
    line [93.3, 17.6, 87.5]
```
> Series order: **Strix · XBOW · Decepticon** (Decepticon L2 is mid-run).

---

## Per-Vulnerability — Shannon Lite (only system with full breakdown)

| Vulnerability type             | Total | Solved | Rate |
|--------------------------------|------:|-------:|-----:|
| Broken Authorization           | 25 | 25 | **100 %** |
| SQL Injection                  |  7 |  7 | **100 %** |
| Blind SQL Injection            |  3 |  3 | **100 %** |
| XSS                            | 23 | 22 | 95.65 % |
| SSRF / Misconfiguration        | 22 | 21 | 95.45 % |
| Server-Side Template Injection | 13 | 12 | 92.31 % |
| Command Injection              | 11 | 10 | 90.91 % |
| **Total**                      | **104** | **100** | **96.15 %** |

MAPTA per-class (overall 76.9 %): SSRF **100 %** · Misconfig **100 %** · SSTI **85 %** · SQLi **83 %** · Broken Authz **83 %** · Cmd-Inj **75 %** · XSS **57 %** · Blind SQLi **0 %**.

Decepticon confirmed-solve counts (L1 + L3 done, L2 partial) — see the
[Confirmed Exploit Coverage matrix](../benchmark/results/README.md#confirmed-exploit-coverage-by-web-attack-class) — 22 web vuln classes,
top: XSS (14), Cmd-Inj (7), Default Creds (7), SSTI (6), IDOR (6), SQLi (5), LFI (5), PrivEsc (5).

---

## Adjacent — Other AI-Pentest Tools / Benchmarks

These projects are notable but **do not yet publish numbers on XBOW** (or use a different benchmark), so they are not in the headline chart.

| Project / Benchmark | What | Why excluded |
|---|---|---|
| **CAI** (aliasrobotics)  | Open-source ReAct multi-agent framework, 300+ LLMs                   | Reports on its own **CAIBench** meta-benchmark, not XBOW |
| **HexStrike** / **PentestAgent (testified-oss)** | MCP server + 150+ tools                                  | No XBOW results published |
| **HackSynth (HACKSY)**   | Planner / Summarizer dual-module                                     | Evaluated on a 200-challenge picoCTF + OverTheWire suite, not XBOW |
| **xOffense**             | Fine-tuned Qwen3-32B multi-agent (arXiv 2509.13021)                  | Uses **AutoPenBench** (72.72 %) and AI-Pentest-Benchmark |
| **CAIBench**             | Meta-benchmark from Alias Robotics                                   | Different benchmark |
| **MHBench**              | Multi-host network red-team benchmark ([bsinger98/MHBench](https://github.com/bsinger98/MHBench)) | Different benchmark |
| **AutoPenBench**         | Single-host pentest benchmark (used by xOffense)                     | Different benchmark |

---

## Sources

- XBOW Validation Benchmarks — <https://github.com/xbow-engineering/validation-benchmarks>
- XBOW corp blog — <https://xbow.com/blog/top-1-how-xbow-did-it> · <https://xbow.com/blog/we-ran-1060-autonomous-attacks>
- Shannon — <https://github.com/KeygraphHQ/shannon> (results in `xben-benchmark-results/`)
- Strix — <https://github.com/usestrix/strix> · <https://www.strix.ai/>
- Cyber-AutoAgent — <https://github.com/westonbrown/Cyber-AutoAgent> · v0.1.0 results: [discussion #12](https://github.com/westonbrown/Cyber-AutoAgent/discussions/12) · [Brown — *From Single Agent to Meta-Agent*](https://medium.com/data-science-collective/from-single-agent-to-meta-agent-building-the-leading-open-source-autonomous-cyber-agent-e1b704f81707)
- PentestGPT — <https://github.com/GreyDGL/PentestGPT> · [DeepWiki XBOW page](https://deepwiki.com/GreyDGL/PentestGPT/5.1-xbow-validation-suite)
- MAPTA — arXiv [2508.20816](https://arxiv.org/abs/2508.20816)
- Red-MIRROR — arXiv [2603.27127](https://arxiv.org/abs/2603.27127)
- VulnBot — arXiv [2501.13411](https://arxiv.org/abs/2501.13411)
- xOffense — arXiv [2509.13021](https://arxiv.org/abs/2509.13021)
- CAI — <https://github.com/aliasrobotics/CAI> · CAIBench: <https://news.aliasrobotics.com/caibench-a-meta-benchmark-for-evaluating-cybersecurity-ai-agents/>
- MHBench — <https://github.com/bsinger98/MHBench>
- Survey — *AI Pentesting Agents 2026* — <https://appsecsanta.com/research/ai-pentesting-agents-2026>
- Awesome list — <https://github.com/insidetrust/awesome-ai-pentest>

> *Last updated: 2026-05-07. Re-check linked READMEs / arXiv versions before citing — projects iterate fast.*
