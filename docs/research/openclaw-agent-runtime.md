# OpenClaw Agent Runtime & Context Engine Deep Dive

> Decepticon 에이전트 런타임 강화를 위한 OpenClaw Pi Agent 내부 구조 완전 분석

## 1. 런타임 설계 원칙

| 원칙 | 설명 | Decepticon 적용 |
|------|------|----------------|
| **Single embedded runtime** | Gateway 내 단일 에이전트 런타임 | RedGate 내 에이전트 풀 |
| **Session-owned state** | 세션 상태는 Gateway 소유 | 인게이지먼트 상태는 RedGate 소유 |
| **Fresh context per iteration** | Ralph 패턴: 반복마다 새 컨텍스트 | 목표마다 새 에이전트 (현재 Decepticon 방식과 동일) |
| **Prompt cache stability** | 시스템 프롬프트 바이트 안정성 우선 | 프롬프트 캐시 최적화 |
| **Tool result pruning** | 오래된 도구 결과 자동 정리 | bash 출력 정리 (현재 SummarizationMiddleware) |

## 2. Pi Agent Embedded Runner

### 2.1 핵심 파일

| File | Lines | Role |
|------|-------|------|
| `src/agents/pi-embedded-runner/run.ts` | ~150+ | `runEmbeddedPiAgent()` 메인 진입점 |
| `src/agents/pi-embedded-runner/runs.ts` | ~74 | 글로벌 싱글톤 상태 관리 |
| `src/agents/pi-embedded-subscribe.ts` | ~145+ | 이벤트 스트리밍 브릿지 |
| `src/agents/pi-embedded-runner/system-prompt.ts` | | 프롬프트 조립 |
| `src/agents/pi-embedded-runner/compact.ts` | | 컨텍스트 압축 |
| `src/agents/pi-embedded-runner/tool-result-truncation.ts` | | 도구 결과 가지치기 |
| `src/agents/agent-command.ts` | ~200 | 에이전트 명령 실행 셋업 |
| `src/agents/command/attempt-execution.ts` | | 실행 시도 로직 |
| `src/agents/command/session.ts` | | 세션 해석 |

### 2.2 실행 라이프사이클 (상세)

```
Phase 0: RPC 수신
─────────────────
Gateway RPC "agent" 수신
  → params 검증
  → sessionKey/sessionId 해석
  → 세션 메타데이터 영속화
  → 즉시 {runId, acceptedAt} 반환 (비동기 시작)

Phase 1: agentCommand
─────────────────────
  1.1 모델 해석
      → agents.defaults.model.primary 읽기
      → per-agent override 적용
      → thinking/verbose 기본값 해석
  
  1.2 스킬 스냅샷
      → loadWorkspaceSkillEntries() 호출
      → 적격 스킬 필터링 (OS, bins, env, config)
      → buildWorkspaceSkillsPrompt() — 프롬프트용 텍스트 생성
      → 경로 축약 (~/ 치환으로 400-600 토큰 절약)
  
  1.3 runEmbeddedPiAgent 호출

Phase 2: runEmbeddedPiAgent
───────────────────────────
  2.1 큐잉
      → per-session lane에 enqueue (session:<key>)
      → global lane에 enqueue (main)
      → 대기 시 2초 이상이면 verbose 로그
  
  2.2 모델 + 인증 해석
      → provider/model 분할 (첫 번째 / 기준)
      → auth-profiles.json에서 프로파일 로딩
      → OAuth 토큰 만료 확인 → 자동 갱신
      → 폴백 체인: primary → fallback → first configured
  
  2.3 Pi 세션 빌드
      → system prompt 조립 (아래 상세)
      → 도구 정의 빌드
      → 세션 히스토리 로딩 (JSONL)
  
  2.4 이벤트 구독
      → subscribeEmbeddedPiSession() 호출
      → pi-agent-core 이벤트 → OpenClaw 스트림 브릿지
  
  2.5 실행
      → pi-agent-core 루프 시작
      → 모델 호출 → 도구 실행 → 반복
      → 타임아웃 초과 시 abort
  
  2.6 결과 반환
      → payloads + usage 메타데이터

Phase 3: subscribeEmbeddedPiSession
───────────────────────────────────
  이벤트 브릿지:
    pi tool events       → stream: "tool" (start/update/end)
    pi assistant deltas  → stream: "assistant" (텍스트 청크)
    pi lifecycle         → stream: "lifecycle" (start/end/error)
  
  버퍼링:
    deltaBuffer   — assistant 텍스트 누적
    blockBuffer   — 블록 스트리밍용 버퍼
    인라인 코드 상태 추적
  
  미디어:
    내부 이벤트에서 미디어 URL 수집
    응답에 소비

Phase 4: 정리
─────────────
  → 세션 트랜스크립트에 결과 기록 (JSONL)
  → 세션 메타데이터 업데이트
  → lifecycle end/error 이벤트 방출
```

### 2.3 글로벌 싱글톤 패턴

**Source**: `src/agents/pi-embedded-runner/runs.ts:51-74`

번들러가 모듈을 여러 번 복사해도 상태가 일관되도록 `Symbol.for` 사용:

```typescript
// 글로벌 상태 (프로세스 전체에서 단일 인스턴스)
const state = globalThis[Symbol.for("openclaw.embeddedRunState")] ??= {
  activeRuns: new Map(),          // runId → RunState
  snapshots: new Map(),           // 스냅샷 캐시
  sessionIdsByKey: new Map(),     // sessionKey → sessionId
  waiters: new Set(),             // 완료 대기 프로미스
  modelSwitchRequests: new Map(), // 모델 전환 요청
};
```

**Decepticon 적용**: Python에서는 모듈 레벨 싱글톤이면 충분하지만, 멀티프로세스 환경에서는 Redis/SQLite 공유 상태가 필요할 수 있음.

## 3. Prompt Assembly (프롬프트 조립)

### 3.1 시스템 프롬프트 구성

**Source**: `src/agents/pi-embedded-runner/system-prompt.ts`

```
시스템 프롬프트 = Base Prompt + Skills Prompt + Bootstrap Context

┌─────────────────────────────────────────────┐
│ Base Prompt                                  │
│ (OpenClaw 핵심 지침: 도구 사용법, 보안 규칙) │
├─────────────────────────────────────────────┤
│ Skills Prompt                                │
│ (활성 스킬 frontmatter 목록: 이름 + 설명)    │
│ (최대 150개, 30000자 제한)                   │
│ (경로 ~/ 축약으로 토큰 절약)                 │
├─────────────────────────────────────────────┤
│ Bootstrap Context                            │
│ ├── AGENTS.md  (운영 지침 + 메모리)          │
│ ├── SOUL.md    (페르소나, 경계, 톤)          │
│ ├── TOOLS.md   (도구 사용 노트)              │
│ ├── IDENTITY.md (이름, 바이브, 이모지)       │
│ ├── USER.md    (사용자 프로파일)             │
│ └── BOOTSTRAP.md (첫 실행 리추얼, 1회용)     │
├─────────────────────────────────────────────┤
│ Per-Run Overrides                            │
│ (모델별 제한, 압축 예비 토큰)                │
│ (플러그인 훅 주입: prependContext,           │
│  systemPrompt, appendSystemContext)          │
└─────────────────────────────────────────────┘
```

### 3.2 Bootstrap Files 상세

| File | 용도 | 첫 턴 주입 | Decepticon 대응 |
|------|------|-----------|----------------|
| `AGENTS.md` | 운영 지침 + 학습된 패턴 | Yes | `skills/` 디렉토리 |
| `SOUL.md` | 페르소나, 윤리 경계, 톤 | Yes | 에이전트 시스템 프롬프트 |
| `TOOLS.md` | 도구별 사용 노트 | Yes | 도구 사용 가이드라인 |
| `IDENTITY.md` | 에이전트 이름/성격 | Yes | 에이전트 페르소나 |
| `USER.md` | 사용자 선호/프로파일 | Yes | 운영자 프로파일 |
| `BOOTSTRAP.md` | 첫 실행 설정 (1회용) | Once | 인게이지먼트 초기 설정 |

**빈 파일은 건너뜀**. 큰 파일은 트림 + 트렁케이트 마커 표시.

### 3.3 프롬프트 캐시 안정성

**Source**: `AGENTS.md` (Prompt Cache Stability 섹션)

OpenClaw은 프롬프트 캐시를 **정확성/성능 critical**로 취급:

```
규칙:
1. 모델/도구 페이로드는 maps/sets/registries에서 조립 시
   결정론적 순서 보장 필요
2. 오래된 transcript/history 바이트를 매 턴 재작성하면 안됨
   (캐시된 prefix 무효화)
3. truncation/compaction이 필요하면 최신/꼬리 콘텐츠를 먼저 변경
   (캐시된 prefix를 최대한 유지)
4. 캐시 민감 변경은 turn-to-turn prefix 안정성 회귀 테스트 필요
```

**Decepticon 적용**: LiteLLM의 Anthropic prompt caching 기능과 결합하여 비용 절감 가능

## 4. Model Resolution Pipeline

### 4.1 해석 순서

```
1. 설정에서 모델 읽기
   → agents.defaults.model.primary (예: "anthropic/claude-opus-4-6")
   
2. Provider / Model 분할
   → 첫 번째 '/' 기준 분할
   → provider: "anthropic"
   → model: "claude-opus-4-6"
   
3. Provider 별칭 확인
   → alias 맵에서 정규 provider 이름 해석
   
4. Auth 프로파일 선택
   → ~/.openclaw/agents/<agentId>/agent/auth-profiles.json
   → 해당 provider의 프로파일 로딩
   → OAuth 토큰 만료 시 자동 갱신
   
5. Fallback 체인
   → primary 실패 → agents.defaults.model.fallback
   → fallback 실패 → first configured provider/model
   → 프로바이더가 default model을 더 이상 노출 안하면
     → first configured provider/model로 최종 폴백
   
6. Per-model 파라미터 오버라이드
   → agents.defaults.models["anthropic/claude-opus-4-6"].params
   → thinking, fastMode, temperature, etc.
```

### 4.2 플러그인 훅 개입

```
before_model_resolve 훅:
  → 세션 시작 전 (messages 없음)
  → provider/model 결정론적 오버라이드 가능
  → 용도: A/B 테스트, 비용 라우팅, 시간대별 모델 변경

before_prompt_build 훅:
  → 세션 로드 후 (messages 있음)
  → prependContext: 동적 텍스트 주입 (매 턴)
  → systemPrompt: 시스템 프롬프트 오버라이드
  → prependSystemContext: 시스템 컨텍스트 앞에 추가
  → appendSystemContext: 시스템 컨텍스트 뒤에 추가
```

### 4.3 Decepticon 대응

```
Decepticon 현재:
  LLMFactory → LiteLLM 프록시 → provider 라우팅
  ModelProfile (ECO/MAX/TEST) → primary + fallback

OpenClaw에서 배울 것:
  1. per-agent auth 프로파일 (에이전트별 다른 API 키)
  2. OAuth 자동 갱신 (장시간 실행 시 중요)
  3. 플러그인 훅으로 모델 라우팅 결정 (비용/성능 최적화)
  4. Alias 시스템 (openrouter/anthropic/claude 같은 복합 경로)
```

## 5. Tool Result Pruning (도구 결과 가지치기)

### 5.1 알고리즘

**Source**: `src/agents/pi-embedded-runner/tool-result-truncation.ts`

매 LLM 호출 전에 **오래된 도구 결과를 인메모리에서 정리**한다:

```
Pruning Flow:

1. 세션 히스토리의 모든 도구 결과를 역순으로 스캔
    ↓
2. 최근 N개는 보존 (TTL 기반)
    ↓
3. 오래된 결과에 Soft-trim 적용:
   ├── 결과의 head (앞부분) 유지
   ├── 결과의 tail (뒷부분) 유지
   └── 중간에 "... [truncated] ..." 삽입
    ↓
4. 더 오래된 결과에 Hard-clear 적용:
   └── 전체 결과를 "[tool output cleared]"로 대체
    ↓
5. TTL 리셋 (캐시 효율을 위해)
```

### 5.2 Soft-trim vs Hard-clear

| 방식 | 적용 대상 | 동작 | 결과 |
|------|----------|------|------|
| **Soft-trim** | 중간 오래된 결과 | head + tail 유지, 중간 트렁케이트 | 60% head + 40% tail (Decepticon과 동일!) |
| **Hard-clear** | 가장 오래된 결과 | 전체 제거 | `[tool output cleared]` |

### 5.3 핵심 특성

- **인메모리만 변경** — 디스크 트랜스크립트는 원본 유지
- **Anthropic 프로파일에서 기본 활성화**
- **TTL 리셋**: pruning 후 TTL을 리셋하여 프롬프트 캐시 prefix 안정성 유지
- **이미지 페이로드 특수 처리**: 크기 제한 + 제거

### 5.4 Decepticon과의 비교

```
Decepticon (현재):
  SummarizationMiddleware → 60% head + 40% tail 트렁케이션
  OutputOffloadMiddleware → 15K자 초과 시 .scratch 파일로 오프로드
  
OpenClaw:
  tool-result-truncation.ts → soft-trim (head+tail) + hard-clear
  
공통점: head + tail 유지, 중간 제거 (동일 전략!)
차이점: OpenClaw은 TTL 기반 다단계 (soft → hard), Decepticon은 크기 기반
개선 기회: TTL 기반 다단계 정리를 Decepticon에 도입
```

## 6. Compaction Lifecycle (압축 라이프사이클)

### 6.1 트리거 조건

```
자동 압축 트리거:
  1. 세션이 모델 context window에 근접
  2. 모델이 context-overflow 에러 반환:
     - "request_too_large"
     - "context length exceeded"
     - "input exceeds maximum tokens"
     - "input is too long for the model"
     - "ollama error: context length exceeded"
  3. 수동: /compact 명령
```

### 6.2 압축 파이프라인

```
Compaction Pipeline:

1. Pre-compaction 훅 (before_compaction)
    ↓
2. 에이전트에 메모리 저장 리마인드
   "Important notes를 memory files에 저장하세요"
    ↓
3. 히스토리를 청크로 분할
   ├── tool call + toolResult 쌍은 분리 안함
   ├── 분할점이 tool block 내부면 → 경계 이동
   └── 최근 unsummarized tail은 보존
    ↓
4. 오래된 청크를 LLM으로 요약
   ├── 기본: 에이전트의 primary model 사용
   ├── 오버라이드: agents.defaults.compaction.model
   ├── 또는 플러그인: registerCompactionProvider()
   └── identifierPolicy: "strict" (불투명 식별자 보존)
    ↓
5. 요약을 세션 트랜스크립트에 저장
    ↓
6. 최근 메시지는 그대로 유지
    ↓
7. Post-compaction 훅 (after_compaction)
    ↓
8. 원래 요청 재시도 (압축된 컨텍스트로)
   ├── 인메모리 버퍼 리셋 (중복 방지)
   └── tool summaries 리셋
```

### 6.3 압축 설정

```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard",           // auto | safeguard | off
        "model": "anthropic/claude-sonnet-4-6",  // 압축 전용 모델
        "identifierPolicy": "strict",  // 식별자 보존
        "provider": "my-provider"      // 커스텀 압축 프로바이더
      }
    }
  }
}
```

### 6.4 Pluggable Compaction

```typescript
// 커스텀 압축 프로바이더 등록
api.registerCompactionProvider({
  id: "my-compaction",
  compact: async (messages, instructions) => {
    // 커스텀 요약 로직
    return { summary: "..." };
  }
});
```

### 6.5 Decepticon 적용

```
현재 Decepticon:
  - SummarizationMiddleware: observation masking (이전 출력 요약으로 대체)
  - Fresh agent per iteration (컨텍스트 오염 방지)

OpenClaw에서 배울 것:
  1. 다단계 압축 (pruning → compaction → retry)
  2. Tool call/result 쌍 보존 (분할 시 쌍 유지)
  3. 식별자 보존 정책 (IP, 포트, CVE 번호 등 보존)
  4. 압축 전 메모리 저장 리마인드 (증거 손실 방지!)
  5. 별도 압축 모델 지정 (비용 최적화: 작은 모델로 요약)
```

## 7. Context Engine Registry

### 7.1 플러거블 컨텍스트 백엔드

**Source**: `src/context-engine/index.ts`

```typescript
// Registry 패턴
registerContextEngine(engine: ContextEngine): void;
resolveContextEngine(): ContextEngine;
ensureContextEnginesInitialized(): void;

// Delegate mode
delegateCompactionToRuntime(): void;

// Legacy support
class LegacyContextEngine implements ContextEngine { ... }
```

**구조**:
```
Context Engine Registry
  ├── registerContextEngine() — 플러거블 백엔드 등록
  ├── resolveContextEngine() — 현재 활성 엔진 반환
  ├── delegateCompactionToRuntime() — 런타임에 위임
  └── LegacyContextEngine — 하위 호환
```

### 7.2 Context Management 레이어 체계

```
Layer 1: Prompt Assembly (정적)
  → system-prompt.ts
  → 베이스 프롬프트 + 스킬 + 부트스트랩
  → 모델별 토큰 제한 적용
  → 압축 예비 토큰 할당

Layer 2: Tool Result Pruning (동적, 인메모리)
  → tool-result-truncation.ts
  → 오래된 도구 결과 soft-trim / hard-clear
  → 디스크 트랜스크립트 미변경
  → TTL 기반

Layer 3: Compaction (적응형)
  → compact.ts
  → context window 근접 시 자동 트리거
  → LLM으로 오래된 대화 요약
  → 트랜스크립트에 요약 저장

Layer 4: Context Engine (플러거블)
  → context-engine/index.ts
  → 커스텀 컨텍스트 관리 백엔드
  → 플러그인이 등록 가능
```

## 8. Streaming Protocol

### 8.1 스트림 유형

**Source**: `src/agents/pi-embedded-subscribe.ts`

```
3가지 스트림 채널:

1. lifecycle 스트림
   ├── phase: "start"  — 에이전트 실행 시작
   ├── phase: "end"    — 정상 완료
   └── phase: "error"  — 에러 발생

2. assistant 스트림
   ├── delta: "partial text..."  — 텍스트 청크 (스트리밍)
   ├── reasoning: "thinking..."  — 추론 과정 (별도 또는 블록)
   └── (미디어 URL 수집)

3. tool 스트림
   ├── status: "start"   — 도구 호출 시작 (이름, 입력)
   ├── status: "update"  — 중간 업데이트 (진행률)
   └── status: "end"     — 도구 완료 (결과)
```

### 8.2 Block Streaming

```
Block streaming = 완성된 assistant block을 즉시 전송

설정:
  blockStreamingDefault: "off" (기본값)
  blockStreamingBreak: "text_end" | "message_end"
  blockStreamingChunk: 800-1200자 (단락 > 줄바꿈 > 문장 경계)
  blockStreamingCoalesce: idle 기반 병합 (단일 줄 스팸 방지)

Decepticon 적용:
  Discord로 레드팀 진행 상황 실시간 보고 시
  block streaming으로 의미 있는 단위로 전송 가능
```

### 8.3 이벤트 구독 상태

```typescript
type EmbeddedPiSubscribeState = {
  deltaBuffer: string;      // assistant 텍스트 누적 버퍼
  blockBuffer: string;      // 블록 스트리밍 버퍼
  inlineCodeState: {        // 인라인 코드 추적
    inBlock: boolean;
    language?: string;
  };
  mediaUrls: string[];      // 수집된 미디어 URL
  toolEvents: Map<string, ToolEvent>;  // 활성 도구 이벤트
};
```

## 9. Session Management 심층

### 9.1 세션 저장소 구조

```
~/.openclaw/agents/<agentId>/sessions/
  ├── sessions.json           # 세션 인덱스
  │   [
  │     {
  │       "sessionId": "uuid",
  │       "sessionKey": "agent:main:main",
  │       "updatedAt": "2026-04-10T...",
  │       "contextTokens": 45000,
  │       "runtimeModel": "anthropic/claude-opus-4-6",
  │       "systemPromptReport": { ... },
  │       "abortedLastRun": false
  │     }
  │   ]
  └── <sessionId>.jsonl       # 메시지 트랜스크립트
      {"role":"system","content":"..."}
      {"role":"user","content":"..."}
      {"role":"assistant","content":"...","tool_calls":[...]}
      {"role":"tool","content":"...","tool_call_id":"..."}
      {"type":"compaction","summary":"..."}
```

### 9.2 세션 라이프사이클

```
생성:
  → 첫 메시지 수신 시 자동 생성
  → sessionId: UUID 할당
  → sessionKey: routing에 의해 결정

리셋 트리거:
  → Daily reset: 04:00 로컬 시간 (기본)
  → Idle reset: session.reset.idleMinutes
  → 수동: /new 또는 /reset
  → 모델 전환: /new <model>
  → (둘 다 설정 시: 먼저 만료되는 것 적용)

유지보수:
  → pruneAfter: 30일 (기본)
  → maxEntries: 500 (기본)
  → mode: "warn" (기본) → "enforce"로 변경하여 자동 정리
```

### 9.3 Write Lock

```
에이전트 실행 전:
  → 세션 write lock 획득
  → SessionManager open + prepare
  → 스트리밍 중 lock 유지
  → 완료/에러 시 lock 해제

의미:
  → 같은 세션에 동시 쓰기 불가 (일관성)
  → queue lane과 결합하여 순차 실행 보장
```

## 10. Subagent & ACP Spawn

### 10.1 sessions_spawn 도구

```typescript
sessions_spawn(
  task: string,
  runtime: "subagent" | "acp",
  mode?: "run" | "session",
  thread?: boolean,
  label?: string,
  cwd?: string,
  model?: string,
  sandbox?: "inherit" | "require",
  resumeSessionId?: string,
  streamTo?: "parent"
)
```

### 10.2 Subagent vs ACP

| | Subagent | ACP |
|--|---------|-----|
| 실행 위치 | OpenClaw 내부 | 외부 프로세스 |
| 컨텍스트 | 새 Pi 세션 | Claude Code/Codex CLI |
| 세션 키 | `subagent:<spawnId>` | `acp:<uuid>` |
| 모델 | OpenClaw 설정 | 외부 CLI 설정 |
| Depth 제한 | `MAX_SPAWN_DEPTH` | — |

### 10.3 subagents 제어 도구

```typescript
subagents(
  action: "list" | "kill" | "steer",
  target?: "all" | "<sessionId>",
  message?: string,           // steer 시 주입할 메시지
  recentMinutes?: number      // list 필터
)
```

## 11. Decepticon 에이전트 런타임 개선 로드맵

### 11.1 직접 적용 가능한 OpenClaw 패턴

| 패턴 | 현재 Decepticon | 개선 |
|------|----------------|------|
| TTL 기반 pruning | 크기 기반 트렁케이션 | 시간 기반 다단계 정리 |
| 압축 전 메모리 저장 | — | findings.txt 자동 업데이트 리마인드 |
| tool call/result 쌍 보존 | — | bash 명령+결과 쌍 보존 |
| Write lock | — | 같은 sandbox에 동시 접근 방지 |
| 별도 압축 모델 | — | 요약에 Haiku, 실행에 Opus |
| Bootstrap files | skills/ | AGENTS.md 패턴 도입 (코드베이스 패턴 축적) |
| Block streaming | StreamingRunnable | 의미 있는 단위로 Discord 보고 |

### 11.2 구현 우선순위

```
Phase 1: Context 관리 개선
  → TTL 기반 pruning 도입
  → 압축 전 findings 저장 리마인드
  → tool/result 쌍 보존

Phase 2: 세션 관리
  → Write lock 도입 (병렬 sandbox 접근 방지)
  → 세션 자동 유지보수 (pruneAfter, maxEntries)
  
Phase 3: 스트리밍 강화
  → Block streaming (Discord 보고용)
  → 도구 이벤트 구조화 (start/update/end)
  
Phase 4: Bootstrap 패턴
  → AGENTS.md 자동 업데이트 (학습된 패턴)
  → progress.txt 통합 (Ralph loop)
```
