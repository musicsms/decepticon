# 개발 가재 키우기 셋업 가이드

> OpenClaw + OMC/OMO를 활용한 자율 개발 워크플로우 구축

## 1. 필요 조건

| 항목 | 요구사항 |
|------|---------|
| OS | macOS / Linux / WSL2 |
| Node.js | 24 (권장) 또는 22.16+ |
| LLM 구독 | Claude Pro/Max 또는 ChatGPT Plus/Codex |
| Discord | 봇 생성 가능한 계정 |
| 서버 | 24/7 실행 가능한 VPS (선택, 로컬도 가능) |

## 2. 설치

### 2.1 OpenClaw 설치

```bash
# npm 글로벌 설치
npm install -g openclaw@latest

# 온보딩 (데몬 설치 포함)
openclaw onboard --install-daemon
```

### 2.2 LLM 인증 설정

**옵션 A: Claude Pro/Max (구독 기반)**
```bash
# Claude CLI가 이미 설치되어 있어야 함
# OpenClaw이 Claude CLI 크리덴셜을 재사용
openclaw onboard --auth-choice anthropic
```

**옵션 B: ChatGPT Plus/Codex (OAuth)**
```bash
openclaw models auth login --provider openai-codex
# 브라우저에서 OpenAI 로그인 → 토큰 자동 발급
```

**옵션 C: API Key (가장 안정적)**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# 또는
export OPENAI_API_KEY="sk-..."
openclaw onboard
```

### 2.3 코딩 에이전트 설치

```bash
# Claude Code (OMC 포함 시)
npm install -g @anthropic-ai/claude-code

# Codex (선택)
npm install -g @openai/codex

# OpenCode + OMO (선택)
npm install -g opencode
```

## 3. Discord 봇 설정

### 3.1 Discord Developer Portal

1. https://discord.com/developers/applications 접속
2. **New Application** → 이름 입력 (예: "DevCrayfish")
3. **Bot** 탭 → **Add Bot**
4. **MESSAGE CONTENT INTENT** 활성화 (필수!)
5. **Bot Token** 복사
6. **OAuth2 → URL Generator**:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions: `Send Messages`, `Read Message History`, `Create Public Threads`
   - 생성된 URL로 서버에 봇 초대

### 3.2 OpenClaw Discord 설정

```bash
# 토큰 설정
export DISCORD_BOT_TOKEN="your-bot-token"

# Discord 채널 활성화
openclaw config set channels.discord.enabled true
openclaw config set channels.discord.token.source env
openclaw config set channels.discord.token.id DISCORD_BOT_TOKEN

# 길드 설정 (서버 ID 필요)
# 서버 ID: Discord > 서버 설정 > 위젯 > 서버 ID
openclaw config set channels.discord.guilds.YOUR_GUILD_ID.requireMention false
```

### 3.3 채널별 에이전트 바인딩 (선택)

```jsonc
// ~/.openclaw/config.json (수동 편집)
{
  "agents": {
    "list": [
      { "id": "main", "workspace": "~/.openclaw/workspace" },
      { "id": "coder", "workspace": "~/.openclaw/workspace-coding" }
    ]
  },
  "bindings": [
    {
      "match": { "channel": "discord", "guildId": "YOUR_GUILD_ID",
                 "peer": { "kind": "channel", "id": "CODING_CHANNEL_ID" } },
      "agentId": "coder"
    }
  ]
}
```

## 4. Gateway 실행

### 4.1 로컬 실행

```bash
openclaw gateway run --bind loopback --port 18789 --verbose
```

### 4.2 VPS 데몬 실행 (24/7)

```bash
# systemd 서비스로 자동 등록됨 (onboard --install-daemon)
# 또는 수동:
nohup openclaw gateway run --bind loopback --port 18789 --force \
  > /tmp/openclaw-gateway.log 2>&1 &

# 상태 확인
openclaw channels status --probe
```

## 5. 사용법

### 5.1 기본 사용

Discord에서:
```
@DevCrayfish implement a REST API for user management with CRUD endpoints
```

### 5.2 OMC autopilot으로 자율 실행

Discord에서:
```
@DevCrayfish use coding-agent to run claude code with autopilot mode:
"Implement user management API with:
- Express.js routes
- PostgreSQL with Prisma ORM  
- JWT authentication
- Input validation with Zod
- Unit tests with vitest
Commit to feature/user-api branch when done."
```

### 5.3 여러 작업 동시 실행

Discord 스레드를 각각 생성하여:
- 스레드 1: "Fix the login bug #123"
- 스레드 2: "Add dark mode to settings"
- 스레드 3: "Write API documentation"

→ 각 스레드가 독립 세션으로 병렬 실행

### 5.4 야간 자동화 (Cron)

```bash
# 매일 새벽 3시 의존성 체크
openclaw cron add \
  --name "dep-audit" \
  --schedule "0 3 * * *" \
  --tz "Asia/Seoul" \
  --isolated \
  --message "Audit npm dependencies for vulnerabilities. If critical, create fix PR." \
  --announce discord:CHANNEL_ID

# 매주 금요일 코드 리뷰
openclaw cron add \
  --name "weekly-review" \
  --schedule "0 18 * * 5" \
  --tz "Asia/Seoul" \
  --isolated \
  --message "Review this week's PRs and summarize code quality trends." \
  --announce discord:CHANNEL_ID
```

## 6. 모니터링

```bash
# 실행 중 에이전트 확인
openclaw sessions list

# 태스크 상태
openclaw tasks list

# Gateway 로그
tail -f /tmp/openclaw-gateway.log

# Discord에서
@DevCrayfish /status
```

## 7. 트러블슈팅

| 문제 | 해결 |
|------|------|
| 봇이 반응 안함 | `openclaw channels status --probe`로 연결 확인 |
| 토큰 만료 | `openclaw models auth login --provider <provider>` 재인증 |
| Gateway 크래시 | `openclaw doctor` 실행, 로그 확인 |
| 메모리 부족 | `session.reset.idleMinutes` 설정으로 세션 자동 리셋 |
