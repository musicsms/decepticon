# OpenClaw System Architecture Analysis

> Reference: `reference/openclaw/` (latest commit synced 2026-04-10)

OpenClaw은 개인용 AI 어시스턴트 플랫폼으로, 로컬 Gateway 제어 평면을 통해 다양한 메시징 채널(Discord, Telegram, Slack 등)에서 AI 에이전트를 자율적으로 운용할 수 있다. 한국 개발자 커뮤니티에서 "가재 키우기"라 불리는 자율 개발 워크플로우의 핵심 인프라이다.

## Documents

| Document | Description |
|----------|-------------|
| [Architecture Overview](./architecture-overview.md) | 전체 시스템 아키텍처 및 핵심 컴포넌트 |
| [Gateway & Discord Integration](./gateway-discord.md) | Gateway 제어 평면, WebSocket 프로토콜, Discord 메시지 라우팅 |
| [Agent Runtime & Sessions](./agent-runtime.md) | Pi 에이전트 런타임, 세션 관리, 컨텍스트 엔진, Cron 자동화 |
| [Coding Agent & Harness Integration](./coding-agent-harness.md) | 코딩 에이전트 스킬, ACP 프로토콜, OMC/OMO 하네스 통합 |
| [Autonomous Workflow Guide](./autonomous-workflow.md) | "가재 키우기" 자율 개발 워크플로우 완전 가이드 |
| [Dev Crayfish Setup](./dev-crayfish-setup.md) | 개발 가재 셋업 가이드 (OpenClaw + OMC/OMO + Discord) |
| [Hacking Crayfish Architecture](./hacking-crayfish-architecture.md) | 해킹 가재 변환 아키텍처 (OpenClaw Juice → Decepticon) |
| [Universal Ralph Loop](./universal-ralph-loop.md) | 유니버설 Ralph Loop 아키텍처 + Plan Adapter 패턴 |

## Quick Architecture Diagram

```
                         Developer (Discord / Telegram / Slack)
                                       |
                                       v
                    +------------------+------------------+
                    |         OpenClaw Gateway            |
                    |     (WS Control Plane :18789)       |
                    |                                     |
                    |  +----------+  +-----------------+  |
                    |  | Routing  |  | Session Manager |  |
                    |  +----------+  +-----------------+  |
                    |  +----------+  +-----------------+  |
                    |  | Plugins  |  |   Hooks Engine  |  |
                    |  +----------+  +-----------------+  |
                    +------------------+------------------+
                              |                |
                   +----------+----------+     |
                   v                     v     v
            +-----------+        +------------------+
            | Pi Agent  |        | Subagent / ACP   |
            | Runtime   |        | Spawn Manager    |
            +-----------+        +------------------+
                   |                     |
            +------+------+      +------+------+
            v             v      v             v
      +---------+  +----------+  +---------+  +----------+
      | Skills  |  | Tools    |  | Claude  |  | Codex /  |
      | System  |  | (bash,   |  | Code    |  | OpenCode |
      |         |  |  browser)|  | (OMC)   |  | (OMO)    |
      +---------+  +----------+  +---------+  +----------+
                                      |             |
                                      v             v
                                 +------------------------+
                                 |   Docker / SSH Sandbox |
                                 |   (Isolated Execution) |
                                 +------------------------+
```

## Key Metrics

- **Channels**: 22+ messaging surfaces (WhatsApp, Telegram, Discord, Slack, Signal, iMessage, etc.)
- **Source**: ~52 src/ directories, 54 skills, 40+ extensions
- **Plugin SDK**: 200+ public exports, capability registration model
- **Hooks**: 30+ lifecycle hook types (agent, tool, message, session, compaction)
- **Protocol**: WebSocket JSON-RPC v3 with idempotency keys
