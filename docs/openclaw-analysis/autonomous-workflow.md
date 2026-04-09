# "가재 키우기" 자율 개발 워크플로우 가이드

> "가재"(Crayfish/Lobster)는 한국 개발자 커뮤니티에서 Claude Code, Codex 등 AI 코딩 에이전트를 부르는 별칭이다. OpenClaw의 마스코트가 가재(lobster)인 것과 맥이 통한다.

## 1. 개념 요약

"가재 키우기"란 **AI 코딩 에이전트를 자율적으로 운용하는 워크플로우**를 말한다:

1. 개발자가 **Discord에서 지시**를 내린다 (예: "OAuth2 인증 구현해")
2. OpenClaw Gateway가 메시지를 받아 **에이전트 세션에 라우팅**
3. 에이전트가 **코딩 하네스(OMC/OMO)를 스폰**하여 백그라운드 실행
4. 하네스가 **자율적으로 코드를 구현**, 테스트, 커밋
5. 개발자는 **자고 일어나면 완성된 코드**를 확인

```
 Developer                  OpenClaw                    Coding Agent
    |                          |                             |
    |  Discord: "implement X"  |                             |
    |------------------------->|                             |
    |                          |  route to agent session     |
    |                          |  spawn coding harness       |
    |                          |---------------------------->|
    |  "accepted, working..."  |                             |
    |<-------------------------|                             |
    |                          |                             |
    |        zzz (sleep)       |     autonomous execution    |
    |                          |     - explore codebase      |
    |                          |     - implement feature     |
    |                          |     - run tests             |
    |                          |     - git commit & push     |
    |                          |                             |
    |                          |  completion event           |
    |                          |<----------------------------|
    |  Discord: "Done! PR #42" |                             |
    |<-------------------------|                             |
    |                          |                             |
```

## 2. 이것이 가능한 이유 (아키텍처적 근거)

### 2.1 비동기 실행 모델

OpenClaw의 에이전트 실행은 **완전 비동기**이다:
- Gateway RPC는 `{runId, acceptedAt}`을 **즉시 반환**
- 에이전트는 백그라운드에서 독립 실행
- Discord 클라이언트는 연결을 유지할 필요 없음
- 결과는 **push 방식**으로 Discord에 전달 (polling 불필요)

### 2.2 세션 격리

각 작업은 **독립 세션**에서 실행된다:
- 스레드별 세션 키: `agent:main:discord:channel:123:thread:456`
- Subagent 세션: `subagent:<spawnId>`
- Cron 세션: `cron:<jobId>`
- 세션 간 컨텍스트 오염 없음

### 2.3 프로세스 지속성

- Gateway는 **항상 실행** (systemd/launchd 데몬)
- Docker 샌드박스 내 코딩 에이전트는 호스트와 독립
- tmux 세션으로 터미널 상태 유지
- 네트워크 끊김에도 실행 지속

### 2.4 에이전트 타임아웃

기본 타임아웃이 **48시간** (`172800s`)이므로 밤새 실행에 충분하다.

### 2.5 자동 완료 통보

- Task system이 완료/실패 상태 추적
- 완료 시 Discord 스레드에 결과 자동 전달
- `announce` 배달 모드로 요약 전송

## 3. 구체적 설정 가이드

### 3.1 기본 인프라 설정

```bash
# 1. OpenClaw 설치
npm install -g openclaw@latest
openclaw onboard --install-daemon

# 2. Discord 봇 생성 (Discord Developer Portal)
# - Bot 생성 → Token 복사
# - MESSAGE CONTENT INTENT 활성화
# - 서버에 봇 초대

# 3. Discord 채널 설정
openclaw config set channels.discord.enabled true
openclaw config set channels.discord.token.source env
openclaw config set channels.discord.token.id DISCORD_BOT_TOKEN
export DISCORD_BOT_TOKEN="your-bot-token"

# 4. 길드 설정 (requireMention: false → 모든 메시지에 반응)
openclaw config set channels.discord.guilds.YOUR_GUILD_ID.requireMention false

# 5. Gateway 시작
openclaw gateway run --bind loopback --port 18789
```

### 3.2 코딩 에이전트 설정

```bash
# Claude Code가 설치되어 있어야 함
which claude  # 확인

# 또는 Codex
which codex

# 작업 디렉토리 설정
mkdir -p ~/.openclaw/workspace
```

### 3.3 자율 실행을 위한 에이전트 설정

**`~/.openclaw/agents/main/AGENTS.md`** (에이전트 지시서):
```markdown
# Agent Instructions

You are a coding assistant that receives tasks via Discord.
When given a coding task:
1. Use the coding-agent skill to spawn Claude Code or Codex
2. Run the agent in background mode
3. Monitor progress and report back to Discord
4. On completion, summarize what was done

Always use background execution for long tasks.
Commit and push completed work automatically.
```

### 3.4 멀티 에이전트 설정 (고급)

```jsonc
{
  "agents": {
    "list": [
      { "id": "main", "workspace": "~/.openclaw/workspace" },
      { "id": "coder", "workspace": "~/.openclaw/workspace-coding" },
      { "id": "reviewer", "workspace": "~/.openclaw/workspace-review" }
    ]
  },
  "bindings": [
    // #coding 채널 → coder 에이전트
    { "match": { "channel": "discord", "guildId": "GUILD", "peer": { "kind": "channel", "id": "CODING_CH" } }, "agentId": "coder" },
    // #review 채널 → reviewer 에이전트
    { "match": { "channel": "discord", "guildId": "GUILD", "peer": { "kind": "channel", "id": "REVIEW_CH" } }, "agentId": "reviewer" },
    // 나머지 → main
    { "match": { "channel": "discord" }, "agentId": "main" }
  ]
}
```

## 4. 사용 시나리오

### 4.1 시나리오 A: Discord → Claude Code (OMC)

```
[Discord #coding]
개발자: @bot implement user authentication with OAuth2 
        - Google and GitHub providers
        - JWT token generation
        - Refresh token flow
        - Store in PostgreSQL

[OpenClaw Agent 내부 동작]
1. Discord 메시지 수신 → routing → coder 에이전트 세션
2. 에이전트가 coding-agent 스킬 활성화
3. sessions_spawn(runtime:"acp") 호출
4. Claude Code 프로세스 스폰:
   claude --permission-mode bypassPermissions --print \
     "/oh-my-claudecode:autopilot 
      Implement OAuth2 authentication:
      - Google + GitHub OAuth providers
      - JWT generation with RS256
      - Refresh token rotation
      - PostgreSQL persistence
      Commit to feature/oauth branch when done."

[백그라운드 실행 (개발자 수면 중)]
- OMC autopilot이 코드베이스 탐색
- 구현 계획 수립 (planner 에이전트)
- 병렬 구현 (executor 에이전트들)
- 테스트 작성 및 실행
- 코드 리뷰 (code-reviewer 에이전트)
- git commit & push

[Discord #coding - 다음 날 아침]
봇: Done! Implemented OAuth2 auth:
    - Created auth middleware (src/auth/)
    - Google + GitHub OAuth providers
    - JWT with RS256, refresh token rotation
    - PostgreSQL migration added
    - 23 tests passing
    PR: github.com/user/repo/pull/42
```

### 4.2 시나리오 B: 다중 세션 병렬 실행

```
[Discord #coding - 스레드 1]
개발자: @bot fix the login timeout bug in #1234

[Discord #coding - 스레드 2]  
개발자: @bot add dark mode toggle to settings page

[Discord #coding - 스레드 3]
개발자: @bot refactor the payment module to use Stripe SDK v3

→ 각 스레드가 독립 세션으로 매핑
→ 3개의 코딩 에이전트가 동시 실행
→ 각 스레드에 독립적으로 결과 보고
```

### 4.3 시나리오 C: Cron으로 야간 자동화

```bash
# 매일 새벽 2시에 의존성 업데이트 확인
openclaw cron add \
  --name "dep-check" \
  --schedule "0 2 * * *" \
  --tz "Asia/Seoul" \
  --isolated \
  --message "Check all npm dependencies for updates and security vulnerabilities. 
             If critical updates found, create a PR with the updates." \
  --announce discord:CHANNEL_ID

# 매주 월요일 오전 9시에 코드 품질 리포트
openclaw cron add \
  --name "quality-report" \
  --schedule "0 9 * * 1" \
  --tz "Asia/Seoul" \
  --isolated \
  --message "Run full code quality analysis: lint, type check, test coverage, 
             dead code detection. Summarize findings and trends." \
  --announce discord:CHANNEL_ID
```

### 4.4 시나리오 D: 실행 중 방향 전환 (Steering)

```
[Discord 스레드]
개발자: @bot implement the user profile page
봇: Working on it... (스폰됨)

[30분 후]
개발자: @bot actually, add avatar upload too with S3 integration

→ steer 모드에서 새 메시지가 실행 중 에이전트에 주입
→ 에이전트가 추가 요구사항을 반영하여 계속 구현
```

## 5. 모니터링 & 관리

### 5.1 실행 상태 확인

```bash
# 실행 중 세션 목록
openclaw sessions list

# 특정 세션 히스토리
openclaw sessions history <sessionKey>

# 태스크 상태
openclaw tasks list
openclaw tasks status <taskId>
```

### 5.2 Discord에서 제어

```
@bot /status          → 현재 실행 중인 에이전트 상태
@bot /stop            → 현재 에이전트 실행 중단
@bot /new             → 세션 리셋
@bot /new claude-opus-4-20250514  → 모델 전환
```

### 5.3 tmux로 직접 모니터링

```bash
# SSH로 서버 접속 후
tmux list-sessions

# 워커 출력 확인
tmux capture-pane -t worker-2 -p | tail -30

# 워커에 입력 전송 (필요시)
tmux send-keys -t worker-2 'y' Enter
```

## 6. 핵심 아키텍처 컴포넌트 매핑

아래는 "가재 키우기" 워크플로우에서 각 단계에 관여하는 OpenClaw 컴포넌트:

```
Step 1: Discord 메시지 수신
  └─ extensions/discord/src/monitor/provider.ts
  └─ extensions/discord/src/monitor/message-handler.preflight.ts

Step 2: 라우팅 & 세션 할당
  └─ src/routing/resolve-route.ts
  └─ src/routing/session-key.ts

Step 3: 에이전트 실행
  └─ src/agents/pi-embedded-runner/run.ts
  └─ src/agents/agent-command.ts

Step 4: 코딩 에이전트 스폰
  └─ src/agents/tools/sessions-spawn-tool.ts
  └─ src/agents/acp-spawn.ts (ACP runtime)
  └─ src/agents/subagent-spawn.ts (subagent runtime)
  └─ skills/coding-agent/SKILL.md

Step 5: 자율 실행 (하네스)
  └─ Claude Code + OMC (oh-my-claudecode)
  └─ Codex + custom config
  └─ OpenCode + OMO (oh-my-opencode)

Step 6: 병렬 세션 관리
  └─ src/agents/tools/subagents-tool.ts
  └─ skills/tmux/SKILL.md

Step 7: 완료 & 통보
  └─ src/tasks/task-registry.ts
  └─ src/auto-reply/ (reply pipeline)
  └─ extensions/discord/src/send.js
```

## 7. Decepticon Ralph Loop과의 비교

| Aspect | Decepticon Ralph | OpenClaw "가재 키우기" |
|--------|-----------------|----------------------|
| **트리거** | CLI에서 수동 시작 | Discord 메시지 / Cron |
| **계획** | opplan.json (사전 정의) | 에이전트 자율 판단 + 하네스 플래너 |
| **실행** | 목표별 fresh agent 스폰 | sessions_spawn + ACP/subagent |
| **격리** | Docker Kali sandbox | Docker sandbox / SSH sandbox |
| **상태 전파** | findings.txt (파일) | Gateway events + Task system |
| **결과 보고** | CLI 출력 | Discord/Telegram/Slack 자동 전달 |
| **컨텍스트** | Fresh per iteration | Compaction + pruning |
| **병렬성** | 순차 (목표별) | 다중 세션 동시 실행 |
| **조향** | 없음 (자율) | steer 모드 (실행 중 방향 전환) |

## 8. 주의사항

### 8.1 보안

- `--permission-mode bypassPermissions`는 Claude Code의 모든 권한을 허용 — 신뢰할 수 있는 환경에서만 사용
- Docker sandbox 활용 권장 (호스트 파일시스템 격리)
- Discord 봇의 allowlist를 반드시 설정 (무단 접근 방지)
- 민감 정보(API 키 등)는 환경변수로 관리

### 8.2 비용

- 장시간 자율 실행은 LLM API 비용이 누적됨
- OAuth 모드(Claude Pro/Max 등)를 활용하면 API 키 비용 절감 가능
- 모델 선택 최적화: 단순 작업은 Sonnet/Haiku, 복잡한 작업은 Opus

### 8.3 안정성

- Gateway 데몬이 중단되면 모든 세션 영향 — systemd 재시작 설정 권장
- 네트워크 불안정 시 Discord 메시지 누락 가능 — 디바운싱/dedupe로 완화
- 48시간 타임아웃 초과 시 에이전트 강제 종료

### 8.4 Korean Community Tips

- **VPS 활용**: 한국 시간대(KST)에 맞춰 AWS/GCP Seoul 리전에 OpenClaw 배포
- **exe.dev**: OpenClaw 팀이 제공하는 호스팅 VM 활용 가능
- **여러 프로젝트**: 에이전트별 workspace 분리로 다중 프로젝트 동시 관리
- **Discord 서버 구조**: `#coding`, `#review`, `#deploy` 등 채널별 에이전트 바인딩 추천
