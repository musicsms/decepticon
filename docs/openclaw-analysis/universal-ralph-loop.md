# Universal Ralph Loop Architecture

> Plan → Pick Next → Execute → Verify → Mark → Repeat  
> 도메인이 바뀌어도 루프는 동일하다. 바뀌는 것은 Plan Adapter뿐이다.

## 1. Core Insight

Ralph Loop의 본질은 **계획 문서 기반 자율 실행 루프**이다:

1. 인간이 **Plan(계획 문서)**를 작성한다 — 이것이 유일한 인간 관여 지점
2. 에이전트가 Plan에서 **다음 미완료 항목을 선택**한다
3. 에이전트가 해당 항목을 **실행**한다 (fresh context)
4. 에이전트가 결과를 **검증**한다 (acceptance criteria)
5. 통과하면 **완료 표시**, 실패하면 **blocked 표시 + 사유 기록**
6. **모든 항목 완료될 때까지 반복** (24/7, 무한)

```
    Human writes Plan (one-time)
              |
              v
    +-------------------+
    | Load Plan         |  ←── PlanAdapter.load()
    +-------------------+
              |
              v
    +-------------------+
    | Pick Next Item    |  ←── PlanAdapter.pick_next()
    | (highest priority |
    |  where !complete) |
    +-------------------+
              |
              v
    +-------------------+
    | Spawn Fresh Agent |  ←── Clean context each iteration
    | + Execute Item    |      Memory via: git, progress.txt, plan.json
    +-------------------+
              |
              v
    +-------------------+
    | Verify Acceptance |  ←── PlanAdapter.verify(item)
    | Criteria          |
    +-------------------+
           /    \
          /      \
    PASS /        \ FAIL
        v          v
  +----------+ +----------+
  | Mark     | | Mark     |
  | Complete | | Blocked  |
  | + commit | | + reason |
  +----------+ +----------+
        \        /
         \      /
          v    v
    +-------------------+
    | All Complete?     |  ←── PlanAdapter.is_done()
    +-------------------+
        /          \
   YES /            \ NO
      v              v
  +----------+   Loop back to
  | EXIT     |   "Pick Next"
  | COMPLETE |
  +----------+
```

**이 패턴이 도메인을 넘어 동일한 이유**: 
- 개발에서: PRD의 user story를 하나씩 구현 → 테스트 → 완료
- 레드팀에서: OPPLAN의 objective를 하나씩 실행 → 증거 수집 → 완료
- 버그바운티에서: 프로그램 스코프의 타겟을 하나씩 테스트 → 취약점 보고 → 완료

**바뀌는 것은 Plan Adapter뿐**이다.

## 2. 기존 구현 비교 분석

### 2.1 Original Ralph (snarktank/ralph)

**Source**: `reference/ralph/`

가장 순수한 형태의 Ralph Loop. Bash 스크립트가 루프를 돌며 매 반복마다 fresh AI 인스턴스를 스폰한다.

```bash
# ralph.sh (핵심 로직)
for i in $(seq 1 $MAX_ITERATIONS); do
    # Fresh AI instance per iteration (clean context)
    OUTPUT=$(claude --dangerously-skip-permissions --print < CLAUDE.md)
    
    # Check completion signal
    if echo "$OUTPUT" | grep -q "<promise>COMPLETE</promise>"; then
        echo "Ralph completed all tasks!"
        exit 0
    fi
done
```

**Plan Format**: `prd.json`
```json
{
  "userStories": [
    {
      "id": "US-001",
      "title": "Add priority field",
      "acceptanceCriteria": ["Migration runs", "Typecheck passes"],
      "priority": 1,
      "passes": false
    }
  ]
}
```

**메모리 모델** (반복 간 지속):
| 매체 | 용도 |
|------|------|
| `prd.json` | 어떤 스토리가 완료되었는지 |
| `progress.txt` | 학습 내용, 패턴, 실수 |
| git history | 코드 변경 이력 |
| `AGENTS.md` | 재사용 가능한 코드베이스 패턴 |

**핵심 원칙**:
- **Each iteration = fresh context** (컨텍스트 오염 방지)
- **Small tasks** (하나의 컨텍스트 윈도우에 완료 가능해야 함)
- **Feedback loops** (typecheck, test가 매 반복 실행)
- **Completion signal** (`<promise>COMPLETE</promise>`)

### 2.2 OMC Ralph (oh-my-claudecode)

**Source**: `~/.claude/plugins/marketplaces/omc/skills/ralph/`

Original Ralph를 Claude Code 하네스에 통합한 형태. 더 정교한 검증과 AI slop 정리 포함.

**추가된 레이어**:
| Layer | Description |
|-------|-------------|
| PRD 자동 생성 | 태스크에서 prd.json 스캐폴드 자동 생성 |
| Acceptance Criteria 강제 | "Implementation is complete" 같은 제네릭 기준 거부 |
| 에이전트 티어링 | Haiku(단순) / Sonnet(표준) / Opus(복잡) 자동 배정 |
| Reviewer 검증 | architect/critic/codex 중 선택하여 독립 검증 |
| Deslop Pass | AI 코드 슬롭 자동 정리 |
| Regression 재검증 | deslop 후 회귀 테스트 |

**OMC Ralph 루프 구조**:
```
PRD Setup → Pick Story → Implement → Verify Criteria
  → Mark Complete → All Done? → Reviewer Verification
  → Deslop Pass → Regression Check → EXIT
```

### 2.3 Decepticon OPPLAN (현재)

**Source**: `decepticon/middleware/opplan.py`

레드팀 도메인 특화. PRD의 user story 대신 OPPLAN의 objective를 사용.

**Plan Format**: OPPLAN State (in-memory, LangGraph state)
```python
class Objective:
    id: str              # OBJ-001
    title: str
    description: str
    phase: ObjectivePhase  # RECON, INITIAL_ACCESS, POST_EXPLOIT, C2, EXFILTRATION
    status: ObjectiveStatus  # pending, in-progress, completed, blocked
    priority: int
    opsec_level: OpsecLevel
    c2_tier: C2Tier
    blocked_by: list[str]    # 의존성 (킬체인 순서)
    acceptance_criteria: list[str]
    evidence: str            # 완료 시 증거
    failure_reason: str      # 차단 시 사유
    attempts: int            # 시도 횟수
    owner: str               # 할당된 서브에이전트
```

**상태 전이**:
```
pending → in-progress → completed (증거 필수)
                      → blocked   (사유 + 시도 횟수 필수)
blocked → in-progress             (다른 접근법으로 재시도)
        → completed               (포기 + 설명)
```

**Battle Tracker** (매 LLM 호출마다 주입):
```
<OPPLAN_STATUS>
Engagement: acme-corp
Threat Profile: APT29
Progress: 3/8 completed, 1 blocked, 1 in-progress, 3 pending
Next: OBJ-004 [INITIAL_ACCESS] SQL Injection on login endpoint
</OPPLAN_STATUS>
```

**Decepticon의 차별점**:
- **킬체인 의존성**: `blocked_by`로 페이즈 순서 강제 (정찰 → 초기접근 → ...)
- **OPSEC 등급**: 각 목표에 노출 위험도 태깅
- **C2 티어**: 명령제어 인프라 등급 추적
- **서브에이전트 할당**: `owner` 필드로 전문 에이전트에 위임
- **증거 수집 강제**: completed 상태 전이 시 evidence 필수

### 2.4 OpenClaw Taskflow

**Source**: `reference/openclaw/skills/taskflow/SKILL.md`

Durable flow 기반 백그라운드 작업. Ralph의 "restart-safe" 버전.

**주요 추출 가능 패턴**:
- **Crash recovery**: 루프 중단 후 재시작 시 상태 복구
- **Progress streaming**: 실행 중 진행 상황 실시간 보고
- **Managed lifecycle**: flow 생성 → 실행 → 완료/실패 → 정리

## 3. Plan Adapter Interface

### 3.1 Universal Interface

모든 도메인의 Plan을 Ralph Loop에 연결하는 어댑터 인터페이스:

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

class ItemStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"

@dataclass
class PlanItem:
    """Ralph Loop의 최소 실행 단위. 도메인별 서브클래스로 확장."""
    id: str
    title: str
    description: str
    acceptance_criteria: list[str]
    priority: int
    status: ItemStatus = ItemStatus.PENDING
    dependencies: list[str] | None = None  # blocked_by
    metadata: dict[str, Any] | None = None  # 도메인별 추가 데이터

@dataclass
class VerificationResult:
    passed: bool
    evidence: str  # 통과 증거 또는 실패 사유
    criteria_results: dict[str, bool]  # 기준별 통과 여부

class PlanAdapter(ABC):
    """Universal Plan Adapter. 이것만 구현하면 어떤 도메인이든 Ralph Loop에 연결 가능."""
    
    @abstractmethod
    def load(self, source: str) -> list[PlanItem]:
        """계획 문서를 로드하여 PlanItem 리스트로 변환.
        
        Args:
            source: 파일 경로, URL, 또는 프로그램 ID
        Returns:
            정렬된 PlanItem 리스트
        """
        ...
    
    @abstractmethod
    def pick_next(self, items: list[PlanItem]) -> PlanItem | None:
        """다음 실행할 항목 선택.
        
        기본: 의존성 충족 + pending/blocked 중 최고 우선순위.
        도메인별로 오버라이드 가능 (예: 킬체인 순서).
        """
        ...
    
    @abstractmethod
    def verify(self, item: PlanItem, execution_result: Any) -> VerificationResult:
        """실행 결과를 acceptance criteria에 대해 검증.
        
        도메인별 검증 로직:
        - PRD: 테스트 통과, 타입체크 통과
        - OPPLAN: 증거 수집, RoE 준수
        - BugBounty: 취약점 재현, PoC 작성
        """
        ...
    
    @abstractmethod
    def mark_complete(self, item: PlanItem, result: VerificationResult) -> None:
        """항목을 완료/차단으로 표시하고 계획 문서 업데이트."""
        ...
    
    @abstractmethod
    def is_done(self, items: list[PlanItem]) -> bool:
        """모든 항목이 완료되었는지 확인.
        
        도메인별 완료 조건:
        - PRD: 모든 story passes=true
        - OPPLAN: 모든 objective completed 또는 justified blocked
        - BugBounty: 스코프 전체 커버 또는 시간 제한 도달
        """
        ...
    
    def format_status(self, items: list[PlanItem]) -> str:
        """현재 진행 상황을 LLM 컨텍스트 주입용 텍스트로 포맷."""
        total = len(items)
        done = sum(1 for i in items if i.status == ItemStatus.COMPLETED)
        blocked = sum(1 for i in items if i.status == ItemStatus.BLOCKED)
        return f"Progress: {done}/{total} completed, {blocked} blocked"
    
    def save(self, items: list[PlanItem], path: str) -> None:
        """계획 상태를 디스크에 영속화."""
        ...
```

### 3.2 PRD Adapter (개발)

```python
class PRDAdapter(PlanAdapter):
    """prd.json 기반 개발 태스크 어댑터."""
    
    def load(self, source: str) -> list[PlanItem]:
        with open(source) as f:
            prd = json.load(f)
        return [
            PlanItem(
                id=story["id"],
                title=story["title"],
                description=story.get("description", ""),
                acceptance_criteria=story["acceptanceCriteria"],
                priority=story["priority"],
                status=ItemStatus.COMPLETED if story["passes"] else ItemStatus.PENDING,
            )
            for story in prd["userStories"]
        ]
    
    def pick_next(self, items):
        pending = [i for i in items if i.status == ItemStatus.PENDING]
        return min(pending, key=lambda i: i.priority, default=None)
    
    def verify(self, item, execution_result):
        # 테스트 통과, 타입체크 통과, 린트 통과
        criteria_results = {}
        for criterion in item.acceptance_criteria:
            if "typecheck" in criterion.lower():
                criteria_results[criterion] = run_typecheck()
            elif "test" in criterion.lower():
                criteria_results[criterion] = run_tests()
            else:
                criteria_results[criterion] = True  # 에이전트 자체 검증
        
        passed = all(criteria_results.values())
        return VerificationResult(passed=passed, evidence=str(criteria_results),
                                  criteria_results=criteria_results)
    
    def mark_complete(self, item, result):
        item.status = ItemStatus.COMPLETED if result.passed else ItemStatus.BLOCKED
    
    def is_done(self, items):
        return all(i.status == ItemStatus.COMPLETED for i in items)
```

### 3.3 OPPLAN Adapter (레드팀)

```python
class OPPLANAdapter(PlanAdapter):
    """opplan.json 기반 레드팀 인게이지먼트 어댑터."""
    
    def load(self, source: str) -> list[PlanItem]:
        with open(source) as f:
            opplan = json.load(f)
        return [
            PlanItem(
                id=obj["id"],
                title=obj["title"],
                description=obj["description"],
                acceptance_criteria=obj["acceptance_criteria"],
                priority=obj["priority"],
                status=ItemStatus(obj["status"]),
                dependencies=obj.get("blocked_by", []),
                metadata={
                    "phase": obj["phase"],           # RECON, INITIAL_ACCESS, ...
                    "opsec_level": obj["opsec"],  # schema field is "opsec"
                    "c2_tier": obj.get("c2_tier"),
                    "owner": obj.get("owner"),        # recon/exploit/postexploit agent
                    "evidence": obj.get("evidence", ""),
                    "attempts": obj.get("attempts", 0),
                },
            )
            for obj in opplan["objectives"]
        ]
    
    def pick_next(self, items):
        # 의존성 충족 + pending/blocked 중 최고 우선순위
        completed_ids = {i.id for i in items if i.status == ItemStatus.COMPLETED}
        actionable = [
            i for i in items
            if i.status in (ItemStatus.PENDING, ItemStatus.BLOCKED)
            and (not i.dependencies or all(d in completed_ids for d in i.dependencies))
        ]
        # 킬체인 순서 우선, 그 다음 우선순위
        PHASE_ORDER = {"RECON": 0, "INITIAL_ACCESS": 1, "POST_EXPLOIT": 2, "C2": 3, "EXFILTRATION": 4}
        return min(actionable, 
                   key=lambda i: (PHASE_ORDER.get(i.metadata.get("phase", ""), 99), i.priority),
                   default=None)
    
    def verify(self, item, execution_result):
        criteria_results = {}
        for criterion in item.acceptance_criteria:
            if "evidence" in criterion.lower():
                # 증거 파일 존재 확인
                criteria_results[criterion] = bool(execution_result.get("evidence_path"))
            elif "roe" in criterion.lower():
                # RoE 준수 확인
                criteria_results[criterion] = execution_result.get("roe_compliant", False)
            else:
                criteria_results[criterion] = execution_result.get(criterion, False)
        
        passed = all(criteria_results.values())
        evidence = execution_result.get("evidence_summary", "")
        return VerificationResult(passed=passed, evidence=evidence,
                                  criteria_results=criteria_results)
    
    def mark_complete(self, item, result):
        if result.passed:
            item.status = ItemStatus.COMPLETED
            item.metadata["evidence"] = result.evidence
        else:
            item.status = ItemStatus.BLOCKED
            item.metadata["attempts"] = item.metadata.get("attempts", 0) + 1
    
    def is_done(self, items):
        # 모든 목표가 completed 또는 justified blocked
        return all(
            i.status == ItemStatus.COMPLETED
            or (i.status == ItemStatus.BLOCKED and i.metadata.get("attempts", 0) >= 3)
            for i in items
        )
    
    def format_status(self, items):
        # Battle Tracker 형식
        total = len(items)
        phases = {}
        for item in items:
            phase = item.metadata.get("phase", "UNKNOWN")
            phases.setdefault(phase, {"done": 0, "total": 0})
            phases[phase]["total"] += 1
            if item.status == ItemStatus.COMPLETED:
                phases[phase]["done"] += 1
        
        lines = ["<OPPLAN_STATUS>"]
        for phase, counts in phases.items():
            lines.append(f"  {phase}: {counts['done']}/{counts['total']}")
        lines.append("</OPPLAN_STATUS>")
        return "\n".join(lines)
```

### 3.4 Bug Bounty Adapter

```python
class BugBountyAdapter(PlanAdapter):
    """버그바운티 프로그램 스코프 기반 어댑터.
    
    HackerOne/Bugcrowd 프로그램 스코프를 자동으로 목표로 변환.
    각 in-scope 자산이 하나의 PlanItem이 됨.
    """
    
    def load(self, source: str) -> list[PlanItem]:
        # source: HackerOne program JSON 또는 스코프 파일
        with open(source) as f:
            program = json.load(f)
        
        items = []
        priority = 1
        
        for asset in program["scope"]["in_scope"]:
            # 자산 유형별 기본 테스트 항목 생성
            asset_type = asset["asset_type"]  # url, domain, mobile, api, ...
            target = asset["asset_identifier"]
            
            if asset_type in ("url", "domain"):
                # 웹 자산: 정찰 → OWASP Top 10 테스트
                items.extend([
                    PlanItem(
                        id=f"BB-{priority:03d}",
                        title=f"Recon: {target}",
                        description=f"Subdomain enum, port scan, tech fingerprint for {target}",
                        acceptance_criteria=[
                            f"Subdomain enumeration completed for {target}",
                            "Port scan results saved to evidence/",
                            "Technology stack identified",
                        ],
                        priority=priority,
                        metadata={"asset": target, "type": asset_type, "phase": "recon"},
                    ),
                    PlanItem(
                        id=f"BB-{priority+1:03d}",
                        title=f"OWASP Top 10: {target}",
                        description=f"Test {target} for OWASP Top 10 vulnerabilities",
                        acceptance_criteria=[
                            "SQLi testing completed on all input parameters",
                            "XSS testing completed on all reflective endpoints",
                            "Authentication bypass attempts documented",
                            "IDOR testing on all object references",
                        ],
                        priority=priority + 1,
                        dependencies=[f"BB-{priority:03d}"],  # recon first
                        metadata={"asset": target, "type": asset_type, "phase": "exploit"},
                    ),
                ])
                priority += 2
            
            elif asset_type == "api":
                items.append(PlanItem(
                    id=f"BB-{priority:03d}",
                    title=f"API Security: {target}",
                    description=f"Test API endpoints for auth, injection, rate limiting",
                    acceptance_criteria=[
                        "API endpoint enumeration completed",
                        "Authentication/authorization testing done",
                        "Input validation testing done",
                        "Rate limiting verified",
                    ],
                    priority=priority,
                    metadata={"asset": target, "type": asset_type, "phase": "exploit"},
                ))
                priority += 1
        
        return items
    
    def pick_next(self, items):
        # recon 먼저, 그다음 exploit
        completed_ids = {i.id for i in items if i.status == ItemStatus.COMPLETED}
        actionable = [
            i for i in items
            if i.status in (ItemStatus.PENDING, ItemStatus.BLOCKED)
            and (not i.dependencies or all(d in completed_ids for d in i.dependencies))
        ]
        PHASE_ORDER = {"recon": 0, "exploit": 1, "report": 2}
        return min(actionable,
                   key=lambda i: (PHASE_ORDER.get(i.metadata.get("phase", ""), 99), i.priority),
                   default=None)
    
    def verify(self, item, execution_result):
        criteria_results = {}
        for criterion in item.acceptance_criteria:
            criteria_results[criterion] = execution_result.get(criterion, False)
        
        passed = all(criteria_results.values())
        findings = execution_result.get("findings", [])
        evidence = f"{len(findings)} findings" if findings else "No findings"
        return VerificationResult(passed=passed, evidence=evidence,
                                  criteria_results=criteria_results)
    
    def is_done(self, items):
        return all(i.status in (ItemStatus.COMPLETED, ItemStatus.BLOCKED) for i in items)
```

## 4. Universal Ralph Loop Engine

### 4.1 엔진 구현

Plan Adapter와 조합되어 어떤 도메인이든 자율 실행하는 루프 엔진:

```python
class RalphLoopEngine:
    """Universal Ralph Loop. PlanAdapter를 받아 자율 실행."""
    
    def __init__(
        self,
        adapter: PlanAdapter,
        agent_spawner: AgentSpawner,    # 에이전트 생성 팩토리
        notifier: Notifier | None,      # Discord/Slack 알림 (OpenClaw juice)
        hooks: list[LoopHook] | None,   # OPSEC 가드레일 등 (OpenClaw juice)
        max_iterations: int = 100,
        progress_file: str = "progress.txt",
    ):
        self.adapter = adapter
        self.agent_spawner = agent_spawner
        self.notifier = notifier
        self.hooks = hooks or []
        self.max_iterations = max_iterations
        self.progress_file = progress_file
    
    async def run(self, plan_source: str) -> LoopResult:
        """메인 루프 실행."""
        items = self.adapter.load(plan_source)
        
        for iteration in range(1, self.max_iterations + 1):
            # 1. Status check
            if self.adapter.is_done(items):
                await self._notify(f"All items complete after {iteration-1} iterations")
                return LoopResult(success=True, iterations=iteration-1)
            
            # 2. Pick next
            item = self.adapter.pick_next(items)
            if item is None:
                await self._notify("No actionable items (all blocked or dependencies unmet)")
                return LoopResult(success=False, reason="deadlock")
            
            # 3. Pre-execution hooks
            for hook in self.hooks:
                await hook.before_execute(item, items)
            
            # 4. Spawn fresh agent + execute (clean context!)
            await self._notify(f"[{iteration}/{self.max_iterations}] "
                              f"Executing: {item.id} - {item.title}")
            
            item.status = ItemStatus.IN_PROGRESS
            agent = self.agent_spawner.spawn(
                item=item,
                context=self.adapter.format_status(items),
                progress=self._read_progress(),
            )
            execution_result = await agent.execute()
            
            # 5. Post-execution hooks
            for hook in self.hooks:
                await hook.after_execute(item, execution_result)
            
            # 6. Verify
            result = self.adapter.verify(item, execution_result)
            
            # 7. Mark
            self.adapter.mark_complete(item, result)
            self.adapter.save(items, plan_source)
            
            # 8. Record progress
            self._append_progress(item, result, iteration)
            
            # 9. Notify
            status = "PASSED" if result.passed else "BLOCKED"
            await self._notify(f"{item.id} {status}: {result.evidence}")
        
        return LoopResult(success=False, reason="max_iterations_reached")
```

### 4.2 에이전트 스포너

```python
class AgentSpawner(ABC):
    """에이전트 생성 팩토리. 도메인별 에이전트 풀을 관리."""
    
    @abstractmethod
    def spawn(self, item: PlanItem, context: str, progress: str) -> Agent:
        """PlanItem에 맞는 에이전트를 생성.
        
        매 반복마다 FRESH context로 생성 (Ralph 핵심 원칙).
        context와 progress만 주입.
        """
        ...

class DevAgentSpawner(AgentSpawner):
    """개발용: Claude Code / Codex 스폰."""
    def spawn(self, item, context, progress):
        return ClaudeCodeAgent(
            prompt=f"Implement: {item.title}\n{item.description}\n"
                   f"Criteria: {item.acceptance_criteria}\n"
                   f"Context: {context}\n"
                   f"Previous learnings: {progress}",
            permission_mode="bypassPermissions",
        )

class RedTeamAgentSpawner(AgentSpawner):
    """레드팀용: 전문 에이전트(recon/exploit/postexploit) 스폰."""
    def spawn(self, item, context, progress):
        phase = item.metadata.get("phase", "recon")
        agent_type = {
            "RECON": "recon",
            "INITIAL_ACCESS": "exploit",
            "POST_EXPLOIT": "postexploit",
            "C2": "postexploit",
            "EXFILTRATION": "postexploit",
        }.get(phase, "recon")
        
        return DecepticonAgent(
            agent_type=agent_type,
            sandbox=DockerKaliSandbox(),
            objective=item,
            roe=self.roe,  # Rules of Engagement 주입
            context=context,
            progress=progress,
        )
```

## 5. OpenClaw Juice Extraction

OpenClaw에서 추출하여 Ralph Loop를 강화하는 패턴들:

### 5.1 Cron → 스케줄 기반 자율 실행

```
OpenClaw Pattern:
  CronService → isolated session → announce to channel

Decepticon 적용:
  ScanScheduler → fresh Ralph iteration → announce to Discord
```

**가치**: Ralph Loop를 특정 시간대에만 실행 (레드팀 night window), 주기적 재스캔 (서브도메인 변경 감지), 일정 기반 자동 시작.

```python
# OpenClaw cron 패턴 적용
class ScheduledRalphLoop:
    async def start_scheduled(self, schedule: str, plan_source: str):
        """cron 표현식으로 Ralph Loop 스케줄링."""
        # "0 22 * * *" → 매일 22:00에 시작
        # "0 2 * * *"  → 매일 02:00에 시작 (야간 윈도우)
        while True:
            await wait_for_schedule(schedule)
            await self.engine.run(plan_source)
            await self.notifier.send("Ralph iteration batch complete")
```

### 5.2 Session Isolation → 병렬 목표 실행

```
OpenClaw Pattern:
  sessions_spawn → isolated session key → parallel execution

Decepticon 적용:
  AgentPool → per-objective sandbox → parallel execution
```

**가치**: 여러 목표를 동시에 실행. 각 목표가 독립 Docker sandbox에서 격리 실행.

```python
class ParallelRalphEngine(RalphLoopEngine):
    """병렬 실행 가능한 Ralph Loop. 독립 목표를 동시 실행."""
    
    async def run_parallel(self, plan_source: str, max_concurrent: int = 3):
        items = self.adapter.load(plan_source)
        
        while not self.adapter.is_done(items):
            # 병렬 실행 가능한 항목들 선택
            actionable = self._get_parallel_actionable(items, max_concurrent)
            
            # 동시 실행 (각각 독립 sandbox)
            tasks = [
                self._execute_single(item, items)
                for item in actionable
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 반영
            for item, result in zip(actionable, results):
                if isinstance(result, Exception):
                    item.status = ItemStatus.BLOCKED
                    item.metadata["failure_reason"] = str(result)
                # ...
```

### 5.3 Hooks → OPSEC 가드레일

```
OpenClaw Pattern:
  before_tool_call / after_tool_call hooks

Decepticon 적용:
  before_execute / after_execute hooks for OPSEC
```

**가치**: 모든 에이전트 액션에 RoE 검증, 속도 제한, 증거 캡처를 자동 적용.

```python
class OPSECHook(LoopHook):
    """OPSEC 가드레일 훅."""
    
    async def before_execute(self, item, all_items):
        # RoE 범위 검증
        if not self.roe.is_in_scope(item.metadata.get("target")):
            raise OPSECViolation(f"Target not in scope: {item.metadata['target']}")
        
        # 시간 윈도우 검증
        if not self.roe.is_within_time_window():
            raise OPSECViolation("Outside permitted time window")
        
        # 노이즈 레벨 검증
        if item.metadata.get("opsec_level") == "quiet" and self._recent_scan_count() > 10:
            raise OPSECViolation("Too many scans for quiet OPSEC level")
    
    async def after_execute(self, item, result):
        # 증거 자동 캡처
        await self.evidence_store.capture(item, result)
        
        # Knowledge Graph 업데이트
        await self.kg.update_from_result(item, result)
        
        # 디컨플릭션 체크
        await self.deconfliction.check(item, result)
```

### 5.4 Event Streaming → Discord 실시간 보고

```
OpenClaw Pattern:
  agent events → WS stream → channel delivery

Decepticon 적용:
  Ralph events → Discord thread → real-time reporting
```

**가치**: Ralph Loop 실행 중 진행 상황을 Discord에 실시간 보고.

```python
class DiscordNotifier(Notifier):
    """Discord 스레드에 Ralph 진행 상황 실시간 보고."""
    
    async def send(self, message: str):
        await self.discord_channel.send(message)
    
    async def stream_execution(self, item, agent):
        """에이전트 실행을 실시간 스트리밍."""
        thread = await self.create_thread(f"🦞 {item.id}: {item.title}")
        
        async for event in agent.stream():
            match event.type:
                case "tool_call":
                    await thread.send(f"🔧 `{event.tool}`: {event.summary}")
                case "finding":
                    await thread.send(f"🔴 **Finding**: {event.description}")
                case "progress":
                    await thread.send(f"📊 {event.message}")
                case "complete":
                    await thread.send(f"✅ {item.id} complete: {event.evidence}")
```

### 5.5 Taskflow → Crash Recovery

```
OpenClaw Pattern:
  durable flow with managed lifecycle

Decepticon 적용:
  Ralph state persistence with auto-resume
```

**가치**: Gateway/에이전트 크래시 후 마지막 상태에서 자동 재개.

```python
class DurableRalphEngine(RalphLoopEngine):
    """크래시 복구 가능한 Ralph Loop."""
    
    async def run(self, plan_source: str):
        # 이전 실행 상태 복구
        state = await self.state_store.load_or_create(plan_source)
        items = state.items or self.adapter.load(plan_source)
        iteration = state.last_iteration + 1
        
        try:
            for i in range(iteration, self.max_iterations + 1):
                state.last_iteration = i
                await self.state_store.save(state)
                
                # ... normal loop ...
        except Exception as e:
            state.error = str(e)
            await self.state_store.save(state)
            await self._notify(f"Ralph paused at iteration {i}: {e}")
            raise
```

## 6. 도메인 확장 가이드

### 6.1 새 도메인 추가하기

Ralph Loop에 새 도메인을 추가하려면 **PlanAdapter만 구현**하면 된다:

```python
# 1. Plan 문서 형식 정의 (JSON/YAML/etc.)
# 2. PlanAdapter 서브클래스 구현
# 3. AgentSpawner 서브클래스 구현 (선택)
# 4. 도메인별 Hook 추가 (선택)

class MyDomainAdapter(PlanAdapter):
    def load(self, source): ...
    def pick_next(self, items): ...
    def verify(self, item, result): ...
    def mark_complete(self, item, result): ...
    def is_done(self, items): ...
```

### 6.2 잠재적 도메인 확장

| Domain | Plan Document | Item | Verification |
|--------|---------------|------|-------------|
| **개발** | PRD (prd.json) | User Story | 테스트 통과, 타입체크 |
| **레드팀** | OPPLAN (opplan.json) | Objective | 증거 수집, RoE 준수 |
| **버그바운티** | Program Scope | Asset + Test | PoC 작성, 재현 가능 |
| **인프라** | Runbook | Step | 상태 체크, 헬스체크 |
| **QA** | Test Plan | Test Case | Pass/Fail + screenshot |
| **문서** | Doc Plan | Section | 검토 통과, 링크 유효 |
| **마이그레이션** | Migration Plan | Migration Step | 롤백 가능, 데이터 무결성 |
| **컴플라이언스** | Audit Checklist | Control | 증빙 수집, 감사 통과 |

## 7. Decepticon 구현 블루프린트

### 7.1 파일 구조

```
decepticon/
  ralph/                          (신규 — Universal Ralph Engine)
    engine.py                     # RalphLoopEngine
    adapters/
      base.py                     # PlanAdapter ABC
      opplan_adapter.py           # OPPLAN → PlanItem
      bugbounty_adapter.py        # BugBounty → PlanItem
    spawners/
      base.py                     # AgentSpawner ABC
      redteam_spawner.py          # 전문 에이전트 스폰
    hooks/
      opsec.py                    # OPSEC 가드레일
      evidence.py                 # 증거 자동 캡처
      roe_validator.py            # RoE 검증
    notifiers/
      discord.py                  # Discord 실시간 보고
      base.py                     # Notifier ABC
    scheduler.py                  # Cron 기반 스케줄러
    state.py                      # Durable state (crash recovery)
```

### 7.2 기존 코드와의 연결점

```
기존 Decepticon              →   Universal Ralph
─────────────────────────────────────────────────
agents/decepticon.py (orch.) →   RalphLoopEngine.run()
opplan.py (OPPLAN middleware)→   OPPLANAdapter
recon.py / exploit.py / ...  →   RedTeamAgentSpawner
docker_sandbox.py            →   Agent execution backend
safe_command.py              →   OPSECHook
subagent_streaming.py        →   Event streaming → Notifier
knowledge_graph              →   after_execute hook → KG update
reporting/                   →   is_done() → auto-report generation
```

### 7.3 시퀀스 다이어그램

```
Developer          Discord        RedGate         RalphLoop        Sandbox
    |                 |               |               |               |
    |  "start BB      |               |               |               |
    |   example.com"  |               |               |               |
    |---------------->|               |               |               |
    |                 |  route msg    |               |               |
    |                 |-------------->|               |               |
    |                 |               |  load plan    |               |
    |                 |               |-------------->|               |
    |                 |               |               | pick_next()   |
    |                 |               |               |------+        |
    |                 |               |               |      |        |
    |                 |  "starting    |               |<-----+        |
    |                 |   BB-001..."  |               |               |
    |                 |<--------------|               |               |
    |                 |               |               | spawn agent   |
    |                 |               |               |-------------->|
    |   zzz (sleep)   |               |               |               |
    |                 |               |               |  execute in   |
    |                 |               |               |  Kali sandbox |
    |                 |               |               |               |
    |                 |               |               |  verify()     |
    |                 |               |               |------+        |
    |                 |               |               |<-----+        |
    |                 |               |               | mark_complete |
    |                 |  "BB-001      |               |               |
    |                 |   PASSED"     |               |               |
    |                 |<---------------------------------+            |
    |                 |               |               |               |
    |                 |               |               | pick_next()   |
    |                 |               |               | (loop...)     |
    |                 |               |               |               |
    |                 |  "All done!   |               |               |
    |                 |   5 findings" |               |               |
    |                 |<---------------------------------+            |
    |  wake up        |               |               |               |
    |  check Discord  |               |               |               |
```

## 8. 핵심 요약

| 개념 | 설명 |
|------|------|
| **Universal Pattern** | Plan → Pick → Execute → Verify → Mark → Repeat |
| **Plan Adapter** | 도메인별 계획 문서를 통일 인터페이스로 변환 |
| **Fresh Context** | 매 반복마다 새 에이전트 (컨텍스트 오염 방지) |
| **Memory Model** | plan.json + progress.txt + git (반복 간 지속) |
| **Completion Signal** | `adapter.is_done()` — 모든 항목 완료 시 종료 |
| **OpenClaw Juice** | Cron(스케줄), Session(병렬), Hooks(가드레일), Events(보고), Taskflow(복구) |
| **Domain Extension** | PlanAdapter만 구현하면 어떤 도메인이든 확장 가능 |
| **Decepticon 적용** | OPPLAN/BugBounty Adapter + OPSEC Hooks + Discord Notifier |
