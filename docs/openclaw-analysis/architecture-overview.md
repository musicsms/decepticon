# OpenClaw Architecture Overview

## 1. Design Philosophy

OpenClaw은 "개인 AI 어시스턴트"를 지향한다. 핵심 설계 원칙:

- **Local-first**: Gateway는 사용자 디바이스에서 실행 (기본 `127.0.0.1:18789`)
- **Channel-agnostic**: 하나의 에이전트가 모든 메시징 채널에 동시 연결
- **Plugin-extensible**: 코어는 린(lean)하게, 기능은 플러그인으로
- **Security-first**: DM 페어링, allowlist, SSRF 보호 등 기본 보안

## 2. Core Components

### 2.1 Gateway (Control Plane)

```
src/gateway/
  ├── server.impl.ts          # Gateway 초기화, 플러그인 부트스트랩
  ├── server/
  │   ├── ws-connection.ts     # WebSocket 라이프사이클
  │   └── ws-connection/
  │       └── message-handler.ts  # 프레임 파싱, connect 핸드셰이크
  ├── protocol/
  │   ├── schema.ts            # 프로토콜 스키마 정의
  │   └── index.ts             # 에러 코드, 검증
  ├── server-chat.ts           # chat.send RPC 핸들러
  └── auth.js                  # 인증, 디바이스 페어링
```

**역할**: 모든 클라이언트(CLI, UI, 모바일 노드, Discord 봇)의 단일 진입점. WebSocket JSON-RPC로 세션, 채널, 도구, 이벤트를 통합 관리.

### 2.2 Routing Engine

```
src/routing/
  ├── resolve-route.ts         # 라우트 해석 (peer → agent → session)
  └── session-key.ts           # 세션 키 빌더
```

**바인딩 우선순위** (first match wins):
1. Exact peer → 2. Parent peer → 3. Guild+Roles → 4. Guild → 5. Team → 6. Account → 7. Channel → 8. Default

**세션 키 형식**:
```
agent:<agentId>:main                              # DM (기본)
agent:<agentId>:discord:channel:<channelId>        # 길드 채널
agent:<agentId>:discord:channel:<id>:thread:<tid>  # 스레드
```

### 2.3 Pi Agent Runtime

```
src/agents/
  ├── pi-embedded-runner/
  │   ├── run.ts               # runEmbeddedPiAgent() 진입점
  │   ├── runs.ts              # 글로벌 싱글톤 상태 관리
  │   ├── system-prompt.ts     # 프롬프트 조립
  │   ├── compact.ts           # 컨텍스트 압축
  │   └── tool-result-truncation.ts  # 도구 결과 가지치기
  ├── pi-embedded-subscribe.ts # 이벤트 스트리밍 브릿지
  ├── agent-command.ts         # 에이전트 명령 실행
  └── command/
      ├── attempt-execution.ts # 실행 시도 로직
      └── session.ts           # 세션 해석
```

**런타임 모델**: `@mariozechner/pi-agent-core` 기반 임베디드 에이전트. 모델+도구 파이프라인 → 세션 관리 → 채널 전달.

### 2.4 Channel Extensions

```
extensions/
  ├── discord/src/
  │   ├── channel.ts                    # Discord 플러그인 진입점
  │   └── monitor/
  │       ├── provider.ts               # 봇 클라이언트 + 이벤트 리스너
  │       ├── message-handler.ts        # 메시지 핸들러 생성
  │       ├── message-handler.preflight.ts  # 권한/멘션 검증
  │       ├── message-handler.process.ts    # 메시지 처리 → Gateway
  │       └── inbound-worker.ts         # 비동기 작업 큐
  ├── slack/src/...
  ├── telegram/src/...
  └── ... (22+ channels)
```

### 2.5 Skills System

```
skills/                        # 55개 스킬 디렉토리
  ├── coding-agent/SKILL.md    # 코딩 에이전트 (핵심)
  ├── tmux/SKILL.md            # 터미널 세션 관리
  ├── discord/SKILL.md         # Discord 액션
  ├── github/SKILL.md          # GitHub CLI
  ├── taskflow/SKILL.md        # 내구성 플로우
  └── ...

src/agents/skills/
  ├── workspace.ts             # 스킬 로딩/필터링/스냅샷
  ├── types.ts                 # 스킬 타입 정의
  └── config.ts                # 스킬 설정 해석
```

**YAML 프론트매터 형식**:
```yaml
---
name: coding-agent
description: Delegate to Claude Code/Codex/Pi agents
metadata:
  openclaw:
    emoji: "\U0001F4BB"
    os: ["darwin", "linux"]
    requires:
      anyBins: [claude, codex, opencode]
---
```

### 2.6 Plugin SDK

```
src/plugin-sdk/               # 200+ public exports
  ├── plugin-entry.ts          # definePluginEntry
  ├── channel-contract.ts      # 채널 플러그인 인터페이스
  ├── provider-entry.ts        # AI 프로바이더 인터페이스
  ├── core.ts                  # 코어 API
  └── ...

src/plugins/
  ├── loader.ts                # 플러그인 디스커버리/로딩
  ├── registry.ts              # 플러그인 레지스트리
  ├── hooks.ts                 # 30+ 라이프사이클 훅
  ├── types.ts                 # 플러그인 타입 시스템
  ├── clawhub.ts               # ClawHub 마켓플레이스
  └── marketplace.ts           # 커뮤니티 마켓플레이스
```

**Capability Registration Model**:
```typescript
api.registerProvider(...)                      // 텍스트 추론
api.registerChannel(...)                       // 메시징 채널
api.registerTool(factory, opts)                // 에이전트 도구
api.registerHook(hook)                         // 라이프사이클 훅
api.registerImageGenerationProvider(...)       // 이미지 생성
api.registerSpeechProvider(...)                // 음성 합성
// ... 20+ 등록 메서드
```

### 2.7 Hooks Engine

```
src/hooks/
  ├── loader.ts                # 훅 로딩/합성
  ├── install.ts               # 훅 설치/검증
  ├── config.ts                # 훅 설정
  └── message-hook-mappers.ts  # 메시지 이벤트 → 훅 트리거
```

**주요 훅 타입**:

| Category | Hooks |
|----------|-------|
| Agent Lifecycle | `before_agent_start`, `before_agent_reply`, `agent_end` |
| Model & Prompt | `before_model_resolve`, `before_prompt_build` |
| Tool Execution | `before_tool_call`, `after_tool_call` |
| Message | `message_received`, `message_sending`, `message_sent` |
| Subagent | `subagent_spawning`, `subagent_ended` |
| Session | `session_start`, `session_end` |
| Compaction | `before_compaction`, `after_compaction` |

## 3. Data Flow Summary

```
Inbound Message (any channel)
    ↓
Channel Extension (dedupe, debounce, preflight)
    ↓
Routing Engine (binding match → agentId + sessionKey)
    ↓
Gateway RPC (chat.send → agent command)
    ↓
Pi Agent Runtime (model call → tool execution → streaming)
    ↓
Auto-Reply Pipeline (block chunking → tool summaries)
    ↓
Channel Delivery (format → send → thread binding update)
```

## 4. Decepticon과의 비교

| Aspect | Decepticon 2.0 | OpenClaw |
|--------|---------------|----------|
| **목적** | Red team 자동화 | 개인 AI 어시스턴트 |
| **에이전트** | LangGraph + create_agent() | Pi agent core (임베디드) |
| **채널** | CLI (Ink.js) | 22+ 메시징 채널 |
| **세션** | Fresh per iteration | Persistent + daily reset |
| **컨텍스트** | 관찰 마스킹, 출력 오프로딩 | 압축(compaction) + 가지치기(pruning) |
| **자율 루프** | Ralph loop (opplan.json) | Cron + subagent + ACP spawn |
| **샌드박스** | Docker Kali Linux | Docker / SSH sandbox |
| **하네스** | 자체 미들웨어 스택 | Plugin SDK + hooks |
