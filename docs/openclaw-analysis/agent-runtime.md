# Agent Runtime & Sessions

## 1. Pi Agent Runtime

### 1.1 개요

OpenClaw의 에이전트는 `@mariozechner/pi-agent-core` 라이브러리 위에 구축된 **임베디드 Pi 런타임**으로 실행된다. Gateway 내부에서 직접 구동되며, 별도 프로세스가 아닌 싱글 프로세스 내 에이전트 루프이다.

### 1.2 핵심 파일

| File | Role |
|------|------|
| `src/agents/pi-embedded-runner/run.ts:150` | `runEmbeddedPiAgent()` — 메인 진입점 |
| `src/agents/pi-embedded-runner/runs.ts:51-74` | 글로벌 싱글톤 상태 (`Symbol.for`) |
| `src/agents/pi-embedded-subscribe.ts:64` | 이벤트 스트리밍 브릿지 |
| `src/agents/agent-command.ts:200` | 에이전트 명령 실행 셋업 |
| `src/agents/command/attempt-execution.ts` | 실행 시도 로직 |

### 1.3 실행 흐름

```
Gateway RPC (agent 요청)
    ↓ 즉시 {runId, acceptedAt} 반환
agentCommand
    ↓ 모델 + thinking/verbose 해석
    ↓ 스킬 스냅샷 로딩
runEmbeddedPiAgent
    ↓ per-session + global 큐로 직렬화
    ↓ 모델 + 인증 프로파일 해석, Pi 세션 빌드
    ↓ Pi 이벤트 구독, assistant/tool 델타 스트리밍
    ↓ 타임아웃 초과 시 abort
    ↓ payloads + usage 메타데이터 반환
subscribeEmbeddedPiSession
    ↓ tool events → stream: "tool"
    ↓ assistant deltas → stream: "assistant"
    ↓ lifecycle events → stream: "lifecycle"
```

### 1.4 글로벌 싱글톤 상태

번들러가 여러 복사본을 생성해도 일관성을 유지하기 위해 `Symbol.for("openclaw.embeddedRunState")` 사용:

```typescript
// 추적 항목:
{
  activeRuns,           // 활성 실행 맵
  snapshots,            // 스냅샷 캐시
  sessionIdsByKey,      // 세션 키 → ID 매핑
  waiters,              // 완료 대기자
  modelSwitchRequests   // 모델 전환 요청
}
```

### 1.5 스트리밍

- **Assistant 델타**: pi-agent-core에서 스트리밍 → `assistant` 이벤트로 방출
- **Tool 이벤트**: start/update/end 라이프사이클로 `tool` 스트림 엔트리
- **Block 스트리밍**: `text_end` 또는 `message_end` 경계에서 부분 응답
- **Reasoning 스트리밍**: 별도 또는 블록 응답으로 방출

### 1.6 큐잉 & 동시성

- **Session lane**: 세션 키 기준 직렬화 (같은 세션 내 순차 실행)
- **Global lane**: 추가 직렬화 옵션
- **Queue modes**: 채널별 선택
  - `collect` — 메시지 수집 후 일괄 처리
  - `steer` — 실행 중 에이전트에 메시지 주입
  - `followup` — 현재 실행 완료 후 후속 실행

### 1.7 Steering (실행 중 조향)

`steer` 모드에서 인바운드 메시지를 실행 중 에이전트에 주입:
- 현재 assistant 턴의 tool call 실행 완료 후
- 다음 LLM 호출 전에 주입
- 진행 중 tool call을 건너뛰지 않음

## 2. Session Management

### 2.1 세션 유형

| Source | Session Key | Isolation |
|--------|-------------|-----------|
| DM (기본) | `agent:<agentId>:main` | 모든 DM 공유 |
| 그룹 채팅 | `agent:<agentId>:group:<peerId>` | 그룹별 격리 |
| 채널/룸 | `agent:<agentId>:channel:<peerId>` | 채널별 격리 |
| Cron 작업 | `cron:<jobId>` | 실행마다 새 세션 |
| Webhook | `agent:<agentId>:webhook:<hookId>` | 훅별 격리 |
| Subagent | `subagent:<spawnId>` | 스폰별 격리 |

### 2.2 DM 격리 모드 (`session.dmScope`)

| Mode | 동작 |
|------|------|
| `main` (기본) | 모든 DM이 하나의 세션 공유 |
| `per-peer` | 발신자별 격리 (채널 무관) |
| `per-channel-peer` | 채널+발신자별 격리 (권장) |
| `per-account-channel-peer` | 계정+채널+발신자별 격리 |

### 2.3 세션 라이프사이클

```
생성 → 활성 → [리셋 조건 충족] → 새 세션 생성
```

**리셋 트리거**:
- **Daily reset** (기본): 매일 04:00 로컬 시간에 새 세션
- **Idle reset**: `session.reset.idleMinutes` 설정 시
- **수동 리셋**: `/new` 또는 `/reset` 명령
- **모델 전환**: `/new <model>`

### 2.4 저장소

```
~/.openclaw/agents/<agentId>/
  ├── sessions/
  │   ├── sessions.json          # SessionEntry 인덱스
  │   └── <sessionId>.jsonl      # JSONL 메시지 트랜스크립트
  └── agent/
      └── auth-profiles.json     # 에이전트별 인증 프로파일
```

**SessionEntry 필드**:
- `sessionId` (UUID), `updatedAt`, `contextTokens`
- `runtimeModel`, `systemPromptReport`, `abortedLastRun`

**유지보수**:
- `pruneAfter`: 기본 30일 후 삭제
- `maxEntries`: 기본 500개 최대

## 3. Context Engine

### 3.1 컨텍스트 관리 레이어

| Layer | File | 역할 |
|-------|------|------|
| Prompt Assembly | `pi-embedded-runner/system-prompt.ts` | 베이스 프롬프트 + 스킬 + 부트스트랩 |
| Tool Result Pruning | `pi-embedded-runner/tool-result-truncation.ts` | 오래된 도구 결과 인메모리 트림 |
| Compaction | `pi-embedded-runner/compact.ts` | 장문 대화 요약/압축 |
| Context Engine | `src/context-engine/index.ts` | 플러거블 컨텍스트 백엔드 |

### 3.2 Tool Result Pruning (가지치기)

- 매 LLM 호출 전에 **오래된 도구 결과**를 인메모리에서 트림
- Soft-trim: head + tail 유지, 중간 `...`
- Hard-clear: 남은 결과 완전 제거
- 디스크 트랜스크립트는 수정하지 않음
- Anthropic 프로파일에서 기본 활성화

### 3.3 Compaction (압축)

- 컨텍스트 오버헤드가 예비 토큰 초과 시 트리거
- 장문 대화를 요약으로 압축
- `compaction` 스트림 이벤트 방출
- 훅: `before_compaction` / `after_compaction`

## 4. Cron & Automation

### 4.1 CronService

```typescript
CronService {
  start()       // 스케줄러 시작
  stop()        // 종료
  list()        // 모든 작업 조회
  add()         // 작업 생성
  run()         // 즉시 실행
  enqueueRun()  // 큐에 추가
}
```

### 4.2 스케줄 유형

| Type | 예시 | 설명 |
|------|------|------|
| `at` | `2026-04-10T09:00:00Z`, `20m` | 일회성 실행 |
| `every` | `30m`, `2h` | 고정 간격 반복 |
| `cron` | `0 9 * * 1-5` | cron 표현식 (TZ 지원) |

### 4.3 실행 모드

| Style | Session | Best for |
|-------|---------|----------|
| Main session | `main` | 리마인더, 시스템 이벤트 |
| **Isolated** | `cron:<jobId>` | 보고서, 백그라운드 작업 |
| Current session | 바인딩 시점 세션 | 컨텍스트 인식 반복 |
| Custom session | `session:xxx` | 히스토리 누적 워크플로우 |

**Isolated Cron의 장점**:
- 실행마다 새 세션 (컨텍스트 오염 방지)
- 작업별 모델/thinking 레벨 오버라이드
- 도구 제한 가능 (`--tools exec,read`)
- 가벼운 컨텍스트 모드 (`--light-context`)

### 4.4 배달 모드

| Mode | 동작 |
|------|------|
| `announce` | 대상 채널에 요약 전달 (격리 모드 기본) |
| `webhook` | URL로 POST |
| `none` | 내부 전용 |

### 4.5 작업 지속성

- `~/.openclaw/cron/jobs.json`에 저장
- Gateway 재시작 후에도 유지
- 일회성 작업은 성공 후 자동 삭제
- 실행 히스토리 추적/조회 가능

## 5. Tasks System

### 5.1 Task 생성 조건

| Source | Runtime | Notify Policy |
|--------|---------|---------------|
| ACP 실행 | `acp` | `done_only` |
| Subagent 스폰 | `subagent` | `done_only` |
| Cron 작업 | `cron` | `silent` |
| CLI 작업 | `cli` | `silent` |

### 5.2 Task 라이프사이클

```
queued → running → {succeeded | failed | timed_out | cancelled | lost}
```

- `lost`: 런타임이 5분 유예 후 백업 상태를 잃은 경우

### 5.3 알림 전달

- **Direct delivery**: 원본 채널로 직접 전달
- **Session-queued**: 직접 실패 시 시스템 이벤트로 큐잉
- 완료 시 즉시 heartbeat wake 트리거
- 터미널 상태 기록 7일 보존

## 6. Auto-Reply Pipeline

### 6.1 응답 파이프라인

```
에이전트 이벤트 수집
    ↓
Block 청킹 (800-1200자, 단락 경계 선호)
    ↓
Tool 집계 (메타데이터/요약)
    ↓
Reply 형성 (텍스트 + reasoning + tool 요약)
    ↓
Silent 토큰 필터링 (NO_REPLY 제거)
    ↓
메시징 중복 제거
    ↓
채널 전달
```

### 6.2 Block Streaming 설정

| Setting | Default | Description |
|---------|---------|-------------|
| `blockStreamingDefault` | `off` | 블록 스트리밍 기본값 |
| `blockStreamingBreak` | `text_end` | 블록 경계 |
| `blockStreamingChunk` | 800-1200자 | 청크 크기 |
| `*.blockStreaming` | `false` | 채널별 활성화 |

## 7. 타임아웃 설정

| Setting | Default | Description |
|---------|---------|-------------|
| `agents.defaults.timeoutSeconds` | 172800 (48h) | 에이전트 실행 최대 시간 |
| `agents.defaults.llm.idleTimeoutSeconds` | 60 | LLM 유휴 타임아웃 |
