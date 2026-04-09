# 해킹 가재 (Hacking Crayfish) 변환 아키텍처

> OpenClaw의 핵심 아키텍처("Juice")를 추출하여 Decepticon으로 변환하는 설계 문서

## 1. Executive Summary

**목표**: Decepticon 2.0을 "해킹 가재" 플랫폼으로 진화시킨다.
Discord에서 레드팀 지시를 내리면, 밤새 자율적으로 정찰/익스플로잇/보고를 수행하고,
아침에 결과를 받아볼 수 있는 시스템.

**핵심 추출 대상 (OpenClaw Juice)**:

| OpenClaw Component | Decepticon 적용 |
|-------------------|----------------|
| Gateway Control Plane | **RedGate** — 레드팀 제어 평면 |
| Discord Channel Plugin | **Discord 지시 채널** |
| sessions_spawn / ACP | **에이전트 스폰 매니저** |
| Cron Service | **야간 자동 스캔 스케줄러** |
| Task Registry | **목표(Objective) 진행 추적** |
| Plugin SDK | **공격 모듈 플러그인 시스템** |
| Hooks Engine | **OPSEC 가드레일 훅** |

## 2. 현재 Decepticon vs 목표 상태

### 2.1 현재 상태 (AS-IS)

```
                    Developer (CLI only)
                          |
                          v
                    +----------+
                    | Ink CLI  |
                    +----------+
                          |
                          v
                  +---------------+
                  | LangGraph     |
                  | Dev Server    |
                  +---------------+
                          |
              +-----------+-----------+
              v                       v
        +-----------+         +-------------+
        | Decepticon|         | Ralph Loop  |
        | Agent     |         | (sequential)|
        +-----------+         +-------------+
              |                       |
              v                       v
        +-----------+         +-------------+
        | Docker    |         | opplan.json |
        | Kali      |         | findings.txt|
        | Sandbox   |         +-------------+
        +-----------+
```

**한계**:
- CLI에서만 접근 가능
- 순차 실행 (목표별 1개 에이전트)
- 스케줄링 없음 (수동 시작)
- 결과 보고가 파일 기반
- 실행 중 조향 불가

### 2.2 목표 상태 (TO-BE): 해킹 가재

```
                Developer (Discord / Telegram / CLI)
                              |
                              v
                +----------------------------+
                |        RedGate             |
                |   (WS Control Plane)       |
                |                            |
                | +--------+ +------------+  |
                | |Routing | |Session Mgr |  |
                | +--------+ +------------+  |
                | +--------+ +------------+  |
                | |Plugins | |OPSEC Hooks |  |
                | +--------+ +------------+  |
                +----------------------------+
                    |          |          |
            +-------+    +----+----+    +-------+
            v            v         v            v
      +---------+  +---------+ +---------+ +--------+
      | Recon   |  | Exploit | | Post-   | | Cron   |
      | Agent   |  | Agent   | | Exploit | | Sched  |
      | Pool    |  | Pool    | | Agent   | +--------+
      +---------+  +---------+ +---------+
            |            |         |
            +------+-----+---------+
                   v
            +-------------+
            | Docker Kali |  x N (parallel sandboxes)
            | Sandbox Pool|
            +-------------+
                   |
                   v
            +-------------+
            | Knowledge   |
            | Graph (Neo4j)|
            +-------------+
                   |
                   v
            +------------------+
            | Auto Reporter    |
            | (HackerOne/      |
            |  Bugcrowd/Exec)  |
            +------------------+
```

## 3. 추출해야 할 OpenClaw Juice

### 3.1 Juice #1: Gateway Control Plane → RedGate

**OpenClaw 원본**: `src/gateway/` — WebSocket JSON-RPC 멀티플렉스 서버

**Decepticon 적용: RedGate**

```python
# decepticon/gateway/redgate.py (신규)

class RedGate:
    """
    Red team 제어 평면.
    WebSocket JSON-RPC로 Discord/CLI/Web에서 접근 가능.
    """
    
    def __init__(self, config: RedGateConfig):
        self.router = EngagementRouter()      # OpenClaw routing 패턴
        self.session_mgr = SessionManager()   # 세션 격리
        self.task_registry = TaskRegistry()    # 목표 추적
        self.hook_engine = OPSECHookEngine()  # OPSEC 가드레일
        self.cron = ScanScheduler()           # 스캔 스케줄러
    
    async def handle_rpc(self, method, params):
        match method:
            case "engagement.start":    # 인게이지먼트 시작
            case "objective.assign":    # 목표 할당
            case "agent.spawn":         # 에이전트 스폰
            case "agent.steer":         # 실행 중 조향
            case "agent.status":        # 상태 조회
            case "scan.schedule":       # 스캔 예약
            case "report.generate":     # 보고서 생성
```

**구현 범위**: 
- WebSocket 서버 (FastAPI/Starlette WebSocket)
- JSON-RPC 프레임 파싱
- 인증 (공유 비밀 + Discord 봇 토큰)
- 이벤트 스트리밍 (에이전트 진행 상황)

### 3.2 Juice #2: Discord Channel → 레드팀 지시 채널

**OpenClaw 원본**: `extensions/discord/` — 메시지 수신 → 라우팅 → 에이전트 실행 → 응답

**Decepticon 적용**:

```python
# decepticon/channels/discord_channel.py (신규)

class DiscordRedTeamChannel:
    """
    Discord에서 레드팀 지시를 수신하고 결과를 보고.
    
    채널 구조:
    - #engagement-control  → 인게이지먼트 시작/중단
    - #recon               → 정찰 지시 + 결과
    - #exploit             → 익스플로잇 지시 + 결과
    - #findings            → 발견사항 자동 보고
    - #alerts              → OPSEC 위반 알림
    """
    
    async def on_message(self, message):
        # 1. allowlist 검증 (승인된 운영자만)
        # 2. 라우팅 (채널별 에이전트 매핑)
        # 3. 세션 할당 (스레드 = 독립 세션)
        # 4. 에이전트 스폰 or 기존 세션에 steer
        # 5. 결과 스트리밍 → Discord 스레드
```

**사용 시나리오**:
```
[Discord #recon]
운영자: @DeceptiBot scan example.com for subdomains and open ports
봇: Accepted. Spawning recon agent in sandbox-01...
    [Thread: recon-example.com-20260410]
    - Subdomain enumeration: 47 found
    - Port scan: 12 open services
    - Web tech fingerprint: nginx/1.25, React, Node.js
    - Potential entry points: 3 identified
    Full report: /workspace/example-com/findings.txt

[Discord #exploit]
운영자: @DeceptiBot attempt SQLi on api.example.com/users?id=
봇: Accepted. Spawning exploit agent...
    ⚠️ OPSEC CHECK: Target in scope (RoE validated)
    [Thread: exploit-sqli-20260410]
    - Testing parameter: id
    - SQLi type: blind boolean-based
    - Result: VULNERABLE (MySQL 8.0)
    - Evidence preserved: /workspace/example-com/evidence/sqli-001.txt
```

### 3.3 Juice #3: Session Management → 인게이지먼트 세션

**OpenClaw 원본**: `src/sessions/` + `src/routing/session-key.ts`

**Decepticon 적용**:

```python
# 세션 키 체계
engagement:<slug>:main                          # 인게이지먼트 메인
engagement:<slug>:recon                         # 정찰 세션
engagement:<slug>:exploit:<target>              # 타겟별 익스플로잇
engagement:<slug>:postexploit:<host>            # 호스트별 후속공격
engagement:<slug>:discord:thread:<threadId>     # Discord 스레드 바인딩

# 세션 격리
- 인게이지먼트별 독립 workspace
- 타겟별 독립 Docker sandbox
- 스레드별 독립 컨텍스트
- RoE가 모든 세션에 주입 (가드레일)
```

### 3.4 Juice #4: sessions_spawn → 병렬 에이전트 풀

**OpenClaw 원본**: `src/agents/tools/sessions-spawn-tool.ts` + `src/agents/subagent-spawn.ts`

**Decepticon 적용**:

```python
# decepticon/gateway/agent_pool.py (신규)

class AgentPool:
    """
    병렬 에이전트 풀. OpenClaw의 sessions_spawn 패턴을 적용.
    각 에이전트는 독립 Docker sandbox에서 실행.
    """
    
    async def spawn(self, objective: Objective, sandbox_id: str) -> AgentRun:
        """
        목표별 에이전트를 독립 세션으로 스폰.
        현재 Ralph loop의 순차 실행을 병렬로 전환.
        """
        session_key = f"engagement:{slug}:{objective.phase}:{objective.id}"
        sandbox = await self.sandbox_pool.acquire(sandbox_id)
        
        agent = create_agent(
            agent_type=objective.phase,  # recon/exploit/postexploit
            sandbox=sandbox,
            session_key=session_key,
            roe=self.roe,  # RoE 주입
        )
        
        run = AgentRun(agent, session_key, objective)
        self.active_runs[run.id] = run
        
        # 비동기 실행 (즉시 반환)
        asyncio.create_task(self._execute_and_report(run))
        return run
    
    async def steer(self, run_id: str, message: str):
        """실행 중 에이전트에 지시 주입 (OpenClaw steer 패턴)"""
        run = self.active_runs[run_id]
        await run.inject_message(message)
    
    async def list_active(self) -> list[AgentRunStatus]:
        """활성 에이전트 상태 조회"""
```

### 3.5 Juice #5: Cron Service → 야간 스캔 스케줄러

**OpenClaw 원본**: `src/cron/` — 격리 에이전트 실행 + 배달

**Decepticon 적용**:

```python
# decepticon/gateway/scan_scheduler.py (신규)

class ScanScheduler:
    """
    야간 자동 스캔. OpenClaw CronService 패턴.
    격리 세션에서 실행하여 컨텍스트 오염 방지.
    """
    
    # 사용 예시:
    schedules = [
        # 매일 새벽 2시: 서브도메인 변경 감지
        CronJob(
            name="subdomain-monitor",
            schedule="0 2 * * *",
            tz="Asia/Seoul",
            task="Compare current subdomains of {target} with previous scan. "
                 "Report new/removed subdomains.",
            isolated=True,
            announce="discord:#recon",
        ),
        # 매주 월요일: 취약점 데이터베이스 업데이트 체크
        CronJob(
            name="cve-check",
            schedule="0 3 * * 1",
            tz="Asia/Seoul",
            task="Check new CVEs for technologies identified in {target}. "
                 "Cross-reference with our findings.",
            isolated=True,
            announce="discord:#findings",
        ),
        # 6시간마다: 포트 변경 감지
        CronJob(
            name="port-monitor",
            schedule="0 */6 * * *",
            task="Quick port scan on {target} scope. Diff with last scan.",
            isolated=True,
            announce="discord:#alerts",
        ),
    ]
```

### 3.6 Juice #6: Hooks Engine → OPSEC 가드레일

**OpenClaw 원본**: `src/hooks/` — 30+ 라이프사이클 훅

**Decepticon 적용**:

```python
# decepticon/gateway/opsec_hooks.py (신규)

class OPSECHookEngine:
    """
    모든 에이전트 액션에 OPSEC 가드레일 적용.
    OpenClaw의 before_tool_call / after_tool_call 패턴.
    """
    
    hooks = {
        "before_tool_call": [
            roe_scope_check,        # RoE 범위 검증
            rate_limit_check,       # 스캔 속도 제한
            noisy_command_check,    # 탐지 위험 명령어 경고
            time_window_check,      # 허용 시간대 검증
        ],
        "after_tool_call": [
            evidence_capture,       # 증거 자동 저장
            finding_classifier,     # 발견사항 자동 분류
            kg_update,             # Knowledge Graph 업데이트
        ],
        "before_agent_reply": [
            sensitive_data_filter,  # 민감정보 필터링
            opsec_rating_inject,    # OPSEC 등급 주입
        ],
        "agent_end": [
            auto_report,           # 자동 보고서 생성
            discord_notify,        # Discord 알림
            deconfliction_check,   # 디컨플릭션 검증
        ],
    }
```

### 3.7 Juice #7: Plugin SDK → 공격 모듈 시스템

**OpenClaw 원본**: `src/plugins/` — Capability Registration Model

**Decepticon 적용**:

```python
# decepticon/plugins/registry.py (신규)

class AttackModuleRegistry:
    """
    공격 모듈 플러그인 시스템. OpenClaw의 capability registration 패턴.
    """
    
    def register_scanner(self, scanner: ScannerPlugin):
        """정찰 스캐너 등록 (nmap wrapper, nuclei, etc.)"""
    
    def register_exploiter(self, exploiter: ExploiterPlugin):
        """익스플로잇 모듈 등록 (SQLi, XSS, etc.)"""
    
    def register_reporter(self, reporter: ReporterPlugin):
        """보고서 생성기 등록 (HackerOne, Bugcrowd, etc.)"""
    
    def register_hook(self, hook: OPSECHook):
        """OPSEC 훅 등록"""

# 모듈 예시
@register_scanner
class NucleiScanner:
    id = "nuclei"
    capabilities = ["vuln-scan", "cve-detect", "misconfig"]
    
    async def scan(self, target, templates=None):
        return await self.sandbox.exec(
            f"nuclei -u {target} -t {templates} -json"
        )
```

## 4. 구현 로드맵

### Phase 1: RedGate 기반 (2-3주)

**목표**: CLI 외에 Discord/WebSocket으로 접근 가능한 제어 평면

```
작업:
├── [ ] RedGate WebSocket 서버 (FastAPI WebSocket)
├── [ ] JSON-RPC 프레임 파서 + 인증
├── [ ] Discord 봇 채널 통합 (discord.py)
├── [ ] 기본 라우팅 (채널 → 에이전트 세션)
├── [ ] 이벤트 스트리밍 (에이전트 → Discord)
└── [ ] 기존 Ink CLI에 WebSocket 클라이언트 추가
```

**변경 파일**:
```
decepticon/
  gateway/           (신규)
    redgate.py       # WebSocket 서버
    routing.py       # 세션 라우팅
    session.py       # 세션 관리
  channels/          (신규)
    discord.py       # Discord 봇 통합
    base.py          # 채널 추상 클래스
```

### Phase 2: 병렬 에이전트 풀 (2주)

**목표**: Ralph loop를 순차→병렬로 전환

```
작업:
├── [ ] AgentPool 구현 (sessions_spawn 패턴)
├── [ ] Docker sandbox 풀 관리 (N개 동시 실행)
├── [ ] 세션 키 체계 도입
├── [ ] 에이전트 steer 기능 (실행 중 조향)
├── [ ] Task registry (목표 진행 추적)
└── [ ] 완료 이벤트 → Discord 자동 통보
```

### Phase 3: 스케줄링 + OPSEC 훅 (1-2주)

**목표**: 야간 자동 스캔 + 안전장치

```
작업:
├── [ ] ScanScheduler (Cron 패턴)
├── [ ] OPSEC 훅 엔진
├── [ ] RoE 자동 검증 훅
├── [ ] 증거 자동 캡처 훅
├── [ ] 발견사항 자동 분류 + KG 업데이트
└── [ ] 보고서 자동 생성 (HackerOne/Bugcrowd)
```

### Phase 4: 플러그인 시스템 (2주)

**목표**: 공격 모듈 확장성

```
작업:
├── [ ] AttackModuleRegistry
├── [ ] 스캐너 플러그인 인터페이스
├── [ ] 익스플로잇 모듈 인터페이스
├── [ ] 보고서 생성기 인터페이스
└── [ ] 커뮤니티 모듈 로딩 (skills/ → plugins/)
```

## 5. 아키텍처 매핑 상세

### 5.1 OpenClaw → Decepticon 컴포넌트 매핑

| OpenClaw | Decepticon (현재) | Decepticon (목표) |
|----------|-------------------|-------------------|
| Gateway WS Server | LangGraph Dev Server | **RedGate** (WS + RPC) |
| Discord Extension | 없음 | **DiscordRedTeamChannel** |
| Pi Agent Runtime | create_agent() + LangGraph | 유지 (LangGraph 기반) |
| sessions_spawn | Ralph loop (순차) | **AgentPool** (병렬) |
| Session Manager | opplan.json (파일) | **SessionManager** (메모리 + 파일) |
| CronService | 없음 | **ScanScheduler** |
| Task Registry | OPPLAN Middleware | **확장된 OPPLAN + TaskRegistry** |
| Plugin SDK | skills/ (마크다운) | **AttackModuleRegistry** |
| Hooks Engine | SafeCommandMiddleware | **OPSECHookEngine** |
| Context Engine | SummarizationMiddleware | 유지 + 강화 |
| Auto-Reply | StreamingRunnable | **확장** (Discord 전달) |
| MCP Bridge | 없음 | **Phase 5** (선택) |

### 5.2 보존해야 할 Decepticon 고유 자산

| 자산 | 이유 |
|------|------|
| **Docker Kali Sandbox** | OpenClaw의 범용 sandbox보다 공격 특화 |
| **OPPLAN Middleware** | 킬체인 기반 목표 추적은 레드팀 고유 |
| **SafeCommandMiddleware** | OPSEC 가드레일의 기반 |
| **Knowledge Graph (Neo4j)** | 공격 체인 영속성 (OpenClaw에 없음) |
| **보고서 생성기** | HackerOne/Bugcrowd 특화 (OpenClaw에 없음) |
| **전문 에이전트** | recon/exploit/postexploit/cloud_hunter/ad_operator |
| **LiteLLM 프록시** | 멀티 프로바이더 라우팅 (OpenClaw과 다른 접근) |

### 5.3 버려도 되는 것 (OpenClaw이 더 나은 것)

| 현재 Decepticon | 대체 |
|----------------|------|
| CLI-only 접근 | RedGate + Discord |
| 순차 Ralph loop | AgentPool 병렬 실행 |
| 수동 시작만 가능 | ScanScheduler + Discord 트리거 |
| 파일 기반 결과 보고 | 이벤트 스트리밍 + Discord 자동 통보 |
| findings.txt 메모리 | Task registry + KG |

## 6. 사용 시나리오: 해킹 가재 완성형

### 6.1 버그바운티 시나리오

```
[Discord #engagement-control]
운영자: @DeceptiBot start engagement target:example.com 
        scope:*.example.com program:hackerone/example
봇: Engagement "example-com" created.
    RoE loaded from HackerOne program scope.
    Sandbox pool: 3 Kali containers ready.

[Discord #recon]  
운영자: @DeceptiBot full recon on *.example.com
봇: Spawning recon agents (3 parallel):
    - Agent-R1: Subdomain enumeration
    - Agent-R2: Port scanning + service fingerprint
    - Agent-R3: Web tech stack + WAF detection

[2시간 후 - 자동 보고]
봇: Recon complete. Summary:
    📍 47 subdomains, 156 open ports
    🔍 3 potential entry points identified
    ⚠️ 2 misconfigured services detected
    Full report: /workspace/example-com/recon-report.md

[Discord #exploit]
운영자: @DeceptiBot test the IDOR on api.example.com/users/{id}
봇: ⚠️ OPSEC CHECK: api.example.com is in scope ✅
    Spawning exploit agent in sandbox-02...
    
[Discord #exploit - Thread: idor-test]
봇: Testing IDOR on /users/{id}...
    - Enumerated users 1-1000
    - Found: 847 accessible (should be 1)
    - Impact: PII exposure (email, phone)
    - CVSS: 7.5 (High)
    - Evidence saved: evidence/idor-001/
    
    📝 Draft HackerOne report generated:
    /workspace/example-com/reports/idor-001.md

[운영자 수면 중 - Cron 자동 실행]
# 새벽 2시: 서브도메인 변경 감지
봇 → #alerts: 🆕 New subdomain detected: staging.example.com
              Port 8080 open (Node.js dev server)
              Potential: exposed staging environment

# 새벽 4시: CVE 크로스레퍼런스
봇 → #findings: 🔴 CVE-2026-1234 affects nginx/1.25.3
                 (identified on api.example.com)
                 Exploit available: PoC in ExploitDB

[아침]
운영자: @DeceptiBot generate report for hackerone
봇: Report generated with 5 findings:
    - P1: IDOR on user API (CVSS 7.5)
    - P2: CVE-2026-1234 nginx (CVSS 8.1)
    - P3: Exposed staging environment
    - P4: Missing rate limiting
    - P5: Information disclosure in error pages
    Ready to submit: /workspace/example-com/reports/final/
```

### 6.2 레드팀 인게이지먼트 시나리오

```
[Discord #engagement-control]
운영자: @DeceptiBot load engagement from /workspace/acme-corp/
        roe: roe.json, conops: conops.json, opplan: opplan.json
봇: Engagement "acme-corp" loaded.
    RoE: 15 rules, 3 exclusions
    CONOPS: APT29 profile
    OPPLAN: 8 objectives (RECON→C2)
    Time window: 22:00-06:00 KST only

[22:00 자동 시작 — Cron]
봇 → #recon: 🟢 Night window started. Executing OPPLAN...
    Objective 1/8: External recon (RECON phase)
    Spawning: Agent-R1 (subdomain) + Agent-R2 (OSINT)

[자율 실행 - 운영자 수면 중]
# 목표 1 완료 → 목표 2 자동 진행
봇 → #recon: ✅ Obj 1 PASSED. 12 targets identified.
봇 → #exploit: 🔄 Obj 2: Initial access via phishing landing page
    Spawning: Agent-E1 in sandbox-01

# OPSEC 위반 감지
봇 → #alerts: 🔴 OPSEC VIOLATION: Agent-E1 attempted out-of-scope IP
    Action: Command blocked. Agent steered back to scope.

# 목표 3 진행
봇 → #exploit: ✅ Obj 2 PASSED. Creds obtained via phishing sim.
봇 → #exploit: 🔄 Obj 3: Lateral movement

[06:00 — 시간 윈도우 종료]
봇 → #engagement-control: 🟡 Night window ended. Pausing operations.
    Progress: 5/8 objectives completed
    Next window: 22:00 KST tonight
    Summary: /workspace/acme-corp/nightly-report-20260410.md
```

## 7. 기술적 고려사항

### 7.1 LiteLLM vs OpenClaw 프로바이더 모델

Decepticon은 **LiteLLM 프록시를 유지**하는 것이 유리하다:
- 이미 구축된 멀티 프로바이더 라우팅
- PostgreSQL 기반 사용량 추적
- 버짓 관리 (장시간 자율 실행 시 중요)
- OpenClaw의 프로바이더 플러그인 방식보다 레드팀에 적합

### 7.2 보안 고려사항

| 항목 | 조치 |
|------|------|
| Discord 봇 접근 | 운영자 allowlist (Discord 사용자 ID) |
| 명령어 인증 | 역할 기반 (admin/operator/viewer) |
| sandbox 격리 | 독립 Docker 네트워크 (sandbox-net) |
| RoE 강제 | before_tool_call 훅에서 모든 명령어 검증 |
| 증거 보호 | 암호화 저장 + 무결성 해시 |
| 로그 보호 | 타임스탬프 + 변경 불가 로그 |

### 7.3 OAuth 통합 (선택)

Decepticon에도 OpenClaw의 OAuth 패턴을 적용하면:
- Claude Pro/Max 구독으로 API 비용 없이 레드팀 실행 가능
- ChatGPT Plus/Codex 구독으로 대안 모델 사용

```python
# decepticon/auth/oauth.py (Phase 5)
# OpenClaw의 token sink 패턴 적용
class OAuthTokenManager:
    def __init__(self, profile_path: Path):
        self.profiles = load_auth_profiles(profile_path)
    
    async def get_token(self, provider: str) -> str:
        profile = self.profiles[provider]
        if profile.is_expired():
            await self.refresh(profile)
        return profile.access_token
```

## 8. 결론

OpenClaw에서 추출할 핵심 "Juice" 7가지:

1. **Gateway 패턴** → RedGate (WS 제어 평면)
2. **Channel 패턴** → Discord 레드팀 채널
3. **Session 패턴** → 인게이지먼트 세션 격리
4. **Spawn 패턴** → 병렬 에이전트 풀
5. **Cron 패턴** → 야간 자동 스캔
6. **Hook 패턴** → OPSEC 가드레일
7. **Plugin 패턴** → 공격 모듈 레지스트리

Decepticon의 **고유 자산**(Kali sandbox, OPPLAN, Knowledge Graph, 전문 에이전트, 보고서 생성기)은 보존하면서, OpenClaw의 **오케스트레이션 인프라**를 이식하는 것이 최적의 전략이다.
