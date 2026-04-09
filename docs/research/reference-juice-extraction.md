# Reference Juice Extraction

> `reference/` 폴더의 모든 프로젝트에서 Decepticon에 적용 가능한 핵심 패턴("Juice") 추출

## 1. Reference Overview

| Project | Language | Lines | Core Value for Decepticon |
|---------|----------|-------|--------------------------|
| **openclaw** | TypeScript | 50K+ | Gateway, Plugin SDK, Agent Runtime, Channel integration |
| **nanobot** | Python | ~3K | 경량 에이전트 루프, 메모리 통합, 멀티채널 |
| **nanoclaw** | TypeScript | ~10K | OpenClaw 경량화, 컨테이너 배포 |
| **strix** | Python | ~5K | 벤치마크, 컨테이너 보안 테스트 |
| **red-run** | Shell/Python | ~2K | 레드팀 실행 프레임워크, 운영자 인터페이스 |
| **red-team-agent-skills** | Node.js | ~1K | Claude Code용 레드팀 스킬 |
| **anthropic-cybersecurity-skills** | Markdown | 700+ skills | **공식 Anthropic 사이버보안 스킬 대전집** |
| **aleister-skills** | Markdown | 30+ skills | 에이전트 작업 스킬 (코드 리뷰, 브레인스토밍) |
| **ralph** | Bash/Markdown | ~240 | 자율 루프 원본 패턴 |
| **deepagents** | Python | ~3K | Deep Agent SDK 참조 |
| **awesome-claude-skills-security** | Markdown | curated | 보안 스킬 컬렉션 |

## 2. nanobot — 경량 에이전트 아키텍처

**Source**: `reference/nanobot/`

### 2.1 프로젝트 개요

nanobot은 **OpenClaw에서 영감받은 초경량 AI 어시스턴트**이다. OpenClaw 대비 99% 적은 코드라인으로 핵심 기능을 구현한다.

> "Delivers core agent functionality with 99% fewer lines of code than OpenClaw."

### 2.2 추출 가능한 Juice

**Juice #1: Persistent Agent Loop**

```python
# nanobot/agent/loop.py (lines 183-254)
class AgentLoop:
    async def _run_agent_loop(self):
        while iteration < self.max_iterations:
            iteration += 1
            
            # Build context
            tool_defs = self.tools.get_definitions()
            
            # Call LLM with tools
            response = await self.provider.chat_with_retry(
                messages=messages,
                tools=tool_defs,
                model=self.model,
            )
            
            if response.has_tool_calls:
                for tool_call in response.tool_calls:
                    result = await self.tools.execute(
                        tool_call.name, tool_call.arguments
                    )
                    messages = self.context.add_tool_result(messages, result)
            else:
                # No tool calls = final response
                final_content = response.content
                break
```

**Decepticon 적용**: nanobot의 루프는 Decepticon의 LangGraph 에이전트보다 단순하지만, **메시지 버스 기반 지속 실행**이라는 점에서 OpenClaw의 임베디드 런타임과 유사. Decepticon에서 경량 스캐너 에이전트에 이 패턴을 적용할 수 있음.

**Juice #2: Memory Consolidation**

```
nanobot 메모리 모델:
├── /memory/MEMORY.md    — 세션 간 지속 사실 (장기 메모리)
├── /memory/HISTORY.md   — grep 가능한 타임라인
│   (각 엔트리: [YYYY-MM-DD HH:MM] 시작)
└── 세션 내 메시지 히스토리 (단기 메모리)
```

**Decepticon 적용**: 
- `findings.txt` (현재) → MEMORY.md + HISTORY.md 패턴으로 분리
- MEMORY.md: 인게이지먼트 전체에서 유효한 사실 (타겟 IP, 서비스 버전, 크리덴셜)
- HISTORY.md: 시간순 공격 타임라인 (포렌식 증거)

**Juice #3: Tool Registry Pattern**

```python
# 도구를 startup 시 한번 등록, tool call마다 원자적 실행
class ToolRegistry:
    tools: dict[str, Tool]  # name → Tool
    
    def register(self, tool: Tool):
        self.tools[tool.name] = tool
    
    def get_definitions(self) -> list[ToolDef]:
        return [t.definition for t in self.tools.values()]
    
    async def execute(self, name: str, arguments: dict) -> str:
        return await self.tools[name].execute(arguments)
```

**Decepticon 적용**: 현재 도구가 Python 모듈로 하드코딩되어 있음. nanobot의 Tool Registry로 동적 도구 등록/해제 가능.

**Juice #4: 멀티채널 지원 (Python 구현)**

nanobot은 Python으로 20+ 채널을 지원:
- WhatsApp, Telegram, Discord, Slack, Signal
- WeChat, DingTalk, Feishu, LINE
- IRC, Matrix, QQ

**Decepticon 적용**: nanobot의 Python 채널 구현을 참조하여 Discord 채널을 빠르게 구현할 수 있음. TypeScript(OpenClaw)보다 Python(nanobot) 구현이 Decepticon에 직접 이식 용이.

### 2.3 nanobot vs OpenClaw 비교

| 측면 | OpenClaw | nanobot | Decepticon 선택 |
|------|----------|---------|----------------|
| 언어 | TypeScript | Python | **Python (nanobot)** |
| 코드 규모 | 50K+ lines | ~3K lines | 경량 시작 |
| Plugin SDK | 200+ exports | 없음 | OpenClaw 참조 설계 |
| Channel | 22+ (플러그인) | 20+ (내장) | nanobot 스타일 |
| Memory | Compaction | MEMORY.md | nanobot 스타일 |
| Gateway | WS JSON-RPC | HTTP API | OpenClaw 스타일 |

## 3. nanoclaw — OpenClaw 경량화

**Source**: `reference/nanoclaw/`

### 3.1 프로젝트 개요

nanoclaw는 OpenClaw의 **경량 포크/재구현**으로, 컨테이너 우선 배포를 목표로 한다.

### 3.2 추출 가능한 Juice

**Juice #1: Container-first Deployment**

```
nanoclaw/
  ├── container/           # 컨테이너 설정
  ├── config-examples/     # 설정 예시
  └── CHANGELOG.md         # 변경 이력
```

**Decepticon 적용**: Docker Compose 기반 배포는 이미 구현. nanoclaw의 컨테이너 최적화 패턴 참고.

**Juice #2: 설정 예시 패턴**

nanoclaw의 `config-examples/` 디렉토리에서 다양한 배포 시나리오별 설정 예시 제공.

**Decepticon 적용**: `config/examples/` 디렉토리에 시나리오별 설정 제공
- `bug-bounty-basic.yaml` — 버그바운티 기본
- `red-team-engagement.yaml` — 레드팀 인게이지먼트
- `continuous-recon.yaml` — 지속적 정찰

## 4. strix — 보안 벤치마크 프레임워크

**Source**: `reference/strix/`

### 4.1 프로젝트 개요

strix는 **Python 기반 보안 벤치마크 프레임워크**로, 컨테이너 보안 테스트와 성능 측정을 제공한다.

```
strix/
  ├── benchmarks/          # 벤치마크 정의
  ├── containers/          # 테스트 컨테이너
  ├── docs/                # 문서
  ├── scripts/             # 실행 스크립트
  ├── pyproject.toml       # Python 프로젝트 설정
  └── Makefile             # 빌드 시스템
```

### 4.2 추출 가능한 Juice

**Juice #1: 벤치마크 기반 에이전트 평가**

strix의 벤치마크 프레임워크를 Decepticon 에이전트 성능 평가에 적용:
- 정찰 에이전트: 서브도메인 발견 수, 스캔 시간, 정확도
- 익스플로잇 에이전트: 취약점 발견률, 오탐률, PoC 성공률
- 전체 파이프라인: 인게이지먼트 완료 시간, 목표 달성률

**Juice #2: 컨테이너 테스트 패턴**

strix의 테스트 컨테이너를 참조하여 Decepticon의 CI 테스트 환경 구축:
- 취약한 대상 컨테이너 (Metasploitable 스타일)
- 자동화된 공격/방어 시나리오
- 결과 측정 및 보고

## 5. red-run — 레드팀 실행 프레임워크

**Source**: `reference/red-run/`

### 5.1 프로젝트 개요

red-run은 **레드팀 작전 실행 프레임워크**로, 에이전트 기반 공격 시뮬레이션을 관리한다.

```
red-run/
  ├── agents/              # 에이전트 정의
  ├── operator/            # 운영자 인터페이스
  ├── scripts/             # 실행 스크립트
  ├── docs/                # 문서
  ├── preflight.sh         # 사전 점검
  ├── install.sh           # 설치 스크립트
  └── CLAUDE.md            # Claude Code 통합
```

### 5.2 추출 가능한 Juice

**Juice #1: Preflight Check Pattern**

```bash
# preflight.sh — 실행 전 환경 검증
# 1. 필수 도구 확인 (nmap, nuclei, etc.)
# 2. Docker 환경 확인
# 3. 네트워크 연결 확인
# 4. RoE 파일 존재 확인
# 5. API 키 설정 확인
```

**Decepticon 적용**: 인게이지먼트 시작 전 자동 사전 점검 시스템. 현재 Decepticon에 없는 패턴.

```python
# decepticon/preflight.py (신규)
class PreflightCheck:
    checks = [
        ("docker_running", "Docker daemon is running"),
        ("sandbox_image", "Kali sandbox image exists"),
        ("tools_available", "Required tools installed in sandbox"),
        ("roe_loaded", "Rules of Engagement file loaded"),
        ("target_reachable", "Target hosts are reachable"),
        ("api_keys_set", "LLM API keys configured"),
        ("disk_space", "Sufficient disk space for evidence"),
    ]
    
    async def run_all(self) -> PreflightReport:
        results = {}
        for check_id, description in self.checks:
            results[check_id] = await getattr(self, check_id)()
        return PreflightReport(results)
```

**Juice #2: Operator Interface**

red-run의 `operator/` 디렉토리는 운영자가 에이전트를 관리하는 인터페이스를 정의.

**Decepticon 적용**: Discord 봇 외에 CLI 기반 운영자 인터페이스도 유지 (현재 Ink CLI 확장).

**Juice #3: CLAUDE.md 통합**

red-run은 Claude Code 통합을 위한 CLAUDE.md를 포함. 이는 Ralph loop에서 에이전트에 주입되는 지시서 역할.

## 6. anthropic-cybersecurity-skills — 사이버보안 스킬 대전집

**Source**: `reference/anthropic-cybersecurity-skills/`

### 6.1 프로젝트 개요

Anthropic 공식 사이버보안 스킬 컬렉션. **700개 이상의 보안 스킬**을 포함하며, 이는 Decepticon의 스킬 시스템에 직접 활용 가능한 최대 자산이다.

### 6.2 스킬 카테고리 분석

| Category | Count (approx.) | Decepticon 관련성 |
|----------|-----------------|-------------------|
| **Analyzing** (분석) | ~90 | 높음 — 포렌식, 악성코드, 네트워크 분석 |
| **Detecting** (탐지) | ~80 | 중간 — 블루팀이지만 레드팀 에뮬레이션에 활용 |
| **Performing** (수행) | ~120 | **매우 높음** — 침투테스트, 취약점 평가 |
| **Exploiting** (익스플로잇) | ~40 | **매우 높음** — 직접 공격 기법 |
| **Implementing** (구현) | ~150 | 중간 — 보안 구현 (방어) |
| **Building** (구축) | ~40 | 중간 — 인프라 구축 |
| **Hunting** (헌팅) | ~40 | 높음 — 위협 헌팅 기법 |
| **Scanning** (스캔) | ~15 | **높음** — 취약점 스캔 |
| **Configuring** (설정) | ~30 | 낮음 — 방어 설정 |
| **Conducting** (실시) | ~30 | **높음** — 침투테스트 실시 |
| **Reverse Engineering** | ~10 | 높음 — 바이너리 분석 |

### 6.3 Decepticon에 직접 활용 가능한 핵심 스킬

**레드팀/침투테스트**:
```
conducting-full-scope-red-team-engagement
conducting-internal-network-penetration-test
conducting-external-reconnaissance-with-osint
executing-red-team-engagement-planning
executing-red-team-exercise
performing-active-directory-penetration-test
performing-web-application-penetration-test
performing-cloud-penetration-testing
performing-network-penetration-test
performing-privilege-escalation-assessment
performing-wireless-network-penetration-test
performing-api-security-testing-with-postman
```

**익스플로잇**:
```
exploiting-sql-injection-vulnerabilities
exploiting-sql-injection-with-sqlmap
exploiting-active-directory-with-bloodhound
exploiting-server-side-request-forgery
exploiting-insecure-deserialization
exploiting-kerberoasting-with-impacket
exploiting-idor-vulnerabilities
exploiting-http-request-smuggling
exploiting-jwt-algorithm-confusion-attack
exploiting-race-condition-vulnerabilities
exploiting-ms17-010-eternalblue-vulnerability
```

**정찰/OSINT**:
```
performing-subdomain-enumeration-with-subfinder
performing-open-source-intelligence-gathering
performing-osint-with-spiderfoot
performing-dns-enumeration-and-zone-transfer
scanning-network-with-nmap-advanced
collecting-open-source-intelligence
```

**후속 공격**:
```
performing-lateral-movement-with-wmiexec
performing-kerberoasting-attack
conducting-domain-persistence-with-dcsync
performing-pass-the-ticket-attacks
exploiting-constrained-delegation-abuse
building-red-team-c2-infrastructure-with-havoc
building-c2-infrastructure-with-sliver-framework
```

### 6.4 적용 전략

```
Strategy: Anthropic 스킬을 Decepticon 스킬로 변환

1. 스킬 선별 (Priority)
   ├── P0: 직접 공격 기법 (exploiting-*, performing-pentest-*)
   ├── P1: 정찰/OSINT (performing-recon-*, collecting-*, scanning-*)
   ├── P2: 후속 공격 (performing-lateral-*, conducting-persistence-*)
   └── P3: 분석/보고 (analyzing-*, building-report-*)

2. 형식 변환
   ├── Anthropic: index.json + skills/<skill-name>/
   └── Decepticon: skills/<phase>/<skill-name>/SKILL.md
       (YAML frontmatter: name, description, phase, tools_required)

3. 에이전트 바인딩
   ├── recon 에이전트 → OSINT/정찰 스킬
   ├── exploit 에이전트 → 익스플로잇 스킬
   ├── postexploit 에이전트 → 후속 공격 스킬
   └── analyst 에이전트 → 분석/보고 스킬
```

## 7. red-team-agent-skills — Claude Code 보안 스킬

**Source**: `reference/red-team-agent-skills/`

### 7.1 프로젝트 개요

Claude Code용 레드팀 스킬 패키지. npm 패키지로 배포.

### 7.2 추출 가능한 Juice

**Juice #1: 스킬 구조 패턴**

```
red-team-agent-skills/
  ├── reports/             # 보고서 템플릿
  ├── results/             # 결과 저장
  ├── package.json         # npm 배포
  └── CLAUDE.md            # 스킬 지시서
```

**Decepticon 적용**: 스킬의 npm 패키지 배포 패턴. `pip install decepticon-skills-redteam` 형태로 공격 스킬 배포 가능.

## 8. aleister-skills — 에이전트 작업 스킬

**Source**: `reference/aleister-skills/`

### 8.1 추출 가능한 Juice

| Skill | 용도 | Decepticon 적용 |
|-------|------|----------------|
| `code-reviewer` | 코드 리뷰 | 공격 코드/스크립트 리뷰 |
| `codeql` | CodeQL 보안 분석 | 소스코드 취약점 분석 |
| `agents-md-generator` | AGENTS.md 자동 생성 | 인게이지먼트 문서 자동 생성 |
| `brainstorming` | 브레인스토밍 | 공격 벡터 브레인스토밍 |
| `create-specification` | 명세 작성 | OPPLAN 자동 생성 |

## 9. ralph — 자율 루프 원본

**Source**: `reference/ralph/`

### 9.1 이미 추출된 Juice (universal-ralph-loop.md 참조)

- Plan → Pick → Execute → Verify → Mark → Repeat 패턴
- prd.json 구조
- progress.txt 학습 축적
- `<promise>COMPLETE</promise>` 완료 신호
- Fresh context per iteration

### 9.2 추가 Juice

**Juice: AGENTS.md 자동 업데이트**

Ralph는 매 반복 후 AGENTS.md를 업데이트하여 **코드베이스 패턴**을 축적한다:
```
Examples of what to add:
- "this codebase uses X for Y"
- "do not forget to update Z when changing W"
- "the settings panel is in component X"
```

**Decepticon 적용**: 각 인게이지먼트의 `workspace/AGENTS.md`에 타겟별 패턴 축적:
```
- "This target uses nginx/1.25 behind Cloudflare WAF"
- "SQL injection on /api/users requires time-based blind technique"
- "Port 8443 responds to mutual TLS only"
```

## 10. deepagents — Deep Agent SDK

**Source**: `reference/deepagents/`

### 10.1 추출 가능한 Juice

**Juice: create_deep_agent() vs create_agent()**

Deep Agents SDK의 `create_deep_agent()`는 자동 미들웨어 스택을 제공. Decepticon은 `create_agent()` (explicit 미들웨어)를 사용하지만, Deep Agents의 패턴도 참고 가능.

## 11. Summary: Juice → Decepticon 매핑

| Reference | Extracted Juice | Decepticon Component | Priority |
|-----------|----------------|---------------------|----------|
| **openclaw** | Gateway WS, Plugin SDK, Agent Runtime, Sessions, Hooks, Cron | RedGate, AttackModuleRegistry, AgentPool, ScanScheduler | P0 |
| **nanobot** | Python 에이전트 루프, 메모리 모델, 멀티채널 (Python) | 경량 에이전트, MEMORY.md, Discord 채널 | P1 |
| **anthropic-cybersecurity-skills** | 700+ 보안 스킬 | skills/ 디렉토리 확장 | P0 |
| **ralph** | 자율 루프, progress.txt, AGENTS.md 업데이트 | Ralph Loop Engine, 학습 축적 | P0 |
| **red-run** | Preflight checks, Operator interface | PreflightCheck, CLI operator | P1 |
| **strix** | 벤치마크, 컨테이너 테스트 | CI 테스트 환경, 에이전트 평가 | P2 |
| **nanoclaw** | Container-first, config examples | Docker 최적화, 설정 예시 | P2 |
| **red-team-agent-skills** | npm 스킬 배포 | pip 스킬 배포 패턴 | P3 |
| **aleister-skills** | CodeQL, AGENTS.md 생성, 브레인스토밍 | 소스코드 분석, 문서 자동화 | P3 |
| **deepagents** | Deep Agent SDK 패턴 | 미들웨어 자동 스택 | P3 |

## 12. 즉시 실행 가능한 액션 아이템

### 12.1 P0 (즉시)
```
1. anthropic-cybersecurity-skills에서 40개 핵심 스킬 선별 → skills/ 복사
2. Ralph loop + PlanAdapter 구현 (universal-ralph-loop.md 참조)
3. OpenClaw Gateway 패턴으로 RedGate 프로토타입
```

### 12.2 P1 (1-2주)
```
4. nanobot 참조하여 Python Discord 채널 구현
5. red-run 참조하여 PreflightCheck 시스템 구현
6. nanobot 참조하여 MEMORY.md + HISTORY.md 도입
```

### 12.3 P2 (3-4주)
```
7. strix 참조하여 에이전트 벤치마크 프레임워크
8. nanoclaw 참조하여 Docker 이미지 최적화
9. 설정 예시 디렉토리 구축
```
