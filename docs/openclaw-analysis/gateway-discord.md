# Gateway & Discord Integration

## 1. Gateway Control Plane

### 1.1 Gateway란?

OpenClaw Gateway는 **단일 프로세스 제어 평면**으로, 모든 메시징 채널과 클라이언트의 중앙 허브이다.

- **단일 멀티플렉스 포트** (기본 `127.0.0.1:18789`)에서 WebSocket RPC, HTTP API, Control UI 제공
- 모든 채널(Discord, Telegram, WhatsApp 등)의 **유일한 연결 소유자**
- 세션 상태는 Gateway가 소유 (UI 클라이언트가 아님)

### 1.2 WebSocket Protocol (v3)

**전송**: WebSocket 텍스트 프레임, JSON 페이로드

**핸드셰이크** (첫 프레임 MUST be `connect`):
```json
{
  "type": "req",
  "id": "unique-id",
  "method": "connect",
  "params": {
    "auth": { "token": "..." },
    "deviceId": "...",
    "minProtocol": 3,
    "maxProtocol": 3
  }
}
```

**프레임 유형**:
```
Request:   { type: "req", id, method, params }
Response:  { type: "res", id, ok, payload|error }
Event:     { type: "event", event, payload, seq, stateVersion }
```

**주요 메서드**:
- `connect` — 인증 + 핸드셰이크
- `agent` — 에이전트 실행 요청 (비동기, runId 반환)
- `agent.wait` — 실행 완료 대기
- `chat.send` — 채널 메시지 전송
- `health` — 상태 확인

**이벤트 스트리밍**:
```json
{
  "type": "event",
  "event": "agent",
  "payload": {
    "runId": "...",
    "sessionKey": "agent:main:discord:channel:123",
    "status": "thinking|streaming|done",
    "text": "..."
  }
}
```

### 1.3 인증 모델

| 방식 | 설명 |
|------|------|
| `shared-secret` | 토큰 또는 비밀번호 기반 (기본) |
| `trusted-proxy` | 프록시 뒤에서 신뢰 |
| `none` | 인증 없음 (개발용) |

**디바이스 페어링**: 새 디바이스 → 페어링 코드 발급 → `openclaw pairing approve` → 디바이스 토큰 발행

## 2. Discord Integration

### 2.1 아키텍처

Discord 통합은 **플러그인 확장**으로 구현되어 있다:

```
extensions/discord/src/
  ├── channel.ts                    # 진입점 (lazy-load 모듈)
  ├── monitor/
  │   ├── provider.ts               # Discord 봇 클라이언트 셋업
  │   ├── message-handler.ts        # 핸들러 생성 + dedupe + debounce
  │   ├── message-handler.preflight.ts  # 멘션/allowlist/그룹 검증
  │   ├── message-handler.process.ts    # 메시지 → Gateway 라우팅
  │   └── inbound-worker.ts         # 비동기 작업 큐 처리
  ├── send.js                       # Discord 메시지 전송
  ├── mentions.ts                   # 멘션 패턴 매칭
  └── allow-list.ts                 # allowlist 관리
```

### 2.2 메시지 처리 파이프라인

```
Discord API Event (메시지 수신)
    ↓
registerDiscordListener (이벤트 핸들러 등록)
    ↓
createDiscordMessageHandler
  ├── 중복 제거 (5분 TTL, 최대 5000개 캐시)
  ├── 디바운싱 (inboundDebouncePolicy)
  └── 프리플라이트 검증
    ↓
preflightDiscordMessage
  ├── 멘션 게이팅 (길드 채널: @봇 필요 여부)
  ├── allowlist 검증 (허용된 사용자/역할)
  ├── 그룹 정책 확인
  └── 세션 키 + 에이전트 라우트 결정
    ↓
buildDiscordInboundJob → inboundWorker.enqueue
    ↓
processDiscordMessage
  ├── resolveDiscordAgentRoute (바인딩 매칭)
  ├── formatInboundEnvelope (텍스트, 미디어, 메타데이터)
  ├── 에이전트 호출 (sessionKey 기반)
  └── 결과 스트리밍
    ↓
deliverDiscordReply
  ├── 대상 결정 (원본 채널, 스레드, DM)
  ├── 텍스트 청킹 (Discord 2000자 제한)
  └── Discord REST API 전송
```

### 2.3 세션 스코핑

| 소스 | 세션 키 형식 | 격리 |
|------|-------------|------|
| DM (기본) | `agent:main:main` | 모든 DM 공유 |
| DM (per-peer) | `agent:main:discord:dm:<userId>` | 사용자별 격리 |
| 길드 채널 | `agent:main:discord:channel:<channelId>` | 채널별 격리 |
| 스레드 | `agent:main:discord:channel:<id>:thread:<tid>` | 스레드별 격리 |

### 2.4 멀티 에이전트 라우팅

Discord 서버에서 역할/채널별로 다른 에이전트를 할당할 수 있다:

```jsonc
{
  "agents": {
    "list": [
      { "id": "main", "workspace": "~/.openclaw/workspace" },
      { "id": "coding", "workspace": "~/.openclaw/workspace-coding" },
      { "id": "research", "workspace": "~/.openclaw/workspace-research" }
    ]
  },
  "bindings": [
    // 'developer' 역할 → coding 에이전트
    { "match": { "channel": "discord", "guildId": "123", "roles": ["developer"] }, "agentId": "coding" },
    // 기본 → main 에이전트
    { "match": { "channel": "discord", "guildId": "123" }, "agentId": "main" }
  ]
}
```

### 2.5 브로드캐스트 (병렬 실행)

하나의 메시지를 여러 에이전트가 동시에 처리:

```jsonc
{
  "broadcast": {
    "strategy": "parallel",
    "DISCORD_CHANNEL_ID": ["coding", "research", "logger"]
  }
}
```

### 2.6 스레드 바인딩

Discord 스레드는 OpenClaw 세션에 자동 바인딩된다:
- **Idle timeout**: 비활성 시 자동 아카이브
- **Max age**: 최대 수명 설정 가능
- **컨텍스트 격리**: 스레드별 독립 대화 컨텍스트

### 2.7 Discord 설정 예시

```jsonc
{
  "channels": {
    "discord": {
      "enabled": true,
      "token": {
        "source": "env",
        "provider": "default",
        "id": "DISCORD_BOT_TOKEN"
      },
      "groupPolicy": "allowlist",
      "guilds": {
        "GUILD_ID": {
          "requireMention": false,    // 모든 메시지에 반응
          "users": ["USER_ID"]        // 허용 사용자
        }
      },
      "dm": {
        "groupEnabled": false
      }
    }
  }
}
```

## 3. Gateway Event System

### 3.1 에이전트 이벤트

에이전트 실행 중 WebSocket으로 스트리밍되는 이벤트:

| Event | Description |
|-------|-------------|
| `agent.start` | 에이전트 실행 시작 |
| `agent.thinking` | 추론 단계 (스트리밍) |
| `agent.tool` | 도구 호출 |
| `agent.result` | 도구 결과 수신 |
| `agent.final` | 최종 응답 |
| `agent.error` | 에러 발생 |
| `agent.stop` | 실행 중단/취소 |

### 3.2 Presence & Tick

```json
// Presence: 시스템 상태 변경 시
{ "event": "presence", "payload": { "sessions": [...], "queue": { "pending": 3 } } }

// Tick: keep-alive + 주기적 상태
{ "event": "tick", "payload": { "tickNumber": 1, "activeAgents": 2 } }
```

## 4. 보안 기본값

| Feature | Default |
|---------|---------|
| 바인딩 | loopback only (`127.0.0.1`) |
| DM 정책 | `pairing` (페어링 코드 필요) |
| 그룹 정책 | `allowlist` |
| 인증 | shared-secret 필수 |
| Non-loopback | 명시적 승인 필요 |
