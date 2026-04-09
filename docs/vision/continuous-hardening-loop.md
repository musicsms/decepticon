# Continuous Hardening Loop

> Attack-Defense Ralph Loop를 통한 24/7 자율 보안 강화 시스템

## 1. Loop 개요

Continuous Hardening Loop는 **공격 → 발견 → 피드백 → 방어 → 검증**을 무한 반복하는 자율 시스템이다. 시간이 지날수록 시스템은 자동으로 더 강해진다.

```
        ┌─────────────────────────────────────────┐
        │        CONTINUOUS HARDENING LOOP         │
        │                                         │
        │   ┌─────────┐                           │
  ┌────>│   │  RECON   │  정찰: 공격 표면 분석     │
  │     │   └────┬────┘                           │
  │     │        │                                │
  │     │   ┌────▼────┐                           │
  │     │   │  ATTACK  │  공격: 취약점 익스플로잇   │
  │     │   └────┬────┘                           │
  │     │        │                                │
  │     │   ┌────▼────┐                           │
  │     │   │ FINDING  │  발견: 취약점 + 증거       │
  │     │   └────┬────┘                           │
  │     │        │                                │
  │     │   ┌────▼────┐                           │
  │     │   │FEEDBACK  │  피드백: 방어 액션 생성    │
  │     │   └────┬────┘                           │
  │     │        │                                │
  │     │   ┌────▼────┐                           │
  │     │   │ DEFENSE  │  방어: 패치/규칙/설정      │
  │     │   └────┬────┘                           │
  │     │        │                                │
  │     │   ┌────▼────┐                           │
  │     │   │ VERIFY   │  검증: 재공격으로 확인     │
  │     │   └────┬────┘                           │
  │     │        │                                │
  │     │        │  immune? ──YES──→ ✅ 면역       │
  │     │        │                                │
  └─────│────────┘  NO → 🔄 다음 반복             │
        │                                         │
        └─────────────────────────────────────────┘
```

## 2. AttackDefensePlanAdapter

### 2.1 설계

```python
class AttackDefensePlanAdapter(PlanAdapter):
    """공격-방어 통합 Ralph Loop 어댑터.
    
    하나의 루프 안에서:
    1. 공격 OPPLAN 실행 → Findings 생성
    2. Findings → Defense OPPLAN 자동 생성
    3. Defense OPPLAN 실행 → 방어 적용
    4. 재공격으로 검증 → 면역 확인
    """
    
    def __init__(self, roe: RulesOfEngagement):
        self.roe = roe
        self.attack_adapter = OPPLANAdapter()
        self.defense_adapter = DefenseOPPLANAdapter()
        self.feedback_pipeline = FeedbackPipeline()
    
    def load(self, source: str) -> list[PlanItem]:
        """공격 + 방어 항목을 통합 로드."""
        attack_items = self.attack_adapter.load(f"{source}/attack-opplan.json")
        
        # 방어 OPPLAN이 있으면 로드, 없으면 빈 상태로 시작
        defense_path = f"{source}/defense-opplan.json"
        if Path(defense_path).exists():
            defense_items = self.defense_adapter.load(defense_path)
        else:
            defense_items = []
        
        # 모든 항목에 lane 태그 부여
        for item in attack_items:
            item.metadata["lane"] = "attack"
        for item in defense_items:
            item.metadata["lane"] = "defense"
        
        return attack_items + defense_items
    
    def pick_next(self, items: list[PlanItem]) -> PlanItem | None:
        """다음 실행 항목 선택. 공격 우선, 방어 후순위."""
        
        # Phase 1: 미완료 공격 목표 확인
        attack_pending = [
            i for i in items 
            if i.metadata.get("lane") == "attack"
            and i.status in (ItemStatus.PENDING, ItemStatus.IN_PROGRESS)
        ]
        if attack_pending:
            return self.attack_adapter.pick_next(attack_pending)
        
        # Phase 2: 공격 완료 → Findings에서 방어 목표 자동 생성
        attack_completed = [
            i for i in items
            if i.metadata.get("lane") == "attack"
            and i.status == ItemStatus.COMPLETED
        ]
        existing_defense = [
            i for i in items if i.metadata.get("lane") == "defense"
        ]
        
        # 아직 방어 목표가 생성되지 않은 Finding이 있으면 생성
        new_defense = self._generate_defense_items(attack_completed, existing_defense)
        if new_defense:
            items.extend(new_defense)
            self.save(items, self._current_source)
        
        # Phase 3: 방어 목표 선택
        defense_pending = [
            i for i in items
            if i.metadata.get("lane") == "defense"
            and i.status in (ItemStatus.PENDING, ItemStatus.IN_PROGRESS)
        ]
        if defense_pending:
            return self.defense_adapter.pick_next(defense_pending)
        
        # Phase 4: 검증 목표 선택 (적용된 방어의 재공격 검증)
        verification_pending = [
            i for i in items
            if i.metadata.get("lane") == "defense"
            and i.status == ItemStatus.COMPLETED
            and not i.metadata.get("verified", False)
        ]
        if verification_pending:
            return self._create_verification_item(verification_pending[0])
        
        return None  # 모든 항목 완료
    
    def verify(self, item: PlanItem, result: Any) -> VerificationResult:
        """항목 유형에 따라 검증."""
        lane = item.metadata.get("lane")
        
        if lane == "attack":
            return self.attack_adapter.verify(item, result)
        elif lane == "defense":
            return self.defense_adapter.verify(item, result)
        elif lane == "verification":
            # 재공격 결과: 차단되면 immune
            blocked = result.get("attack_blocked", False)
            return VerificationResult(
                passed=blocked,
                evidence="Attack blocked by defense" if blocked else "Defense bypassed",
                criteria_results={"immune": blocked},
            )
    
    def is_done(self, items: list[PlanItem]) -> bool:
        """모든 공격 완료 + 모든 방어 검증됨."""
        attack_done = all(
            i.status in (ItemStatus.COMPLETED, ItemStatus.BLOCKED)
            for i in items if i.metadata.get("lane") == "attack"
        )
        defense_verified = all(
            i.metadata.get("verified", False)
            for i in items if i.metadata.get("lane") == "defense"
        )
        return attack_done and defense_verified
    
    def format_status(self, items: list[PlanItem]) -> str:
        """Battle Tracker + Defense Tracker."""
        attack = [i for i in items if i.metadata.get("lane") == "attack"]
        defense = [i for i in items if i.metadata.get("lane") == "defense"]
        
        a_done = sum(1 for i in attack if i.status == ItemStatus.COMPLETED)
        d_done = sum(1 for i in defense if i.metadata.get("verified"))
        immune = sum(1 for i in defense if i.metadata.get("immune"))
        
        return (
            f"<HARDENING_STATUS>\n"
            f"  Attack:  {a_done}/{len(attack)} objectives completed\n"
            f"  Defense: {d_done}/{len(defense)} remediations applied\n"
            f"  Immune:  {immune}/{len(defense)} verified immune\n"
            f"  Convergence: {immune/max(len(defense),1)*100:.0f}%\n"
            f"</HARDENING_STATUS>"
        )
```

### 2.2 Defense Item 자동 생성

```python
def _generate_defense_items(
    self, 
    completed_attacks: list[PlanItem],
    existing_defense: list[PlanItem],
) -> list[PlanItem]:
    """완료된 공격 목표에서 방어 목표를 자동 생성."""
    
    existing_finding_ids = {
        d.metadata.get("source_finding") for d in existing_defense
    }
    
    new_items = []
    for attack in completed_attacks:
        findings = attack.metadata.get("findings", [])
        for finding in findings:
            if finding["id"] in existing_finding_ids:
                continue  # 이미 방어 목표 존재
            
            for action in finding.get("remediation_actions", []):
                new_items.append(PlanItem(
                    id=f"DEF-{len(existing_defense) + len(new_items) + 1:03d}",
                    title=f"{action['type']}: {finding['title']}",
                    description=action["description"],
                    acceptance_criteria=[
                        f"Remediation applied to {action['target_system']}",
                        f"No service disruption detected",
                        f"Re-attack on {finding['target']} is blocked",
                    ],
                    priority={"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
                        .get(finding["severity"], 5),
                    dependencies=[attack.id],
                    metadata={
                        "lane": "defense",
                        "source_finding": finding["id"],
                        "action": action,
                        "severity": finding["severity"],
                        "verified": False,
                        "immune": False,
                    },
                ))
    
    return new_items
```

## 3. Loop Phases (상세)

### Phase 1: Recon (정찰)

```
입력: 스코프 정의 (도메인, IP 범위, 서비스)
에이전트: Recon Agent
도구: nmap, subfinder, nuclei, httpx, whois

출력:
  ├── 공격 표면 맵 (subdomains, ports, services)
  ├── 기술 스택 (web server, frameworks, libraries)
  ├── 잠재적 진입점 (exposed services, default creds)
  └── KG 업데이트 (Target nodes)
```

### Phase 2: Attack (공격)

```
입력: Recon 결과 + OPPLAN 목표
에이전트: Exploit Agent, PostExploit Agent, CloudHunter, ADOperator
도구: sqlmap, metasploit, burpsuite, impacket, bloodhound

출력:
  ├── 성공한 익스플로잇 목록
  ├── 획득한 크리덴셜/접근
  ├── 횡방향 이동 경로
  └── 각 성공에 대한 Finding 생성
```

### Phase 3: Finding (발견)

```
입력: 공격 결과
처리: FeedbackPipeline.extract_findings()

출력 (Finding 객체):
  ├── id: FIND-001
  ├── severity: CRITICAL
  ├── target: api.example.com
  ├── cwe_id: CWE-89
  ├── evidence: PoC + 스크린샷
  ├── root_cause: "Unsanitized input in SQL query"
  └── remediation_actions: [WAF rule, Code patch, Detection rule]
```

### Phase 4: Feedback (피드백)

```
입력: Finding 객체들
처리: FeedbackPipeline.generate_defense_opplan()

변환 과정:
  1. Finding 분류 (CWE → 방어 유형 매핑)
  2. RemediationAction 생성 (구체적 방어 액션)
  3. 우선순위 결정 (severity × 서비스 중단 위험)
  4. 승인 요구사항 결정 (자동 vs 인간)
  5. Defense OPPLAN 생성

출력: Defense OPPLAN (자동 생성)
```

### Phase 5: Defense (방어)

```
입력: Defense OPPLAN
에이전트: WAF Agent, Patch Agent, Config Agent, Detection Agent

실행:
  ├── WAF Agent: ModSecurity/Cloudflare 규칙 추가
  ├── Patch Agent: 코드 패치 생성 → PR → CI
  ├── Config Agent: 서버 설정 강화
  ├── Detection Agent: Sigma/YARA 규칙 배포
  └── Network Agent: 방화벽 정책 업데이트

출력: Applied remediations
```

### Phase 6: Verify (검증)

```
입력: 적용된 방어 액션 목록
에이전트: Exploit Agent (재공격 모드)

검증:
  ├── 같은 공격 벡터로 재공격 시도
  ├── 차단됨 → Finding status: "immune" ✅
  ├── 통과됨 → 방어 재조정 필요 🔄
  └── 서비스 정상 여부 확인

출력: Verification results + Immunity status
```

## 4. Metrics & Convergence

### 4.1 핵심 메트릭

```python
@dataclass
class HardeningMetrics:
    """Continuous Hardening Loop 메트릭."""
    
    # 진행도
    total_objectives: int          # 전체 공격 목표 수
    completed_objectives: int      # 완료된 공격 목표
    total_findings: int            # 발견된 취약점 수
    total_remediations: int        # 적용된 방어 수
    verified_immune: int           # 면역 확인된 수
    
    # 수렴도
    convergence_rate: float        # immune / total_findings (0.0 → 1.0)
    findings_per_iteration: list[int]  # 반복별 발견 수 (감소 추세)
    
    # 시간
    total_iterations: int          # 총 반복 수
    total_runtime_hours: float     # 총 실행 시간
    avg_remediation_time: float    # 평균 방어 적용 시간 (분)
    avg_verification_time: float   # 평균 검증 시간 (분)
    
    # 심각도 분포
    severity_distribution: dict[str, int]  # CRITICAL: 3, HIGH: 5, ...
    immune_by_severity: dict[str, int]     # CRITICAL: 3, HIGH: 4, ...
    
    @property
    def is_converged(self) -> bool:
        """수렴 여부. 마지막 3회 반복에서 발견 0이면 수렴."""
        if len(self.findings_per_iteration) < 3:
            return False
        return all(f == 0 for f in self.findings_per_iteration[-3:])
    
    def trend(self) -> str:
        """추세 분석."""
        if len(self.findings_per_iteration) < 2:
            return "insufficient_data"
        recent = self.findings_per_iteration[-1]
        previous = self.findings_per_iteration[-2]
        if recent < previous:
            return "improving"
        elif recent == previous == 0:
            return "converged"
        elif recent > previous:
            return "degrading"  # 새 취약점 발견 (코드 변경 등)
        return "stable"
```

### 4.2 수렴 그래프

```
Convergence Dashboard:

Findings per Iteration:
  10 │ ██████████
   8 │ ████████
   5 │ █████
   3 │ ███
   1 │ █
   0 │              ← CONVERGED
     └──────────────
       1  2  3  4  5

Immunity Progress:
  100% │                    ██████████
   80% │               █████
   60% │          █████
   40% │     █████
   20% │ ████
    0% │
       └──────────────────────────────
         1  2  3  4  5  6  7  8  9  10

Severity Breakdown:
  CRITICAL: ████████ 8/8 immune (100%) ✅
  HIGH:     ██████── 6/8 immune (75%)
  MEDIUM:   ████──── 4/8 immune (50%)
  LOW:      ██────── 2/8 immune (25%)
```

### 4.3 수렴 조건

```python
class ConvergenceCriteria:
    """루프 종료 조건."""
    
    # 기본 수렴 (모든 known 취약점 면역)
    all_immune: bool = True
    
    # 시간 기반 (최대 실행 시간)
    max_runtime_hours: float = 48.0
    
    # 반복 기반 (최대 반복 수)
    max_iterations: int = 100
    
    # 추세 기반 (N회 연속 0 발견)
    zero_findings_streak: int = 3
    
    # 면역률 기반 (N% 이상)
    min_immunity_rate: float = 0.95  # 95%
    
    def should_stop(self, metrics: HardeningMetrics) -> tuple[bool, str]:
        if metrics.is_converged:
            return True, "converged: zero findings for 3 consecutive iterations"
        if metrics.convergence_rate >= self.min_immunity_rate:
            return True, f"immunity rate {metrics.convergence_rate:.0%} >= {self.min_immunity_rate:.0%}"
        if metrics.total_iterations >= self.max_iterations:
            return True, f"max iterations reached: {self.max_iterations}"
        if metrics.total_runtime_hours >= self.max_runtime_hours:
            return True, f"max runtime reached: {self.max_runtime_hours}h"
        return False, "continuing"
```

## 5. Scheduling & 24/7 Operation

### 5.1 Cron 기반 스케줄링

```python
# OpenClaw CronService 패턴 적용
class HardeningScheduler:
    """지속적 강화 루프 스케줄러."""
    
    schedules = {
        # 야간 전체 사이클 (공격 + 방어 + 검증)
        "nightly_full": CronJob(
            schedule="0 22 * * *",       # 매일 22:00
            tz="Asia/Seoul",
            task="full_hardening_cycle",
            params={"max_iterations": 20},
            announce="discord:#security",
        ),
        
        # 주기적 정찰 (6시간마다)
        "periodic_recon": CronJob(
            schedule="0 */6 * * *",
            task="recon_only",
            params={"check_new_assets": True},
            announce="discord:#recon",
        ),
        
        # 즉시 방어 (Finding 발생 시)
        "on_finding": EventTrigger(
            event="finding.critical",
            task="immediate_defense",
            params={"auto_approve": False},  # CRITICAL은 인간 승인
            announce="discord:#alerts",
        ),
        
        # 주간 수렴 보고서
        "weekly_report": CronJob(
            schedule="0 9 * * 1",        # 매주 월요일 09:00
            tz="Asia/Seoul",
            task="convergence_report",
            announce="discord:#reports",
        ),
    }
```

### 5.2 Night Window 운용

```
Night Window Operation:

22:00 KST ── 시작 ──────────────────────────── 06:00 KST
  │                                              │
  ├── 22:00-23:00: Recon (정찰)                  │
  │   └── 서브도메인, 포트, 서비스 스캔          │
  │                                              │
  ├── 23:00-02:00: Attack (공격)                 │
  │   └── 발견된 취약점 익스플로잇               │
  │                                              │
  ├── 02:00-03:00: Feedback (피드백)             │
  │   └── Findings → Defense OPPLAN 생성         │
  │                                              │
  ├── 03:00-05:00: Defense (방어)                │
  │   └── WAF 규칙, 패치, 설정 적용             │
  │                                              │
  ├── 05:00-06:00: Verify (검증)                 │
  │   └── 재공격으로 면역 확인                   │
  │                                              │
  └── 06:00: 종료 + Discord 보고서               │

운영자는 아침에 확인:
  - 발견된 취약점 수
  - 자동 적용된 방어 수
  - 면역 확인된 수
  - 인간 승인 대기 항목
```

### 5.3 이벤트 기반 실행

```python
class EventDrivenHardening:
    """이벤트 기반 즉시 방어."""
    
    async def on_critical_finding(self, finding: Finding):
        """CRITICAL 취약점 발견 시 즉시 대응."""
        
        # 1. 즉시 Discord 알림
        await self.notify(
            channel="#alerts",
            message=f"🔴 CRITICAL: {finding.title}\n"
                    f"Target: {finding.target}\n"
                    f"CVSS: {finding.cvss_score}",
        )
        
        # 2. 자동화 가능한 방어 즉시 적용
        for action in finding.remediation_actions:
            if action.automatable and not action.requires_approval:
                await self.defensive_lane.apply(action)
                await self.notify(
                    channel="#defense",
                    message=f"🛡️ Auto-applied: {action.description}",
                )
        
        # 3. 승인 필요 항목 Discord에 대기
        approval_needed = [
            a for a in finding.remediation_actions
            if a.requires_approval
        ]
        if approval_needed:
            await self.notify(
                channel="#approvals",
                message=f"⏳ Approval needed for {len(approval_needed)} actions\n"
                        + "\n".join(f"  - {a.description}" for a in approval_needed),
            )
```

## 6. Concrete Scenario: End-to-End

### 6.1 시나리오: E-Commerce 웹사이트 강화

```
[22:00] Hardening Loop 시작
        대상: shop.example.com
        스코프: *.example.com

[22:15] Recon Agent 완료
        - 12 subdomains 발견
        - 47 open ports
        - Tech: nginx/1.25, Node.js, PostgreSQL
        → KG 업데이트

[22:30] Attack Agent: SQLi on /api/products?category=
        - Type: UNION-based blind
        - DB: PostgreSQL 15.2
        - Tables: users, orders, payments
        → FIND-001 생성 (CRITICAL, CVSS 9.1)

[22:45] Attack Agent: XSS on /search?q=
        - Type: Reflected XSS
        - No CSP header
        → FIND-002 생성 (HIGH, CVSS 6.1)

[23:00] Attack Agent: IDOR on /api/orders/{id}
        - 다른 사용자 주문 열람 가능
        → FIND-003 생성 (HIGH, CVSS 7.5)

[23:15] Feedback Pipeline 실행
        FIND-001 → DEF-001 (WAF SQLi rule, auto)
                   DEF-002 (Code patch, PR)
        FIND-002 → DEF-003 (CSP header, auto)
                   DEF-004 (XSS sanitization, PR)
        FIND-003 → DEF-005 (Auth middleware, PR)

[23:20] Discord #alerts:
        "🔴 CRITICAL: SQL Injection on /api/products
         3 findings total, 2 auto-applicable, 3 need PR review"

[23:30] WAF Agent: DEF-001 적용
        ModSecurity rule added: block SQLi on category param
        → Status: applied ✅

[23:35] Config Agent: DEF-003 적용
        nginx: Content-Security-Policy header added
        → Status: applied ✅

[23:40] Patch Agent: DEF-002, DEF-004, DEF-005
        3 PRs 생성:
        - PR #142: Fix SQLi in products API
        - PR #143: Add XSS sanitization to search
        - PR #144: Add auth check to orders API
        → Status: awaiting_approval (Discord 알림)

[02:00] 운영자 아침 (또는 자동 머지):
        PR #142, #143, #144 approved + merged

[02:30] Verify: 재공격 시도
        FIND-001 재시도 → WAF 차단 (403) → immune ✅
        FIND-002 재시도 → CSP 차단 → immune ✅
        FIND-003 재시도 → 코드 배포 대기중 → pending

[03:00] CI/CD 배포 완료 (PR #144)
        FIND-003 재시도 → 401 Unauthorized → immune ✅

[03:05] Discord #reports:
        "🛡️ Hardening Cycle Complete
         Findings: 3 (1 CRITICAL, 2 HIGH)
         Remediated: 3/3
         Immune: 3/3 (100%)
         Convergence: 100% for this cycle"

[06:00] 다음 사이클 스케줄:
        - 새 코드 배포 후 재스캔 (regression check)
        - 추가 공격 벡터 시도 (이전에 안 해본 것)
        - OSINT 업데이트 (새 서브도메인 확인)
```

## 7. 기술적 고려사항

### 7.1 공격-방어 타이밍

```
고려: 공격 중 방어가 적용되면 혼란 발생

해결: Phase-based 실행
  - 공격 Phase 완료 → Findings 확정
  - 방어 Phase 시작 → 방어 적용
  - 검증 Phase → 재공격
  - 동시 실행 아님 (순차)

예외: CRITICAL 즉시 방어
  - 공격 중이라도 CRITICAL Finding → 즉시 WAF 차단
  - 나머지 방어는 Phase 대로
```

### 7.2 오탐 관리

```
False Positive 방지:

1. PoC 기반 확인
   - Finding은 PoC 성공 시에만 생성
   - 스캐너 결과만으로는 Finding 안됨

2. 방어 전 카나리아
   - WAF 규칙: monitor 모드로 먼저 적용
   - 정상 트래픽 차단 여부 확인
   - 문제 없으면 block 모드로 전환

3. 자동 롤백
   - 서비스 헬스체크 실패 시 자동 롤백
   - 롤백 후 Discord 알림
```

### 7.3 상태 영속성

```python
# 루프 상태 영속화 (crash recovery)
class HardeningLoopState:
    attack_opplan: OPPLAN           # 공격 계획 상태
    defense_opplan: DefenseOPPLAN   # 방어 계획 상태
    findings: list[Finding]          # 발견 목록
    metrics: HardeningMetrics       # 메트릭
    current_phase: str              # "recon"/"attack"/"defense"/"verify"
    current_iteration: int          # 현재 반복 번호
    last_checkpoint: datetime       # 마지막 체크포인트
    
    # Crash recovery
    def save(self, path: str):
        """JSON으로 영속화."""
        with open(path, "w") as f:
            json.dump(asdict(self), f, default=str)
    
    @classmethod
    def load(cls, path: str) -> "HardeningLoopState":
        """이전 상태에서 복구."""
        with open(path) as f:
            data = json.load(f)
        return cls(**data)
```

## 8. Dashboard & Reporting

### 8.1 Discord 실시간 보고

```
Discord 채널 구조:
  #hardening-control  → 루프 시작/종료, 설정 변경
  #attack-log        → 공격 진행 상황, Finding 알림
  #defense-log       → 방어 적용 상황
  #alerts            → CRITICAL/HIGH 즉시 알림
  #approvals         → 인간 승인 대기 항목
  #reports           → 일간/주간 수렴 보고서
```

### 8.2 수렴 보고서 형식

```markdown
# Hardening Report — 2026-04-10

## Summary
- **Cycle**: #7 (nightly)
- **Duration**: 22:00 - 05:30 KST (7.5h)
- **Convergence**: 87% → 94% (+7%)

## Findings
| ID | Severity | Target | Status |
|----|----------|--------|--------|
| FIND-042 | HIGH | api.example.com/users | immune ✅ |
| FIND-043 | MEDIUM | cdn.example.com | immune ✅ |
| FIND-044 | LOW | blog.example.com | remediated, pending verify |

## Defenses Applied
| ID | Type | Target | Automated |
|----|------|--------|-----------|
| DEF-089 | WAF Rule | ModSecurity | Yes (auto) |
| DEF-090 | Code Patch | PR #156 | Yes (approved) |
| DEF-091 | Config | nginx CSP | Yes (auto) |

## Trend
Finding per cycle: 8 → 5 → 3 → 2 → 1 (improving ↓)
Immunity rate: 67% → 75% → 83% → 89% → 94% (improving ↑)

## Next Cycle
- Scheduled: 2026-04-11 22:00 KST
- Focus: New subdomains detected, regression check on PR #156
```

## 9. 핵심 요약

```
Continuous Hardening Loop = 
  AttackDefensePlanAdapter 
  + RalphLoopEngine 
  + HardeningScheduler 
  + Convergence Metrics

한 문장: 
  "공격 에이전트가 찾고, 방어 에이전트가 고치고, 
   재공격으로 검증하는 무한 루프가 
   시스템을 스스로 강하게 만든다."

수렴:
  반복할수록 발견되는 취약점이 줄어들고,
  면역률이 높아지고,
  시스템이 견고해진다.
  
  Every attack makes us stronger.
```
