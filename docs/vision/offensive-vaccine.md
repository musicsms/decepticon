# Decepticon Vision: The Offensive Vaccine

> "공격은 최선의 방어가 아니다. 공격의 결과를 방어에 피드백하는 것이 최선의 방어이다."

## 1. Core Philosophy: Offensive Vaccine (공격형 백신)

### 1.1 백신의 원리

생물학적 백신은 **약화된 병원체**를 주입하여 면역 시스템이 항체를 생성하게 만든다. 진짜 병원체가 침입했을 때, 이미 훈련된 면역 시스템이 즉각 대응한다.

Decepticon의 공격형 에이전트는 **디지털 백신**이다:

```
생물학적 백신                    Decepticon (디지털 백신)
─────────────────────────────────────────────────────────
약화된 병원체 주입               공격형 에이전트의 모의 공격
  ↓                               ↓
면역 시스템 반응                 취약점 발견 (findings)
  ↓                               ↓
항체 생성                        방어 규칙/패치 생성
  ↓                               ↓
면역 기억                        방어 시스템 학습
  ↓                               ↓
실제 병원체 방어                 실제 공격 방어
```

### 1.2 핵심 통찰

**공격형 에이전트의 진짜 가치는 공격 자체가 아니라, 공격에서 얻은 피드백이다.**

공격은 수단이고, 방어 강화가 목적이다.

```
                     Offensive Vaccine Model
                     
     ┌─────────────────────────────────────────────┐
     │                                             │
     │   Offensive Agent (공격형 에이전트)          │
     │   = 백신의 "약화된 병원체"                   │
     │                                             │
     │   ┌─────────────────────────────────┐       │
     │   │ 정찰 → 취약점 발견 → PoC 작성  │       │
     │   └──────────────┬──────────────────┘       │
     │                  │                           │
     │                  │ Findings (항원)            │
     │                  ↓                           │
     │   ┌─────────────────────────────────┐       │
     │   │         Feedback Pipeline       │       │
     │   │  (항원 → 항체 변환 과정)         │       │
     │   │                                 │       │
     │   │  Finding → Impact Analysis      │       │
     │   │  → Remediation Plan             │       │
     │   │  → Defensive Action             │       │
     │   └──────────────┬──────────────────┘       │
     │                  │                           │
     │                  │ Defensive Actions (항체)   │
     │                  ↓                           │
     │   ┌─────────────────────────────────┐       │
     │   │ Defensive Agent (방어형 에이전트) │       │
     │   │ = 면역 시스템                    │       │
     │   │                                 │       │
     │   │ WAF 룰 업데이트                 │       │
     │   │ 패치 적용                       │       │
     │   │ 설정 변경                       │       │
     │   │ 탐지 규칙 추가                  │       │
     │   │ 네트워크 정책 강화              │       │
     │   └──────────────┬──────────────────┘       │
     │                  │                           │
     │                  │ Hardened System            │
     │                  ↓                           │
     │   ┌─────────────────────────────────┐       │
     │   │      Re-Attack (재공격)         │       │
     │   │  = 백신 효과 검증               │       │
     │   │                                 │       │
     │   │  같은 취약점 재시도 → 차단됨?   │       │
     │   │  → YES: 면역 확인 ✅            │       │
     │   │  → NO: 재조정 필요 🔄           │       │
     │   └─────────────────────────────────┘       │
     │                                             │
     └─────────────────────────────────────────────┘
```

### 1.3 왜 "Vaccine"인가?

| 특성 | 전통적 레드팀 | Decepticon (Offensive Vaccine) |
|------|-------------|-------------------------------|
| **목적** | 취약점 찾기 | 취약점 찾기 **+ 자동 수정** |
| **결과물** | 보고서 (PDF) | **실행 가능한 방어 액션** |
| **주기** | 연 1-2회 | **24/7 지속** |
| **피드백** | 인간이 읽고 수동 패치 | **에이전트가 읽고 자동 패치** |
| **검증** | 다음 해 레드팀에서 확인 | **즉시 재공격으로 검증** |
| **학습** | 보고서 아카이브 | **Knowledge Graph에 누적** |
| **확장** | 인력 한계 | **에이전트 무한 확장** |

## 2. OpenClaw 철학과의 연결

### 2.1 "Actually Does Things"

OpenClaw의 핵심 철학:

> "OpenClaw is the AI that **actually does things**. It runs on your devices, in your channels, with your rules."
> — OpenClaw VISION.md

Decepticon도 같은 철학을 공유한다:

> "Decepticon is the AI that **actually hacks**. It runs in your sandbox, on your targets, within your RoE."

### 2.2 철학적 대응

| OpenClaw | Decepticon |
|----------|-----------|
| "Actually does things" | "Actually hacks" |
| 개인 AI 어시스턴트 | 보안 AI 에이전트 |
| 실제 메시지 전송 | 실제 공격 수행 |
| 채널에서 대화 | 네트워크에서 공격 |
| 도구로 작업 수행 | 도구로 취약점 발견 |
| 결과를 채널로 전달 | 결과를 방어 시스템에 피드백 |

### 2.3 "Real" Agent의 의미

**개발 에이전트 (OpenClaw/OMC)**:
- "real"의 의미: 실제 코드를 작성하고, 테스트를 실행하고, PR을 생성한다
- 인간이 잠자는 동안 실제 기능이 구현된다

**공격형 에이전트 (Decepticon)**:
- "real"의 의미: 실제 스캔을 수행하고, 실제 익스플로잇을 시도하고, 실제 증거를 수집한다
- 인간이 잠자는 동안 실제 취약점이 발견된다

**방어형 에이전트 (Decepticon 비전)**:
- "real"의 의미: 실제 패치를 적용하고, 실제 룰셋을 변경하고, 실제 설정을 강화한다
- 인간이 잠자는 동안 실제 방어가 강화된다

이 세 가지가 합쳐지면:
> **인간이 잠자는 동안 시스템이 스스로 공격하고, 스스로 방어하고, 스스로 강해진다.**

## 3. Attack → Defense Feedback Pipeline

### 3.1 Finding의 생명주기

```
Phase 1: Discovery (발견)
  공격형 에이전트가 취약점 발견
  ├── 정찰 에이전트: 서브도메인, 열린 포트, 서비스 버전
  ├── 익스플로잇 에이전트: SQLi, XSS, IDOR, RCE
  ├── 후속 공격 에이전트: 횡방향 이동, 권한 상승
  └── Output: Finding 객체 (KG에 저장)

Phase 2: Analysis (분석)
  Finding을 분석하여 방어 액션으로 변환
  ├── CVSS 점수 계산
  ├── 영향 범위 분석
  ├── 근본 원인 식별
  └── Output: Remediation Plan (수정 계획)

Phase 3: Remediation (수정)
  방어형 에이전트가 수정 계획을 실행
  ├── WAF 규칙 업데이트
  ├── 코드 패치 적용
  ├── 설정 변경
  ├── 탐지 규칙 추가
  └── Output: Applied Actions (적용된 액션)

Phase 4: Verification (검증)
  공격형 에이전트가 같은 취약점을 재시도
  ├── 재공격 시도 → 차단됨: ✅ 면역 확인
  ├── 재공격 성공 → 방어 실패: 🔄 재조정
  └── Output: Verification Result

Phase 5: Learning (학습)
  Knowledge Graph에 전체 사이클 기록
  ├── 어떤 공격이 효과적이었는지
  ├── 어떤 방어가 성공했는지
  ├── 어떤 패턴이 반복되는지
  └── Output: Knowledge 누적
```

### 3.2 Finding 객체 구조

```python
@dataclass
class Finding:
    """공격형 에이전트가 발견한 취약점."""
    
    # Identity
    id: str                         # FIND-001
    title: str                      # "SQL Injection on /api/users"
    
    # Classification
    severity: Severity              # CRITICAL, HIGH, MEDIUM, LOW, INFO
    cvss_score: float               # 7.5
    cwe_id: str                     # CWE-89
    mitre_id: str                   # T1190
    owasp_category: str             # A03:2021 Injection
    
    # Technical Details
    target: str                     # api.example.com
    endpoint: str                   # /api/users?id=
    parameter: str                  # id
    attack_type: str                # time-based blind SQLi
    evidence: Evidence              # PoC, screenshots, logs
    
    # Remediation (공격 → 방어 변환)
    root_cause: str                 # "Unsanitized user input in SQL query"
    remediation_type: RemediationType  # PATCH, CONFIG, RULE, POLICY
    remediation_actions: list[RemediationAction]
    
    # Lifecycle
    status: FindingStatus           # discovered, analyzing, remediating, verified, immune
    discovered_at: datetime
    remediated_at: datetime | None
    verified_at: datetime | None
    
    # Attack-Defense Link
    attack_objective_id: str        # OBJ-003 (OPPLAN에서)
    defense_task_id: str | None     # DEF-001 (방어 OPPLAN에서)

class RemediationAction:
    """Finding에서 도출된 구체적 방어 액션."""
    
    type: RemediationType
    description: str
    target_system: str              # "WAF", "nginx", "application", "firewall"
    
    # 구체적 액션
    waf_rule: str | None            # "SecRule ARGS:id \"@rx ['\"]\" ..."
    patch_diff: str | None          # 코드 패치 diff
    config_change: dict | None      # 설정 변경사항
    detection_rule: str | None      # Sigma/YARA 규칙
    
    # 자동화 가능 여부
    automatable: bool               # 방어 에이전트가 자동 적용 가능?
    requires_approval: bool         # 인간 승인 필요?
    risk_of_disruption: str         # "none", "low", "medium", "high"
```

### 3.3 구체적 Finding → Defense 변환 예시

**예시 1: SQL Injection**
```
공격형 에이전트 발견:
  Finding: SQLi on /api/users?id=1' OR '1'='1
  Evidence: 847개 사용자 레코드 노출
  Root cause: PreparedStatement 미사용

방어형 에이전트 액션:
  1. [즉시] WAF 규칙 추가:
     SecRule ARGS:id "@rx ['\";]|--|\bOR\b|\bAND\b|\bUNION\b" \
       "id:1001,deny,status:403,msg:'SQLi blocked'"
  
  2. [코드] 패치 생성:
     - users_controller.py: raw SQL → parameterized query
     - git commit + PR 생성
  
  3. [탐지] Sigma 규칙:
     title: SQL Injection Attempt on Users API
     logsource: product: nginx
     detection:
       selection: request_uri|contains:
         - "' OR "
         - "1=1"
         - "UNION SELECT"
     level: high

공격형 에이전트 재검증:
  같은 공격 재시도 → WAF에 의해 차단 (403)
  → Finding status: "immune" ✅
```

**예시 2: Open Port (불필요한 서비스)**
```
공격형 에이전트 발견:
  Finding: Port 8080 open (Node.js dev server)
  Evidence: staging.example.com:8080 응답
  Root cause: 개발 서버가 프로덕션에 노출

방어형 에이전트 액션:
  1. [즉시] 방화벽 규칙:
     iptables -A INPUT -p tcp --dport 8080 -j DROP
  
  2. [설정] nginx 변경:
     8080 포트 upstream 제거
  
  3. [모니터링] 포트 스캔 알림:
     새로운 포트 열림 감지 시 자동 알림

공격형 에이전트 재검증:
  Port 8080 스캔 → closed/filtered
  → Finding status: "immune" ✅
```

**예시 3: 취약한 의존성**
```
공격형 에이전트 발견:
  Finding: nginx/1.25.3 → CVE-2026-1234 (RCE)
  Evidence: 버전 핑거프린트 + PoC 성공
  Root cause: 패치 미적용

방어형 에이전트 액션:
  1. [패치] 패키지 업데이트:
     apt-get update && apt-get upgrade nginx
  
  2. [설정] 임시 완화:
     nginx 설정에서 취약 모듈 비활성화
  
  3. [모니터링] CVE 모니터:
     해당 기술 스택 CVE 알림 구독

공격형 에이전트 재검증:
  같은 CVE 익스플로잇 시도 → 실패 (패치됨)
  → Finding status: "immune" ✅
```

## 4. Ralph Loop in Attack-Defense Cycle

### 4.1 기존 Ralph Loop (개발)

```
PRD → Pick Story → Implement → Test → Mark → Repeat
```

### 4.2 Decepticon Ralph Loop (공격)

```
OPPLAN → Pick Objective → Attack → Verify → Mark → Repeat
```

### 4.3 Offensive Vaccine Ralph Loop (공격 + 방어)

```
┌─────────────────────────────────────────────────────┐
│              CONTINUOUS HARDENING LOOP               │
│                                                     │
│  ┌───────────┐     ┌───────────┐     ┌───────────┐ │
│  │  Attack   │     │ Feedback  │     │  Defense  │ │
│  │  OPPLAN   │────>│ Pipeline  │────>│  OPPLAN   │ │
│  │           │     │           │     │           │ │
│  │ OBJ-001  │     │ FIND-001  │     │ DEF-001  │ │
│  │ OBJ-002  │     │ FIND-002  │     │ DEF-002  │ │
│  │ OBJ-003  │     │ FIND-003  │     │ DEF-003  │ │
│  └─────┬─────┘     └───────────┘     └─────┬─────┘ │
│        │                                    │       │
│        │         Ralph Loop                 │       │
│        │                                    │       │
│        │    ┌───────────────────┐           │       │
│        └───>│   Re-Attack       │<──────────┘       │
│             │   (Verification)  │                   │
│             │                   │                   │
│             │ Same vuln blocked?│                   │
│             │ → YES: immune ✅  │                   │
│             │ → NO: loop back 🔄│                   │
│             └───────────────────┘                   │
│                                                     │
│  Convergence: 시간이 지날수록 "immune" 비율 증가     │
│  = 시스템이 점점 강해짐                              │
└─────────────────────────────────────────────────────┘
```

### 4.4 수렴 조건 (Convergence)

```
Iteration 1:  Attack 10 vectors → 8 vuln found → 8 patches → 6 verified
Iteration 2:  Attack 10 vectors → 3 vuln found → 3 patches → 3 verified
Iteration 3:  Attack 10 vectors → 1 vuln found → 1 patch  → 1 verified
Iteration 4:  Attack 10 vectors → 0 vuln found → CONVERGED ✅

수렴 그래프:
  Vulns │
  Found │ ██████████  (Iter 1: 8)
        │ ████        (Iter 2: 3)
        │ █           (Iter 3: 1)
        │             (Iter 4: 0) ← IMMUNE
        └──────────────────────
          1    2    3    4   Iterations

각 반복은:
  - 새로운 공격 벡터를 시도 (기존 + 신규)
  - 이전에 패치된 취약점은 더 이상 발견되지 않음
  - 발견 수가 0에 수렴하면 해당 스코프는 "면역" 상태
```

## 5. "Real" Agent 요건

### 5.1 공격형 에이전트가 "Real"이려면

Decepticon의 공격형 에이전트가 진짜 레드팀 테스트를 수행하려면:

| 요건 | 현재 상태 | 목표 |
|------|----------|------|
| **실제 네트워크 스캔** | ✅ nmap in Kali sandbox | 유지 |
| **실제 취약점 스캔** | ✅ nuclei, nikto 사용 가능 | 스킬 확장 |
| **실제 익스플로잇** | ✅ Metasploit, sqlmap | 자동화 강화 |
| **실제 후속 공격** | ✅ postexploit 에이전트 | C2 통합 |
| **실제 증거 수집** | ✅ evidence 저장 | KG 자동 업데이트 |
| **실제 보고서** | ✅ HackerOne/Bugcrowd 형식 | 자동 제출 |
| **자율 실행** | ✅ Ralph loop | 24/7 지속 실행 |
| **방어 피드백** | ❌ 없음 | **VIS 핵심 목표** |

### 5.2 방어형 에이전트가 "Real"이려면

| 요건 | 구현 방법 |
|------|----------|
| **실제 패치 적용** | 코드 수정 → PR 생성 → CI → 자동 배포 |
| **실제 WAF 규칙** | ModSecurity/Cloudflare API로 룰셋 업데이트 |
| **실제 방화벽 변경** | iptables/pf/cloud 보안그룹 API |
| **실제 설정 강화** | Ansible/Terraform으로 인프라 변경 |
| **실제 탐지 규칙** | Sigma → Splunk/ElasticSIEM 자동 배포 |
| **실제 모니터링** | Prometheus/Grafana 알림 규칙 추가 |

### 5.3 인간의 역할

```
인간 관여 지점 (Decepticon Offensive Vaccine):

1. 계획 단계 (Plan):
   ├── RoE (Rules of Engagement) 작성
   ├── OPPLAN 검토 및 승인
   ├── 스코프 정의 (어디를 공격할 것인가)
   └── 위험 수용 결정 (어떤 방어 액션을 자동화할 것인가)

2. 승인 게이트 (Approval Gates):
   ├── HIGH/CRITICAL 방어 액션 → 인간 승인 필요
   ├── 서비스 중단 위험 액션 → 인간 승인 필요
   ├── 네트워크 정책 변경 → 인간 승인 필요
   └── LOW/MEDIUM 방어 액션 → 자동 승인 가능

3. 나머지는 모두 에이전트:
   ├── 공격 실행 → 에이전트
   ├── 취약점 분석 → 에이전트
   ├── 패치 생성 → 에이전트
   ├── 방어 적용 → 에이전트 (LOW/MED) 또는 인간 승인 후 에이전트 (HIGH/CRIT)
   └── 검증 재공격 → 에이전트
```

## 6. Decepticon의 진화 로드맵

### 6.1 현재 → 비전 도달까지

```
Phase 0: 현재 (Current)
  ├── 공격형 에이전트만 존재
  ├── CLI 접근만 가능
  ├── 순차 실행 (Ralph loop)
  └── 결과: 보고서 (파일)

Phase 1: Real Attack (실제 공격)
  ├── 공격형 에이전트 강화 (700+ 스킬)
  ├── Discord 채널 통합 (RedGate)
  ├── 병렬 실행 (AgentPool)
  └── 결과: 구조화된 Findings (KG)

Phase 2: Feedback Pipeline (피드백 파이프라인)
  ├── Finding → RemediationAction 자동 변환
  ├── Impact analysis 자동화
  ├── Root cause 식별 자동화
  └── 결과: 실행 가능한 방어 액션

Phase 3: Defensive Agent (방어형 에이전트)
  ├── 방어형 에이전트 구현
  ├── WAF 규칙 자동 업데이트
  ├── 코드 패치 자동 생성
  ├── 설정 강화 자동 적용
  └── 결과: 자동 수정된 시스템

Phase 4: Continuous Hardening Loop (지속적 강화 루프)
  ├── Attack-Defense Ralph Loop
  ├── 24/7 자율 실행
  ├── 수렴 메트릭 추적
  ├── 면역 상태 Dashboard
  └── 결과: 스스로 강해지는 시스템

Phase 5: Ecosystem (생태계)
  ├── 커뮤니티 공격 모듈
  ├── 커뮤니티 방어 모듈
  ├── 멀티 조직 공유 인텔리전스
  └── 결과: 집단 면역 (Herd Immunity)
```

### 6.2 비유로 보는 진화

```
Phase 0: 의사가 진찰만 함 (진단만)
Phase 1: 의사가 정밀 검사를 수행 (실제 검사)
Phase 2: 검사 결과를 처방전으로 변환 (피드백)
Phase 3: 약을 자동으로 투약 (자동 치료)
Phase 4: 24/7 건강 모니터링 + 자동 치료 (지속적 건강 관리)
Phase 5: 집단 건강 데이터 공유 (역학 조사)
```

## 7. 경쟁 환경 분석 (2026-04-10 기준)

### 7.1 기존 도구와의 차별점

| 도구 | 유형 | 자율성 | 방어 피드백 | 지속 실행 |
|------|------|--------|-----------|----------|
| Metasploit | 수동 익스플로잇 | ❌ | ❌ | ❌ |
| Nuclei | 자동 스캐너 | 부분 | ❌ | ❌ |
| Burp Suite | 수동 + 자동 | 부분 | ❌ | ❌ |
| Cobalt Strike | C2 프레임워크 | ❌ | ❌ | ❌ |
| **Strix** | AI 에이전트 | ✅ | ❌ | 부분 |
| **red-run** | AI 에이전트 | ✅ | ❌ | 부분 |
| **Decepticon** | **Offensive Vaccine** | ✅ | **✅** | **✅** |

### 7.2 핵심 차별화

Decepticon만의 고유한 가치:

1. **Attack-Defense Closed Loop**: 공격 → 방어 → 검증이 하나의 시스템 안에서
2. **Autonomous Convergence**: 시간이 지날수록 자동으로 보안이 강해짐
3. **Plan-Driven Architecture**: PlanAdapter로 어떤 도메인이든 확장 가능
4. **Real Agent Actions**: OpenClaw 철학 — 실제로 공격하고, 실제로 방어함
5. **Knowledge Accumulation**: Neo4j KG에 모든 학습이 누적됨

## 8. 이름의 의미

### 8.1 "Decepticon" 재해석

Transformers의 Decepticon은 **변신(Transformation)**의 상징이다.

Decepticon 프레임워크에서의 변신:
```
취약점 (Vulnerability) → 면역 (Immunity)
공격 (Attack)         → 방어 (Defense)
약점 (Weakness)       → 강점 (Strength)
위협 (Threat)         → 항체 (Antibody)
```

**모든 공격은 방어로 변신한다.** 이것이 Offensive Vaccine이다.

### 8.2 프로젝트 태그라인

> **"Every attack makes us stronger."**
> 
> **"모든 공격이 우리를 더 강하게 만든다."**

## 9. 핵심 원칙 (Design Principles)

### Principle 1: Attack is Feedback
공격은 목적이 아니라 피드백이다. 모든 공격의 결과는 방어를 강화하는 데 사용되어야 한다.

### Principle 2: Real Actions Only
시뮬레이션이 아닌 실제 공격, 실제 패치, 실제 방어. OpenClaw이 실제 메시지를 보내듯, Decepticon은 실제 취약점을 찾고 실제 패치를 적용한다.

### Principle 3: Human Plans, Agent Executes
인간은 계획(RoE, OPPLAN, 스코프)만 작성한다. 실행은 에이전트의 몫이다. 24시간, 365일.

### Principle 4: Convergence over Perfection
한번에 완벽한 보안은 불가능하다. 반복적 수렴을 통해 점진적으로 강해진다. 매 반복마다 하나의 취약점이 면역 상태가 된다.

### Principle 5: Knowledge Compounds
모든 공격, 모든 방어, 모든 실패가 Knowledge Graph에 축적된다. 시스템은 잊지 않는다.

### Principle 6: Defense Must Be Automated
수동 패치는 확장되지 않는다. 방어 에이전트가 자동으로 WAF 규칙, 코드 패치, 설정 변경을 적용해야 한다.

### Principle 7: Verification Closes the Loop
방어가 적용된 후 반드시 재공격으로 검증한다. 검증 없는 패치는 가짜 면역이다.

## 10. 요약

```
Decepticon = Offensive Vaccine Platform

공격형 에이전트 (현재)
  = 약화된 병원체
  = 실제 공격 수행
  = 취약점 발견 (항원)

피드백 파이프라인 (Phase 2)
  = 항원 → 항체 변환
  = Finding → RemediationAction

방어형 에이전트 (Phase 3)
  = 면역 시스템
  = 패치, 룰셋, 설정 자동 적용

지속적 강화 루프 (Phase 4)
  = Ralph Loop (Attack-Defense)
  = 24/7 자율 실행
  = 시간이 지날수록 수렴 → 면역

"Every attack makes us stronger."
```
