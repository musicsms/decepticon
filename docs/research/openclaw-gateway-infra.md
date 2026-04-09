# OpenClaw Gateway Infrastructure Deep Dive

> Decepticon의 RedGate(레드팀 제어 평면) 구현을 위한 OpenClaw Gateway 인프라 완전 분석

## 1. Gateway 설계 원칙

OpenClaw Gateway는 다음 원칙으로 설계되어 있다:

| 원칙 | 설명 | Decepticon 적용 |
|------|------|----------------|
| **Single Process** | 호스트당 하나의 Gateway | 하나의 RedGate 프로세스가 모든 인게이지먼트 관리 |
| **Multiplexed Port** | 하나의 포트(18789)로 WS+HTTP+UI | 하나의 포트로 CLI+Discord+Web 접근 |
| **Gateway-owned State** | 세션 상태는 Gateway 소유 (클라이언트 X) | 인게이지먼트 상태는 RedGate 소유 |
| **Event-driven** | 모든 변경은 이벤트로 스트리밍 | 에이전트 진행 상황 실시간 보고 |
| **Auth-by-default** | 인증 없이는 접속 불가 | 레드팀 운영자 인증 필수 |

## 2. WebSocket Server 구현

### 2.1 서버 초기화

**Source**: `src/gateway/server.impl.ts`

```
Gateway 시작 흐름:
1. Config 로딩 (openclaw.json)
2. Plugin 부트스트랩 (bundled + workspace + marketplace)
3. WebSocket 서버 바인딩 (host:port)
4. HTTP 서버 마운트 (Canvas host, Control UI, API)
5. Channel 프로바이더 시작 (Discord bot, Telegram bot, etc.)
6. Cron 서비스 시작
7. Config 파일 워치 시작 (hot-reload)
```

**핵심 컴포넌트**:
```typescript
// server.impl.ts 구조 (개념적)
class GatewayServer {
  private wsServer: WebSocketServer;
  private httpServer: HttpServer;
  private pluginRegistry: PluginRegistry;
  private cronService: CronService;
  private configWatcher: ConfigWatcher;
  
  async start(config: OpenClawConfig) {
    // 1. Plugin bootstrap
    await this.pluginRegistry.loadAll(config);
    
    // 2. WS server
    this.wsServer = new WebSocketServer({ port: config.gateway.port });
    this.wsServer.on('connection', (ws) => this.handleConnection(ws));
    
    // 3. HTTP server (same port)
    this.httpServer.mount('/__openclaw__/canvas/', canvasHandler);
    this.httpServer.mount('/__openclaw__/a2ui/', a2uiHandler);
    
    // 4. Channels
    for (const channel of config.channels) {
      await channel.start();
    }
    
    // 5. Cron
    await this.cronService.start();
    
    // 6. Config watch
    this.configWatcher.watch(config.path, () => this.reload());
  }
}
```

### 2.2 Connection Lifecycle (연결 생명주기)

**Source**: `src/gateway/server/ws-connection.ts`, `ws-connection/message-handler.ts`

```
Client                          Gateway
  |                               |
  |  ── WebSocket upgrade ──────> |  (HTTP → WS 업그레이드)
  |                               |
  |  ── req:connect ────────────> |  (첫 프레임: MUST be connect)
  |     {                         |
  |       type: "req",            |
  |       id: "uuid",             |
  |       method: "connect",      |
  |       params: {               |
  |         auth: { token: "..." },|
  |         deviceId: "...",      |
  |         platform: "darwin",   |
  |         deviceFamily: "mac",  |
  |         minProtocol: 3,       |
  |         maxProtocol: 3        |
  |       }                       |
  |     }                         |
  |                               |  ← Auth 검증
  |                               |  ← Device 페어링 확인
  |                               |  ← Protocol 버전 협상
  |                               |  ← Challenge nonce 서명 검증
  |                               |
  |  <── res (ok) ───────────────|
  |     {                         |
  |       type: "res",            |
  |       id: "uuid",             |
  |       ok: true,               |
  |       payload: {              |
  |         hello-ok: {           |
  |           features: {         |
  |             methods: [...],   |  (사용 가능 메서드 목록)
  |             events: [...]     |  (구독 가능 이벤트 목록)
  |           },                  |
  |           presence: {...},    |  (현재 상태 스냅샷)
  |           health: {...}       |  (헬스 상태)
  |         }                     |
  |       }                       |
  |     }                         |
  |                               |
  |  <── event:presence ─────────|  (실시간 상태 업데이트 시작)
  |  <── event:tick ─────────────|  (keep-alive + 주기적 상태)
  |                               |
  |  ── req:agent ───────────────>|  (에이전트 실행 요청)
  |     {                         |
  |       method: "agent",        |
  |       params: {               |
  |         message: "...",       |
  |         sessionKey: "...",    |
  |         idempotencyKey: "..." |  (필수! 안전한 재시도)
  |       }                       |
  |     }                         |
  |                               |
  |  <── res:agent (즉시) ───────|  (ack: {runId, status:"accepted"})
  |  <── event:agent (스트리밍) ──|  (thinking/tool/result/final)
  |  <── event:agent (스트리밍) ──|
  |  <── event:agent (최종) ─────|  (status:"done", summary)
```

### 2.3 프레임 유형 및 검증

**Source**: `src/gateway/protocol/schema.ts`

**요청 프레임**:
```json
{
  "type": "req",
  "id": "<idempotency_key>",
  "method": "connect|agent|agent.wait|send|health|status|system-presence|...",
  "params": { }
}
```

**응답 프레임**:
```json
{
  "type": "res",
  "id": "<matching_id>",
  "ok": true,
  "payload": { }
}
// 또는 에러:
{
  "type": "res",
  "id": "<matching_id>",
  "ok": false,
  "error": { "code": "...", "message": "..." }
}
```

**이벤트 프레임** (서버 → 클라이언트 push):
```json
{
  "type": "event",
  "event": "agent|presence|tick|shutdown|chat|cron|heartbeat",
  "payload": { },
  "seq": 42,
  "stateVersion": 7
}
```

**프레임 검증 규칙**:
1. 첫 프레임이 JSON이 아니면 → **hard close**
2. 첫 프레임이 `connect`가 아니면 → **hard close**
3. TypeBox 스키마로 모든 프레임 검증
4. 미지원 메서드 → error response
5. Side-effecting 메서드 (`send`, `agent`)는 **idempotency key 필수**
6. 서버는 짧은 dedupe 캐시로 안전한 재시도 보장

### 2.4 주요 RPC 메서드

| Method | Side-effect | Description |
|--------|-------------|-------------|
| `connect` | No | 핸드셰이크 + 인증 |
| `health` | No | Gateway 헬스 상태 |
| `status` | No | 세션/채널 상태 |
| `agent` | **Yes** | 에이전트 실행 (비동기, runId 반환) |
| `agent.wait` | No | 실행 완료 대기 |
| `chat.send` | **Yes** | 채널 메시지 전송 |
| `send` | **Yes** | 범용 메시지 전송 |
| `system-presence` | No | 시스템 상태 구독 |

## 3. Auth Resolution (인증 해석)

### 3.1 인증 모드

**Source**: `src/gateway/auth.js`, `docs/gateway/security.md`

| Mode | 메커니즘 | 용도 |
|------|---------|------|
| `shared-secret` | 토큰 또는 비밀번호 | 기본값. 로컬/VPS |
| `trusted-proxy` | 프록시 헤더 (X-Forwarded-*) | 리버스 프록시 뒤 |
| `none` | 인증 없음 | 개발 전용 (위험!) |
| Tailscale | tailnet identity | `allowTailscale: true` 시 |

### 3.2 인증 흐름

```
connect 요청 수신
    ↓
1. Auth mode 확인
    ├─ shared-secret: params.auth.token 또는 .password 검증
    ├─ trusted-proxy: 헤더에서 identity 추출
    ├─ Tailscale: tailnet identity로 인증
    └─ none: 모든 연결 허용
    ↓
2. Device identity 확인
    ├─ deviceId가 기존에 등록됨 → 토큰 검증
    └─ 새 deviceId → 페어링 프로세스 시작
    ↓
3. Protocol 버전 협상
    ├─ minProtocol/maxProtocol 교차 확인
    └─ 비호환 → error + close
    ↓
4. Challenge nonce 서명 검증
    ├─ v3: platform + deviceFamily도 바인딩
    └─ 메타데이터 변경 시 repair pairing 필요
    ↓
5. 연결 승인 → hello-ok 응답
```

### 3.3 Device Pairing Protocol (디바이스 페어링)

**Source**: `src/pairing/`, `docs/gateway/pairing.md`

**Decepticon에서 중요한 이유**: 레드팀 운영자만 접근 가능해야 함

```
1. 새 디바이스가 connect 시도
    ↓
2. Gateway가 페어링 코드 생성 (6자리, 1시간 유효)
    ↓
3. Gateway가 코드를 이미 승인된 채널로 알림
   (예: Discord DM, CLI 로그)
    ↓
4. 운영자가 CLI에서 승인:
   $ openclaw pairing approve <channel> <code>
    ↓
5. Gateway가 device token 발행 (영속적)
    ↓
6. 이후 연결은 device token으로 자동 인증
```

**보안 특성**:
- Loopback(127.0.0.1) 연결은 자동 승인 가능 (같은 호스트 UX)
- Non-loopback은 **항상 명시적 승인 필요**
- Tailnet/LAN도 페어링 승인 필요
- 메타데이터(platform, deviceFamily) 변경 시 repair pairing 강제

## 4. Config System (설정 시스템)

### 4.1 설정 파일 구조

```
~/.openclaw/
  ├── openclaw.json              # 메인 설정 파일
  ├── workspace/                 # 기본 에이전트 워크스페이스
  ├── agents/                    # 멀티 에이전트 상태
  │   └── <agentId>/
  │       ├── agent/
  │       │   └── auth-profiles.json  # 에이전트별 인증
  │       └── sessions/
  │           ├── sessions.json      # 세션 인덱스
  │           └── <sessionId>.jsonl  # 트랜스크립트
  ├── cron/
  │   └── jobs.json              # Cron 작업 목록
  ├── skills/                    # 매니지드 스킬
  └── credentials/               # 레거시 크리덴셜
```

### 4.2 Config Hot-Reload

**Source**: `src/config/`, server.impl.ts

```
설정 변경 감지 메커니즘:
1. 파일 워치 (fs.watch) — 설정 파일 변경 감시
2. 변경 감지 시:
   a. 새 설정 파일 파싱 + 스키마 검증
   b. 변경된 섹션만 식별 (diff)
   c. 영향받는 컴포넌트에 reload 시그널:
      - 채널 설정 변경 → 채널 프로바이더 재시작
      - 에이전트 설정 변경 → 스킬 스냅샷 무효화
      - 모델 설정 변경 → auth 프로파일 재로딩
   d. 연결 중인 클라이언트에 config 이벤트 브로드캐스트
3. Hybrid reload mode: 파일 워치 + 주기적 폴링 (watchMs: 1000)
```

**Decepticon 적용**: 인게이지먼트 설정 변경 시 에이전트 재시작 없이 적용 가능

## 5. Queue & Concurrency (큐 & 동시성)

### 5.1 Lane-based FIFO Queue

**Source**: `docs/concepts/queue.md`

OpenClaw의 큐 모델은 **lane-aware FIFO**이다:

```
                          ┌─────────────────────────┐
Inbound Messages ────────>│    Session Lane Queue    │
  (Discord, CLI, etc.)    │  (per session key, 1 at  │
                          │   a time per session)    │
                          └──────────┬──────────────┘
                                     │
                          ┌──────────v──────────────┐
                          │    Global Lane Queue     │
                          │  (main lane, cap by      │
                          │   maxConcurrent)         │
                          └──────────┬──────────────┘
                                     │
                          ┌──────────v──────────────┐
                          │  Agent Execution Pool    │
                          │  (Pi runtime instances)  │
                          └─────────────────────────┘
```

**Lane 유형**:
| Lane | Concurrency | 용도 |
|------|-------------|------|
| `session:<key>` | 1 | 세션 내 순차 실행 (상태 일관성) |
| `main` | 4 (기본) | 인바운드 + heartbeat |
| `subagent` | 8 (기본) | 서브에이전트 실행 |
| `cron` | 별도 | 백그라운드 Cron 작업 |

**핵심**: 세션 내에서는 **항상 1개만 실행** → 세션 상태 일관성 보장

### 5.2 Queue Modes (인바운드 메시지 처리 방식)

| Mode | 동작 | 용도 |
|------|------|------|
| `collect` (기본) | 모든 대기 메시지를 하나의 후속 턴에 합침 | 일반 대화 |
| `steer` | 현재 실행 중인 에이전트에 즉시 주입 | 실행 중 방향 전환 |
| `followup` | 현재 실행 완료 후 새 턴 시작 | 순차 대화 |
| `steer-backlog` | steer + 후속 턴 보존 | 이중 응답 가능 |
| `interrupt` | 현재 실행 중단 + 새 메시지로 재시작 | 긴급 전환 |

**Queue 옵션**:
```json
{
  "messages": {
    "queue": {
      "mode": "collect",
      "debounceMs": 1000,    // 조용해진 후 시작
      "cap": 20,             // 세션당 최대 대기 메시지
      "drop": "summarize"    // 초과 시: old, new, summarize
    }
  }
}
```

### 5.3 Decepticon 적용

```
Decepticon Queue 설계:
- Session lane: engagement:<slug>:<phase>:<target> (목표별 순차 실행)
- Global lane: 최대 동시 sandbox 수 제한 (리소스 관리)
- Cron lane: 야간 자동 스캔 (메인과 독립)
- Subagent lane: 병렬 정찰/익스플로잇 에이전트 (8 동시 기본)
- Mode: "steer" (Discord에서 실행 중 목표 변경 가능)
```

## 6. Event Streaming (이벤트 스트리밍)

### 6.1 에이전트 이벤트

**Source**: `src/infra/agent-events.ts`

```json
// 에이전트 실행 중 스트리밍되는 이벤트
{
  "type": "event",
  "event": "agent",
  "payload": {
    "runId": "run-uuid",
    "sessionKey": "agent:main:discord:channel:123",
    "agentId": "main",
    "stream": "lifecycle|assistant|tool",
    
    // lifecycle 스트림
    "phase": "start|end|error",
    "status": "accepted|streaming|done|error|timeout",
    
    // assistant 스트림
    "delta": "partial text...",
    "reasoning": "thinking...",
    
    // tool 스트림
    "toolName": "bash",
    "toolInput": { "command": "nmap ..." },
    "toolOutput": "scan results...",
    "toolStatus": "start|update|end"
  },
  "seq": 42
}
```

### 6.2 이벤트 유형 전체 목록

| Event | 트리거 | 용도 |
|-------|--------|------|
| `agent` | 에이전트 실행 중 | 진행 상황 스트리밍 |
| `presence` | 시스템 상태 변경 | 활성 세션, 큐 상태 |
| `tick` | 주기적 (keep-alive) | 연결 유지 + 상태 요약 |
| `chat` | 채팅 메시지 | 인바운드/아웃바운드 메시지 |
| `cron` | Cron 작업 이벤트 | 스케줄 실행 상태 |
| `heartbeat` | 메인 세션 heartbeat | 백그라운드 처리 |
| `shutdown` | Gateway 종료 | 클라이언트 graceful disconnect |

### 6.3 Decepticon 적용

```
RedGate 이벤트 설계:
- "objective" 이벤트: 목표 진행 상황 (tool 사용, 결과, 증거)
- "opsec" 이벤트: OPSEC 위반 감지, RoE 검증 결과
- "finding" 이벤트: 취약점 발견 시 즉시 알림
- "engagement" 이벤트: 인게이지먼트 상태 변경
- "scan" 이벤트: 스캔 진행률 및 결과
```

## 7. Deployment Patterns (배포 패턴)

### 7.1 데몬 설치

**Source**: `src/daemon/`

```bash
# systemd (Linux)
openclaw onboard --install-daemon
# → /etc/systemd/user/openclaw-gateway.service 생성
# → 자동 재시작, 로그 journald 통합

# launchd (macOS)
openclaw onboard --install-daemon
# → ~/Library/LaunchAgents/ai.openclaw.gateway.plist 생성
# → 로그인 시 자동 시작
```

### 7.2 Docker 배포

**Source**: `Dockerfile`, `docker-compose.yml`

```yaml
# docker-compose.yml (개념적)
services:
  openclaw-gateway:
    build: .
    ports:
      - "18789:18789"
    volumes:
      - ${OPENCLAW_CONFIG_DIR}:/home/node/.openclaw
      - ${OPENCLAW_WORKSPACE_DIR}:/home/node/.openclaw/workspace
    environment:
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
    restart: unless-stopped
```

### 7.3 VPS 배포 (exe.dev 패턴)

**Source**: `AGENTS.md` (exe.dev VM ops 섹션)

```bash
# VPS에서의 Gateway 운용
# 1. 설치
sudo npm i -g openclaw@latest

# 2. 설정
openclaw config set gateway.mode local

# 3. 데몬 시작
pkill -9 -f openclaw-gateway || true
nohup openclaw gateway run --bind loopback --port 18789 --force \
  > /tmp/openclaw-gateway.log 2>&1 &

# 4. 검증
openclaw channels status --probe
ss -ltnp | rg 18789
tail -n 120 /tmp/openclaw-gateway.log
```

### 7.4 원격 접속

| 방식 | 보안 | 설정 |
|------|------|------|
| **Tailscale** (권장) | E2E 암호화 | `gateway.auth.allowTailscale: true` |
| **SSH 터널** | SSH 암호화 | `ssh -N -L 18789:127.0.0.1:18789 user@host` |
| **TLS** | 인증서 기반 | WS over TLS + 선택적 핀닝 |

## 8. OAuth / Subscription Model (구독 기반 인증)

### 8.1 현재 상태 (2026-04-10)

**Source**: `docs/concepts/oauth.md`, `docs/providers/anthropic.md`, `docs/providers/openai.md`

| Provider | OAuth 지원 | 현재 상태 | 비고 |
|----------|-----------|-----------|------|
| **Anthropic** | Claude CLI 재사용 | **불확실** | "allowed again"이라 하지만 조건부. API key 권장 |
| **OpenAI Codex** | PKCE OAuth | **공식 지원** | "explicitly supported for external tools" |
| **Qwen Cloud** | API Key | 지원 | Coding Plan 구독 |
| **MiniMax** | OAuth (`minimax-portal`) | 지원 | Coding Plan |
| **Z.AI/GLM** | API Key | 지원 | Coding Plan |

### 8.2 Anthropic 상세 (주의 필요)

OpenClaw 문서의 정확한 표현:
> "Anthropic staff told us OpenClaw-style Claude CLI usage is allowed again...
> **unless Anthropic publishes a new policy.**"

**리스크**:
- "allowed again"은 과거에 한번 차단되었다가 다시 허용된 것을 의미
- "unless publishes a new policy"는 언제든 다시 차단 가능함을 시사
- **2026-04-10 기준 사용자 보고**: Anthropic이 이를 다시 차단했을 가능성
- **프로덕션 권장**: API key 사용 (가장 예측 가능)

**메커니즘** (작동하는 경우):
```
1. 호스트에 Claude CLI가 설치되어 있어야 함
2. Claude CLI로 로그인 (claude login)
3. OpenClaw이 Claude CLI의 크리덴셜 파일을 재사용
4. Token sink 패턴: 재사용만 하고 refresh token을 소비하지 않음
5. 외부 CLI가 관리하는 크리덴셜을 re-read
```

### 8.3 OpenAI Codex OAuth (안정적)

**PKCE 플로우**:
```
1. PKCE verifier/challenge 생성 + random state
2. 브라우저에서 https://auth.openai.com/oauth/authorize?... 열기
3. http://127.0.0.1:1455/auth/callback 에서 callback 캡처 시도
4. callback 바인딩 실패 시 (원격/headless): redirect URL/code 수동 붙여넣기
5. https://auth.openai.com/oauth/token 에서 교환
6. access token에서 accountId 추출
7. { access, refresh, expires, accountId } 저장
```

**토큰 갱신**:
```
- expires가 미래 → 저장된 access token 사용
- 만료됨 → file lock 하에 refresh → 크리덴셜 덮어쓰기
- 외부 CLI 크리덴셜: 외부에서 관리, OpenClaw은 re-read만
```

### 8.4 Token Sink 패턴

**왜 존재하는가**: 같은 OAuth 계정을 여러 도구에서 사용하면 refresh token 충돌 발생

```
문제:
  OpenClaw login → refresh token A 발급
  Claude CLI login → refresh token B 발급
  → Token A 무효화 → OpenClaw "logged out"

해결 (Token Sink):
  - auth-profiles.json을 single source of truth으로 사용
  - 여러 profile을 유지하고 결정론적으로 라우팅
  - 외부 CLI 크리덴셜 재사용 시: 
    provenance 기록 + 외부 소스 re-read (rotate 안함)
```

### 8.5 Decepticon 적용

```python
# Decepticon에서의 LLM 인증 전략:
# 1. LiteLLM 프록시 유지 (이미 구축됨, 멀티프로바이더 라우팅)
# 2. OpenAI Codex OAuth 추가 (PKCE) → 구독 기반 비용 절감
# 3. Anthropic은 API key로 유지 (안정성 우선)
# 4. 장기: OpenClaw의 auth-profiles.json 패턴 참고하여
#    에이전트별 인증 프로파일 지원
```

## 9. Health & Monitoring (헬스 & 모니터링)

### 9.1 헬스 체크

```json
// health RPC 응답
{
  "status": "ok",
  "uptime": 123456,
  "sessions": {
    "active": 3,
    "total": 15
  },
  "queue": {
    "pending": 2,
    "active": 1
  },
  "channels": {
    "discord": "connected",
    "telegram": "connected"
  }
}
```

### 9.2 Presence Events

```json
// 시스템 상태 변경 시 자동 전송
{
  "event": "presence",
  "payload": {
    "sessions": [
      { "key": "agent:main:discord:channel:123", "status": "streaming" }
    ],
    "queue": { "pending": 3, "active": 1 },
    "health": { "status": "ok", "uptime": 123456 }
  }
}
```

### 9.3 Doctor 진단

```bash
# 설정 문제, 보안 위험, 채널 상태 등을 자동 진단
openclaw doctor
openclaw doctor --fix  # 자동 수정 가능한 문제 수정

# 보안 감사
openclaw security audit
```

## 10. Decepticon RedGate 설계 시사점

### 10.1 직접 적용 가능한 패턴

| OpenClaw 패턴 | RedGate 적용 |
|-------------|-------------|
| WS JSON-RPC | `engagement.start`, `objective.assign`, `agent.spawn` |
| Device pairing | 운영자 디바이스 인증 (Discord 봇 토큰 + 사용자 ID) |
| Lane-based queue | 인게이지먼트별 세션 레인 + 글로벌 sandbox 제한 |
| Config hot-reload | RoE/OPPLAN 변경 시 에이전트 재시작 없이 적용 |
| Event streaming | 목표 진행, OPSEC 알림, 발견사항 실시간 보고 |
| Daemon install | systemd 데몬으로 24/7 운용 |
| Health checks | Gateway 상태 + sandbox 상태 + 채널 상태 |

### 10.2 구현 우선순위

```
Phase 1 (핵심): WebSocket 서버 + JSON-RPC + Auth
Phase 2 (연결): Discord 채널 + Event streaming
Phase 3 (관리): Config hot-reload + Health checks + Doctor
Phase 4 (배포): Docker + systemd daemon + 원격 접속
```

### 10.3 기술 스택 추천

```
OpenClaw (TypeScript)          →  Decepticon (Python)
─────────────────────────────────────────────────
WebSocket (ws)                 →  websockets / FastAPI WebSocket
TypeBox schema                 →  Pydantic models
Node.js event loop             →  asyncio event loop
fs.watch (config reload)       →  watchdog / inotify
launchd/systemd (daemon)       →  systemd (Linux 전용)
```
