# Attack-Defense Agent Architecture

> 공격형 에이전트와 방어형 에이전트의 이중 구조 설계

## 1. 아키텍처 개요

```
                    ┌─────────────────────────────────────────────┐
                    │              Decepticon Platform            │
                    │                                             │
                    │  ┌───────────────┐   ┌───────────────────┐ │
                    │  │   RedGate      │   │  Knowledge Graph  │ │
                    │  │ (Control Plane)│   │  (Neo4j / JSON)   │ │
                    │  └───────┬───────┘   └────────┬──────────┘ │
                    │          │                     │            │
                    │    ┌─────┴─────────────────────┴─────┐     │
                    │    │        Feedback Pipeline         │     │
                    │    │  Finding → Analysis → Action     │     │
                    │    └─────┬─────────────────────┬─────┘     │
                    │          │                     │            │
                    │  ┌───────┴───────┐   ┌────────┴──────────┐│
                    │  │  OFFENSIVE    │   │   DEFENSIVE       ││
                    │  │  LANE         │   │   LANE            ││
                    │  │               │   │                   ││
                    │  │ ┌───────────┐ │   │ ┌───────────────┐ ││
                    │  │ │ Recon     │ │   │ │ WAF Agent     │ ││
                    │  │ │ Agent     │ │   │ │ (규칙 업데이트) │ ││
                    │  │ ├───────────┤ │   │ ├───────────────┤ ││
                    │  │ │ Exploit   │ │   │ │ Patch Agent   │ ││
                    │  │ │ Agent     │ │   │ │ (코드 패치)    │ ││
                    │  │ ├───────────┤ │   │ ├───────────────┤ ││
                    │  │ │ PostExp   │ │   │ │ Config Agent  │ ││
                    │  │ │ Agent     │ │   │ │ (설정 강화)    │ ││
                    │  │ ├───────────┤ │   │ ├───────────────┤ ││
                    │  │ │ Cloud     │ │   │ │ Detection     │ ││
                    │  │ │ Hunter    │ │   │ │ Agent (탐지)   │ ││
                    │  │ └───────────┘ │   │ └───────────────┘ ││
                    │  │               │   │                   ││
                    │  │  Docker Kali  │   │  Target Systems   ││
                    │  │  Sandbox      │   │  (Implant/Agent)  ││
                    │  └───────────────┘   └───────────────────┘│
                    └─────────────────────────────────────────────┘
```

## 2. Offensive Lane (공격 레인)

### 2.1 기존 Decepticon 에이전트 (현재 구현)

| Agent | File | Role | Tools |
|-------|------|------|-------|
| **Decepticon** | `agents/decepticon.py` | 오케스트레이터 | OPPLAN CRUD, 서브에이전트 위임 |
| **Recon** | `agents/recon.py` | 정찰 + OSINT | nmap, subfinder, nuclei, whois |
| **Exploit** | `agents/exploit.py` | 초기 접근 | sqlmap, metasploit, burp |
| **PostExploit** | `agents/postexploit.py` | 후속 공격 | mimikatz, impacket, bloodhound |
| **Analyst** | `agents/analyst.py` | 취약점 연구 | 소스 코드 리뷰, CVE 분석 |
| **Reverser** | `agents/reverser.py` | 바이너리 분석 | ghidra, r2, strace |
| **CloudHunter** | `agents/cloud_hunter.py` | 클라우드 공격 | pacu, scout suite |
| **ADOperator** | `agents/ad_operator.py` | AD 익스플로잇 | bloodhound, rubeus, certipy |
| **Soundwave** | `agents/soundwave.py` | 문서 생성 | RoE, CONOPS 작성 |

### 2.2 공격 레인 데이터 흐름

```
OPPLAN (계획)
    │
    ├── OBJ-001: External recon ──→ Recon Agent
    │   └── Output: subdomains, ports, services, tech stack
    │
    ├── OBJ-002: Vuln scanning ──→ Recon Agent + Analyst
    │   └── Output: CVE list, misconfigs, exposed services
    │
    ├── OBJ-003: Initial access ──→ Exploit Agent
    │   └── Output: shell/creds, PoC, evidence
    │
    ├── OBJ-004: Privilege escalation ──→ PostExploit Agent
    │   └── Output: elevated access, kernel exploits
    │
    ├── OBJ-005: Lateral movement ──→ PostExploit Agent
    │   └── Output: additional hosts, pivot paths
    │
    └── Each objective produces:
        Finding {
          id, severity, target, evidence,
          root_cause, remediation_actions[]
        }
```

### 2.3 공격 레인 → Feedback 변환

```python
class OffensiveLaneFeedbackExtractor:
    """공격 결과에서 방어 피드백을 자동 추출."""
    
    def extract_findings(self, objective_result: ObjectiveResult) -> list[Finding]:
        findings = []
        
        # 1. 도구 출력에서 취약점 파싱
        for tool_output in objective_result.tool_outputs:
            if tool_output.tool == "nuclei":
                findings.extend(self._parse_nuclei(tool_output))
            elif tool_output.tool == "nmap":
                findings.extend(self._parse_nmap(tool_output))
            elif tool_output.tool == "sqlmap":
                findings.extend(self._parse_sqlmap(tool_output))
        
        # 2. 에이전트 판단에서 추가 findings 추출
        for judgment in objective_result.agent_judgments:
            if judgment.type == "vulnerability_confirmed":
                findings.append(self._judgment_to_finding(judgment))
        
        # 3. 각 Finding에 remediation 액션 자동 생성
        for finding in findings:
            finding.remediation_actions = self._generate_remediations(finding)
        
        return findings
    
    def _generate_remediations(self, finding: Finding) -> list[RemediationAction]:
        """Finding 유형에 따라 방어 액션 자동 생성."""
        actions = []
        
        match finding.cwe_id:
            case "CWE-89":  # SQL Injection
                actions.append(RemediationAction(
                    type=RemediationType.WAF_RULE,
                    target_system="WAF",
                    waf_rule=self._generate_sqli_waf_rule(finding),
                    automatable=True,
                    requires_approval=False,
                ))
                actions.append(RemediationAction(
                    type=RemediationType.CODE_PATCH,
                    target_system="application",
                    description="Parameterize SQL query",
                    automatable=True,
                    requires_approval=True,  # 코드 변경은 승인 필요
                ))
            
            case "CWE-79":  # XSS
                actions.append(RemediationAction(
                    type=RemediationType.WAF_RULE,
                    target_system="WAF",
                    waf_rule=self._generate_xss_waf_rule(finding),
                    automatable=True,
                    requires_approval=False,
                ))
                actions.append(RemediationAction(
                    type=RemediationType.CONFIG,
                    target_system="nginx",
                    config_change={"add_header": "Content-Security-Policy: default-src 'self'"},
                    automatable=True,
                    requires_approval=False,
                ))
            
            case "CWE-200":  # Information Exposure
                actions.append(RemediationAction(
                    type=RemediationType.CONFIG,
                    target_system="nginx",
                    config_change={"server_tokens": "off"},
                    automatable=True,
                    requires_approval=False,
                ))
        
        return actions
```

## 3. Defensive Lane (방어 레인)

### 3.1 방어형 에이전트 정의

| Agent | 역할 | Target System | 자동화 수준 |
|-------|------|---------------|------------|
| **WAF Agent** | WAF 규칙 업데이트 | ModSecurity, Cloudflare, AWS WAF | 높음 (자동) |
| **Patch Agent** | 코드 패치 생성/적용 | Application code (Git) | 중간 (PR 생성) |
| **Config Agent** | 서버/서비스 설정 강화 | nginx, Apache, SSH, DB | 높음 (자동) |
| **Detection Agent** | 탐지 규칙 생성 | Sigma, YARA, Splunk, ElasticSIEM | 높음 (자동) |
| **Network Agent** | 네트워크 정책 변경 | iptables, Security Groups, NSG | 중간 (승인 후) |
| **Monitor Agent** | 모니터링 강화 | Prometheus, Grafana, CloudWatch | 높음 (자동) |

### 3.2 방어형 에이전트 구현 설계

```python
class DefensiveAgent(ABC):
    """방어형 에이전트 기본 클래스."""
    
    agent_type: str
    target_system: str
    
    @abstractmethod
    async def apply_remediation(
        self, action: RemediationAction, context: DefenseContext
    ) -> RemediationResult:
        """방어 액션 적용."""
        ...
    
    @abstractmethod
    async def verify_remediation(
        self, action: RemediationAction, result: RemediationResult
    ) -> bool:
        """적용된 방어가 유효한지 검증."""
        ...
    
    @abstractmethod
    async def rollback(
        self, action: RemediationAction, result: RemediationResult
    ) -> None:
        """방어 액션 롤백 (실패 또는 서비스 중단 시)."""
        ...

class WAFAgent(DefensiveAgent):
    """WAF 규칙 관리 에이전트."""
    
    agent_type = "waf"
    target_system = "modsecurity"  # or "cloudflare", "aws_waf"
    
    async def apply_remediation(self, action, context):
        match self.target_system:
            case "modsecurity":
                # ModSecurity CRS 규칙 추가
                rule_file = f"/etc/modsecurity/rules/decepticon-{action.finding_id}.conf"
                await self.write_rule(rule_file, action.waf_rule)
                await self.reload_modsecurity()
                
            case "cloudflare":
                # Cloudflare API로 규칙 추가
                await self.cloudflare_api.create_rule(
                    zone_id=context.zone_id,
                    expression=action.waf_rule,
                    action="block",
                    description=f"Decepticon: {action.finding_id}"
                )
        
        return RemediationResult(success=True, applied_at=datetime.now())
    
    async def verify_remediation(self, action, result):
        # 같은 공격 페이로드로 테스트
        response = await self.test_payload(action.original_payload)
        return response.status_code == 403  # WAF가 차단하면 성공

class PatchAgent(DefensiveAgent):
    """코드 패치 생성/적용 에이전트."""
    
    agent_type = "patch"
    target_system = "application"
    
    async def apply_remediation(self, action, context):
        # 1. 패치 브랜치 생성
        branch = f"decepticon/fix-{action.finding_id}"
        await self.git.create_branch(branch)
        
        # 2. 코드 수정 (LLM 에이전트 활용)
        patch = await self.generate_patch(
            finding=action.finding,
            root_cause=action.root_cause,
            codebase=context.repo_path,
        )
        
        # 3. 패치 적용 + 테스트
        await self.git.apply_patch(patch)
        test_result = await self.run_tests()
        
        # 4. PR 생성 (인간 승인 대기)
        if test_result.passed:
            pr = await self.github.create_pr(
                title=f"[Decepticon] Fix {action.finding_id}: {action.title}",
                body=self.format_pr_body(action, patch, test_result),
                branch=branch,
                labels=["security", "decepticon-auto"],
            )
            return RemediationResult(success=True, pr_url=pr.url)
        
        return RemediationResult(success=False, reason="Tests failed")

class ConfigAgent(DefensiveAgent):
    """서버 설정 강화 에이전트."""
    
    agent_type = "config"
    target_system = "infrastructure"
    
    async def apply_remediation(self, action, context):
        # Ansible playbook 생성 + 실행
        playbook = self.generate_playbook(action.config_change)
        result = await self.ansible.run(playbook, target=action.target)
        return RemediationResult(success=result.rc == 0)

class DetectionAgent(DefensiveAgent):
    """탐지 규칙 생성 에이전트."""
    
    agent_type = "detection"
    target_system = "siem"
    
    async def apply_remediation(self, action, context):
        # Sigma 규칙 생성
        sigma_rule = self.generate_sigma_rule(action.finding)
        
        # SIEM에 배포
        match context.siem_type:
            case "splunk":
                await self.splunk.create_search(sigma_to_spl(sigma_rule))
            case "elastic":
                await self.elastic.create_rule(sigma_to_eql(sigma_rule))
        
        return RemediationResult(success=True, rule_id=sigma_rule.id)
```

### 3.3 방어형 에이전트 배포 모델 (Implant)

```
방어형 에이전트 배포 방식:

1. Agent-based (에이전트 기반)
   ├── 대상 시스템에 경량 에이전트 설치
   ├── RedGate와 통신 (WS 또는 HTTP)
   ├── 로컬에서 방어 액션 실행
   └── 예: WAF Agent가 ModSecurity 호스트에 설치

2. API-based (API 기반)
   ├── 외부 API로 방어 액션 실행
   ├── 에이전트 설치 불필요
   ├── Cloudflare, AWS, GitHub API 활용
   └── 예: Config Agent가 AWS Security Group API 호출

3. Git-based (코드 기반)
   ├── 코드 패치 → PR → CI → 배포
   ├── 기존 CI/CD 파이프라인 활용
   ├── 인간 리뷰 게이트 (PR approval)
   └── 예: Patch Agent가 GitHub PR 생성

4. Hybrid (혼합)
   ├── 즉시 적용: WAF 규칙 (API)
   ├── 검토 후 적용: 코드 패치 (Git PR)
   ├── 자동 적용: 탐지 규칙 (SIEM API)
   └── 승인 후 적용: 네트워크 정책 (API + 승인)
```

## 4. Feedback Pipeline (피드백 파이프라인)

### 4.1 파이프라인 구조

```
Finding (공격 레인 출력)
    │
    ▼
┌──────────────────────────────────┐
│  Stage 1: Triage (분류)          │
│  ├── 중복 제거 (KG 대조)         │
│  ├── 심각도 분류 (CVSS 계산)      │
│  └── 긴급도 판단 (즉시/예약)      │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Stage 2: Analysis (분석)        │
│  ├── 근본 원인 식별               │
│  ├── 영향 범위 분석               │
│  ├── 공격 체인 매핑               │
│  └── 관련 Finding 연결 (KG)       │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Stage 3: Planning (계획)        │
│  ├── RemediationAction 생성       │
│  ├── 자동화 가능 여부 판단         │
│  ├── 서비스 중단 위험 평가         │
│  └── 승인 요구 사항 결정           │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Stage 4: Approval (승인)        │
│  ├── LOW/MEDIUM: 자동 승인        │
│  ├── HIGH: Discord 알림 + 대기     │
│  ├── CRITICAL: Discord 즉시 알림  │
│  └── 서비스 중단 위험: 수동 승인   │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Stage 5: Execution (실행)       │
│  ├── 방어형 에이전트에 액션 할당   │
│  ├── 액션 실행 (WAF/패치/설정)    │
│  ├── 실행 결과 기록               │
│  └── 실패 시 롤백                 │
└──────────────┬───────────────────┘
               │
               ▼
┌──────────────────────────────────┐
│  Stage 6: Verification (검증)    │
│  ├── 공격형 에이전트로 재공격      │
│  ├── 같은 취약점 차단 확인         │
│  ├── 부작용 확인 (서비스 정상?)    │
│  └── Finding 상태 → "immune"      │
└──────────────────────────────────┘
```

### 4.2 승인 정책 매트릭스

| Finding Severity | 서비스 중단 위험 | 승인 방식 | 대기 시간 |
|-----------------|----------------|----------|----------|
| CRITICAL | None | 자동 | 즉시 |
| CRITICAL | Low | 자동 + 알림 | 즉시 |
| CRITICAL | Medium/High | **인간 승인** | Discord 알림 후 대기 |
| HIGH | None | 자동 | 즉시 |
| HIGH | Low | 자동 + 알림 | 5분 대기 |
| HIGH | Medium/High | **인간 승인** | Discord 알림 후 대기 |
| MEDIUM | None/Low | 자동 | 다음 사이클 |
| MEDIUM | Medium/High | **인간 승인** | 다음 사이클 |
| LOW | Any | 자동 | 배치 처리 |

### 4.3 Defense OPPLAN

공격 OPPLAN에서 자동 생성되는 방어 OPPLAN:

```json
{
  "engagement_name": "acme-corp-defense",
  "source_engagement": "acme-corp-attack",
  "objectives": [
    {
      "id": "DEF-001",
      "title": "Block SQLi on /api/users",
      "source_finding": "FIND-001",
      "type": "waf_rule",
      "target_system": "modsecurity",
      "action": {
        "rule": "SecRule ARGS:id \"@rx ['\\\";]\" \"id:1001,deny,status:403\"",
        "automatable": true
      },
      "status": "pending",
      "priority": 1,
      "approval": "auto"
    },
    {
      "id": "DEF-002",
      "title": "Patch parameterized query for users API",
      "source_finding": "FIND-001",
      "type": "code_patch",
      "target_system": "application",
      "action": {
        "file": "src/api/users.py",
        "description": "Replace raw SQL with parameterized query",
        "automatable": true
      },
      "status": "pending",
      "priority": 2,
      "approval": "human_required"
    }
  ]
}
```

## 5. Integration Points (통합 지점)

### 5.1 공격 → 방어 데이터 흐름

```python
# Decepticon 코어에서의 통합
class AttackDefenseOrchestrator:
    """공격-방어 루프 오케스트레이터."""
    
    def __init__(self):
        self.offensive = OffensiveLane()    # 기존 Decepticon
        self.feedback = FeedbackPipeline()  # 신규
        self.defensive = DefensiveLane()    # 신규
        self.kg = KnowledgeGraph()          # 기존 Neo4j
    
    async def run_cycle(self, attack_opplan: OPPLAN) -> CycleResult:
        # 1. 공격 실행
        attack_results = await self.offensive.execute(attack_opplan)
        
        # 2. Finding 추출
        findings = self.feedback.extract_findings(attack_results)
        
        # 3. KG 업데이트
        await self.kg.store_findings(findings)
        
        # 4. 방어 OPPLAN 생성
        defense_opplan = self.feedback.generate_defense_opplan(findings)
        
        # 5. 방어 실행
        defense_results = await self.defensive.execute(defense_opplan)
        
        # 6. 검증 (재공격)
        verification = await self.offensive.verify(findings, defense_results)
        
        # 7. 면역 상태 업데이트
        await self.kg.update_immunity(findings, verification)
        
        return CycleResult(
            findings=findings,
            remediated=defense_results,
            verified=verification,
            immune_count=sum(1 for v in verification if v.immune),
        )
```

### 5.2 Knowledge Graph 통합

```
KG Node Types:
  ├── Target (호스트, 서비스, 엔드포인트)
  ├── Vulnerability (발견된 취약점)
  ├── Attack (수행된 공격)
  ├── Finding (공격 결과)
  ├── Remediation (적용된 방어)
  ├── Verification (검증 결과)
  └── Immunity (면역 상태)

KG Edge Types:
  ├── FOUND_ON (Finding → Target)
  ├── EXPLOITED_BY (Vulnerability → Attack)
  ├── REMEDIATED_BY (Finding → Remediation)
  ├── VERIFIED_BY (Remediation → Verification)
  ├── IMMUNE_TO (Target → Vulnerability)
  └── DEPENDS_ON (Finding → Finding)

KG Query Examples:
  "면역되지 않은 취약점은?"
  MATCH (t:Target)-[:FOUND_ON]-(f:Finding)
  WHERE NOT EXISTS((t)-[:IMMUNE_TO]-(:Vulnerability {id: f.vuln_id}))
  RETURN f

  "가장 효과적인 방어 유형은?"
  MATCH (r:Remediation)-[:VERIFIED_BY]-(v:Verification {immune: true})
  RETURN r.type, count(*) ORDER BY count(*) DESC
```

## 6. Dual OPPLAN System

### 6.1 Attack OPPLAN (기존)

```
Phase: RECON → INITIAL_ACCESS → POST_EXPLOIT → C2 → EXFILTRATION
Status: pending → in-progress → completed → blocked
Owner: recon/exploit/postexploit agents
Output: Findings
```

### 6.2 Defense OPPLAN (신규)

```
Phase: TRIAGE → ANALYZE → PLAN → APPLY → VERIFY
Status: pending → approved → applying → applied → verified → immune
Owner: waf/patch/config/detection/network agents
Input: Findings from Attack OPPLAN
Output: Immune status
```

### 6.3 PlanAdapter 확장

```python
class AttackDefensePlanAdapter(PlanAdapter):
    """공격-방어 통합 PlanAdapter.
    
    공격 OPPLAN과 방어 OPPLAN을 하나의 루프에서 관리.
    """
    
    def load(self, source: str) -> list[PlanItem]:
        attack_items = OPPLANAdapter().load(f"{source}/attack-opplan.json")
        defense_items = DefenseOPPLANAdapter().load(f"{source}/defense-opplan.json")
        
        # 방어 아이템은 공격 완료 후 시작
        for d_item in defense_items:
            d_item.dependencies.append(d_item.metadata["source_finding"])
        
        return attack_items + defense_items
    
    def pick_next(self, items):
        # 1. 미완료 공격 목표가 있으면 공격 우선
        attack_items = [i for i in items if i.metadata.get("lane") == "attack"]
        next_attack = OPPLANAdapter().pick_next(attack_items)
        if next_attack:
            return next_attack
        
        # 2. 공격 완료 → 방어 목표 선택
        defense_items = [i for i in items if i.metadata.get("lane") == "defense"]
        return DefenseOPPLANAdapter().pick_next(defense_items)
    
    def is_done(self, items):
        # 모든 공격 완료 AND 모든 방어 검증됨
        attack_done = all(
            i.status in (ItemStatus.COMPLETED, ItemStatus.BLOCKED)
            for i in items if i.metadata.get("lane") == "attack"
        )
        defense_done = all(
            i.status == ItemStatus.COMPLETED  # "immune"
            for i in items if i.metadata.get("lane") == "defense"
        )
        return attack_done and defense_done
```

## 7. 실행 환경

### 7.1 공격 환경 (기존)

```
Docker Kali Sandbox
  ├── 격리 네트워크 (sandbox-net)
  ├── 대상만 접근 가능
  ├── tmux 세션 관리
  └── PS1 polling (명령 완료 감지)
```

### 7.2 방어 환경 (신규)

```
방어형 에이전트 실행 환경:

Option A: Same sandbox (같은 샌드박스)
  ├── 공격과 같은 Docker에서 방어 액션 생성
  ├── API 호출로 외부 시스템에 적용
  └── 장점: 간단, 단점: 격리 부족

Option B: Separate sandbox (별도 샌드박스)
  ├── 방어 전용 Docker 컨테이너
  ├── 대상 시스템 네트워크 접근
  ├── Ansible/Terraform 도구 포함
  └── 장점: 격리, 단점: 복잡

Option C: Direct API (API 직접 호출)
  ├── RedGate에서 직접 API 호출
  ├── Cloudflare, AWS, GitHub API
  ├── 샌드박스 불필요
  └── 장점: 빠름, 단점: API 의존

추천: Option C (API) + Option B (필요시)
  ├── WAF/Cloud: API 직접 호출 (C)
  ├── 서버 설정: Ansible 샌드박스 (B)
  └── 코드 패치: Git API (C)
```

## 8. 보안 고려사항

### 8.1 방어형 에이전트의 권한

```
위험: 방어형 에이전트가 시스템을 변경할 수 있는 권한을 가짐
  → 공격자가 이 에이전트를 탈취하면 시스템을 파괴할 수 있음

완화:
  1. 최소 권한 원칙 (각 에이전트는 자기 역할만)
  2. 승인 게이트 (HIGH/CRITICAL은 인간 승인)
  3. 롤백 보장 (모든 변경은 되돌릴 수 있음)
  4. 감사 로그 (모든 변경 기록)
  5. 변경 범위 제한 (Decepticon 생성 규칙만 관리)
  6. API 키 분리 (공격/방어 별도 크리덴셜)
```

### 8.2 Finding 신뢰도

```
위험: 오탐(false positive)에 기반한 방어가 서비스 중단 유발

완화:
  1. Finding 검증 (PoC 성공 시에만 remediation)
  2. 단계적 적용 (WAF → 모니터링 → 차단 순서)
  3. 카나리아 테스트 (적용 후 서비스 정상 여부 확인)
  4. 자동 롤백 (서비스 중단 감지 시)
  5. 오탐 피드백 루프 (잘못된 방어 → 학습)
```
