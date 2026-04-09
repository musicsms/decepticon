# Coding Agent & Harness Integration

## 1. Coding Agent Skill

### 1.1 개요

OpenClaw의 `coding-agent` 스킬은 **외부 코딩 에이전트를 스폰하고 관리하는 오케스트레이터**이다. Claude Code, Codex, OpenCode, Pi 등 다양한 코딩 CLI 도구를 백그라운드에서 실행할 수 있다.

**위치**: `skills/coding-agent/SKILL.md`

### 1.2 지원 에이전트

| Agent | CLI | PTY 필요 | 실행 예시 |
|-------|-----|---------|----------|
| Claude Code | `claude` | No | `claude --permission-mode bypassPermissions --print "task"` |
| Codex | `codex` | Yes | `codex exec "task"` |
| OpenCode | `opencode` | Yes | `opencode "task"` |
| Pi | `pi` | Yes | Pi coding agent |

### 1.3 실행 모드

```bash
# Claude Code (PTY 불필요 — 가장 간단)
bash workdir:~/project background:true \
  command:"claude --permission-mode bypassPermissions --print 'Implement OAuth2 auth'"

# Codex (PTY 필요)
bash pty:true workdir:~/project background:true \
  command:"codex exec 'Build user dashboard'"

# OpenCode (PTY 필요)
bash pty:true workdir:~/project background:true \
  command:"opencode 'Fix the login bug'"
```

### 1.4 프로세스 관리 도구

| Command | Description |
|---------|-------------|
| `process action:list` | 실행 중 세션 목록 |
| `process action:log sessionId:XXX` | 진행 상황 모니터링 |
| `process action:write sessionId:XXX data:"y"` | 입력 전송 |
| `process action:submit sessionId:XXX data:"yes"` | 입력 + Enter |
| `process action:kill sessionId:XXX` | 세션 종료 |

## 2. Subagent & ACP Spawn

### 2.1 sessions_spawn 도구

`sessions_spawn`은 **코딩 에이전트 스폰의 핵심 진입점**이다.

```
src/agents/tools/sessions-spawn-tool.ts    # 도구 정의
src/agents/subagent-spawn.ts (915 LOC)     # 내부 서브에이전트 스폰
src/agents/acp-spawn.ts (1235 LOC)         # 외부 ACP 하네스 스폰
```

### 2.2 두 가지 런타임

**Runtime: "subagent"** — OpenClaw 내부 에이전트 스폰

```typescript
sessions_spawn(
  task: "Implement feature X",
  runtime: "subagent",
  mode: "run" | "session",  // 일회성 vs 지속성
  label?: "feature-x",
  cwd?: "/workspace",
  model?: "claude-sonnet-4-20250514"
)
// → { childSessionKey, runId, status }
```

**Runtime: "acp"** — 외부 하네스 스폰 (Claude Code, Codex, OpenCode)

```typescript
sessions_spawn(
  task: "Build OAuth2 flow",
  runtime: "acp",
  resumeSessionId?: "...",    // 기존 세션 재개
  streamTo: "parent"?,        // 부모에게 스트리밍
  model?: "gpt-5.3-codex"
)
// → ACP 세션이 Gateway 세션 키에 매핑
```

### 2.3 세션 모드

| Mode | 동작 | 용도 |
|------|------|------|
| `run` | 일회성 실행, 완료 시 종료 | 단일 태스크 |
| `session` | 지속 세션, 후속 메시지 가능 | 대화형 작업 |
| `thread:true` | 스레드 바인딩 세션 자동 생성 | Discord 스레드 |

## 3. ACP (Agent Client Protocol)

### 3.1 ACP 브릿지

```
src/acp/                              # 368 파일
  ├── channel-bridge.ts (450+ LOC)    # 메인 브릿지
  ├── channel-server.ts               # MCP 서버 인스턴스
  ├── channel-tools.ts                # 도구 등록
  └── plugin-tools-serve.ts           # 플러그인 도구 서빙
```

OpenClaw은 **ACP 서버**로서 IDE/하네스의 프롬프트를 Gateway 세션에 매핑:

```bash
# ACP 브릿지 실행 (stdio 인터페이스)
openclaw acp --url wss://gateway-host:18789 --token <token>

# 특정 에이전트 스코프에 매핑
openclaw acp --session agent:main:main
```

### 3.2 ACP 세션 매핑

| 형식 | 설명 |
|------|------|
| `acp:<uuid>` | ACP 클라이언트별 격리 (기본) |
| `agent:main:main` | 에이전트 메인 세션에 매핑 |
| `agent:design:feature-X` | 커스텀 에이전트 스코프 |

### 3.3 ACP 호환성

- **지원**: `initialize`, `newSession`, `prompt`, `cancel`, `listSessions`
- **부분 지원**: `loadSession`, `tool_call` 스트리밍, 세션 모드
- **미지원**: per-session MCP, 클라이언트 파일시스템, ACP 터미널

## 4. Multi-Agent Orchestration

### 4.1 subagents 제어 도구

```typescript
subagents(
  action: "list" | "kill" | "steer",
  target?: "all" | "<sessionId>",
  message?: "Change direction to...",
  recentMinutes?: 30
)
```

| Action | 설명 |
|--------|------|
| `list` | 실행 중 서브에이전트 상태/시작 시간/세션 키 |
| `kill` | 특정 또는 전체 서브에이전트 종료 |
| `steer` | 실행 중 서브에이전트에 메시지 주입 (방향 전환) |

### 4.2 세션 키 레지스트리

- 부모-자식 세션 관계 추적
- 무한 스폰 방지 (`DEFAULT_SUBAGENT_MAX_SPAWN_DEPTH`)
- 완료 이벤트 자동 전파 (자식 → 부모)

## 5. Harness Integration: OMC (oh-my-claudecode)

### 5.1 OMC란?

oh-my-claudecode(OMC)는 Claude Code를 위한 **멀티 에이전트 오케스트레이션 레이어**이다. OpenClaw과 결합하면:

1. OpenClaw이 Discord에서 지시를 받아 coding-agent 스킬로 Claude Code 스폰
2. Claude Code가 OMC 하네스와 함께 실행
3. OMC가 내부적으로 전문 에이전트를 병렬 오케스트레이션
4. 완료 시 OpenClaw Gateway로 결과 전파

### 5.2 OpenClaw에서 OMC 활용 예시

```bash
# Discord에서 지시 → OpenClaw 에이전트가 실행:
bash workdir:~/project background:true \
  command:"claude --permission-mode bypassPermissions --print \
    '/oh-my-claudecode:autopilot Implement user auth with OAuth2. 
     Requirements: Google + GitHub OAuth, JWT tokens, refresh flow.
     When done, commit and push to feature/oauth branch.'"
```

### 5.3 OMC 핵심 워크플로우

| Workflow | 설명 |
|----------|------|
| `autopilot` | 아이디어 → 완성 코드까지 완전 자율 실행 |
| `ultrawork` | 모든 에이전트 병렬 스폰, 완료까지 멈추지 않음 |
| `ralph` | 자기 참조 루프, 100% 완료까지 반복 |
| `team` | N개 에이전트 공유 태스크 리스트 협업 |
| `ralplan` | 합의 기반 계획 → 실행 게이팅 |

## 6. Harness Integration: OMO (oh-my-opencode)

### 6.1 OMO란?

oh-my-opencode(OMO)는 OpenCode를 위한 하네스로, OMC와 유사한 멀티 에이전트 오케스트레이션을 제공한다.

**위치**: `reference/oh-my-opencode/`

### 6.2 OMO 핵심 컴포넌트

| Component | 역할 |
|-----------|------|
| Sisyphus | 오케스트레이터 (끝까지 반복) |
| Hephaestus | 딥 워커 (복잡한 구현) |
| Prometheus | 플래너 (계획 수립) |
| Oracle | 의사결정 |
| Librarian | 문서/참조 관리 |
| Explore | 코드베이스 탐색 |

### 6.3 OMO 고유 기능

- **Hash-Anchored Edit**: 콘텐츠 해시 기반 안정적 라인 참조 (하네스 문제 해결)
- **Background Agents**: 5+ 전문가 병렬 실행 (컨텍스트 블로트 없음)
- **46개 훅**: 37 코어 + 7 계속 + 2 스킬
- **Multi-Level Config**: 프로젝트 → 사용자 → 기본값 병합

## 7. Docker Sandbox

### 7.1 샌드박스 모드

```
src/agents/sandbox/     # 68 파일
Dockerfile.sandbox      # 기본 샌드박스 이미지
Dockerfile.sandbox-browser  # 브라우저 포함 샌드박스
docker-compose.yml      # 컴포즈 설정
```

| Mode | 설명 |
|------|------|
| `sandbox:"inherit"` | 부모 샌드박스 설정 상속 |
| `sandbox:"require"` | 반드시 샌드박스 내 실행 |

### 7.2 샌드박스 백엔드

| Backend | 설명 |
|---------|------|
| Docker | 격리 실행 (기본) |
| SSH | 원격 샌드박스 |
| File Bridge | 호스트-샌드박스 간 안전 파일 접근 |

## 8. Tmux Integration

### 8.1 tmux 스킬

`skills/tmux/SKILL.md`로 터미널 세션 관리:

```bash
# 세션 목록
tmux list-sessions

# 출력 캡처
tmux capture-pane -t shared -p | tail -20

# 에이전트에 입력 전송
tmux send-keys -t worker-3 'y' Enter

# 다중 워커 모니터링
for s in worker-2 worker-3 worker-4; do
  echo "=== $s ==="
  tmux capture-pane -t $s -p | tail -5
done
```

### 8.2 병렬 세션 구조

| Session | 용도 |
|---------|------|
| `shared` | 기본 대화형 세션 |
| `worker-2` ~ `worker-8` | 병렬 코딩 워커 |

이 구조를 통해 하나의 OpenClaw 인스턴스에서 **최대 7개의 코딩 에이전트를 동시 실행**할 수 있다.

## 9. Hooks System for Harness Integration

### 9.1 훅 기반 자동화

```
src/hooks/
  ├── loader.ts               # 훅 로딩/합성
  ├── install.ts              # 설치/검증
  ├── message-hook-mappers.ts # 메시지 이벤트 → 훅 트리거
  └── plugin-hooks.ts         # 플러그인 훅 와이어링
```

### 9.2 Fire-and-Forget 훅 예시

```jsonc
{
  "hooks": {
    "internal": {
      "entries": [
        {
          "name": "spawn-coding-agent-on-discord",
          "when": {
            "channel": "discord",
            "mentions": ["me"],
            "text_pattern": "^implement|^build|^fix"
          },
          "do": {
            "method": "sessions_spawn",
            "params": {
              "task": "{message_text}",
              "runtime": "acp",
              "thread": true,
              "model": "claude-sonnet-4-20250514",
              "cwd": "/workspace"
            }
          }
        }
      ]
    }
  }
}
```

이 설정으로 Discord에서 "implement", "build", "fix"로 시작하는 메시지가 봇을 멘션하면 자동으로 코딩 에이전트가 스폰된다.
