# OpenClaw Security Model & OPSEC Patterns for Decepticon

> OpenClaw의 보안 아키텍처에서 Decepticon 레드팀 OPSEC 가드레일에 적용할 패턴 추출

## 1. 보안 설계 원칙

OpenClaw 보안의 핵심 철학:

> "Security in OpenClaw is a deliberate tradeoff: strong defaults without killing capability."
> — VISION.md

| 원칙 | OpenClaw | Decepticon OPSEC 적용 |
|------|----------|----------------------|
| **Secure by default** | DM pairing, allowlist 기본 활성 | RoE 검증 기본 활성 |
| **Explicit opt-in for power** | 위험 기능은 명시적 활성화 | 공격적 도구는 명시적 허용 |
| **Untrusted input** | 인바운드 DM = untrusted | 스캔 결과 = untrusted (인젝션 방지) |
| **Operator-controlled** | 운영자가 정책 결정 | 레드팀 리더가 RoE 결정 |

## 2. DM Pairing Protocol

### 2.1 전체 흐름

**Source**: `src/pairing/`, `docs/gateway/pairing.md`

```
┌──────────┐                    ┌───────────┐
│ New User │                    │  Gateway  │
│ (Discord)│                    │           │
└────┬─────┘                    └─────┬─────┘
     │                                │
     │  DM: "Hello"                   │
     │──────────────────────────────>│
     │                                │
     │                                │ ← dmPolicy="pairing" 확인
     │                                │ ← 사용자가 allowlist에 없음
     │                                │ ← 6자리 페어링 코드 생성
     │                                │ ← 코드 유효기간: 1시간
     │                                │
     │  "Pairing code: A7X9K2"        │
     │<──────────────────────────────│
     │                                │
     │  (사용자 메시지 처리 안함)       │
     │                                │
┌──────────┐                          │
│ Operator │                          │
│ (CLI)    │                          │
└────┬─────┘                          │
     │                                │
     │  $ openclaw pairing approve    │
     │    discord A7X9K2              │
     │──────────────────────────────>│
     │                                │
     │                                │ ← 사용자를 allowlist에 추가
     │                                │ ← 이후 메시지 처리 시작
     │                                │
     │  "Approved"                    │
     │<──────────────────────────────│
```

### 2.2 DM 정책 유형

| Policy | 동작 | 용도 |
|--------|------|------|
| `pairing` (기본) | 미승인 사용자에게 코드 발급, 메시지 미처리 | 보안 우선 |
| `open` | 모든 DM 처리 (allowFrom에 `*` 필요) | 공개 봇 |
| `disabled` | DM 완전 비활성 | 그룹 전용 |

### 2.3 Decepticon 적용

```
레드팀 운영자 인증:
1. Discord 봇 DM으로 첫 접속 시 페어링 코드 발급
2. 리더가 CLI에서 승인: decepticon pairing approve <code>
3. 이후 해당 운영자만 인게이지먼트 지시 가능
4. allowlist에 없는 사용자의 메시지는 무시

추가 보안:
- 역할 기반 접근 (viewer/operator/admin)
- 인게이지먼트별 접근 제한
- 감사 로그 필수
```

## 3. Allowlist System

### 3.1 다중 레벨 Allowlist

**Source**: `extensions/discord/src/monitor/allow-list.ts`

```
Allowlist 계층:

글로벌 → 채널 → 길드 → 역할 → 사용자

channels.discord.allowFrom: ["*"]           # 글로벌 (위험!)
channels.discord.allowFrom: ["USER_ID"]     # 특정 사용자만

channels.discord.guilds.GUILD_ID:
  users: ["USER_ID_1", "USER_ID_2"]         # 길드 내 사용자
  roles: ["ROLE_ID"]                         # 역할 기반

channels.discord.dm:
  policy: "pairing"                          # DM 정책
  groupEnabled: false                        # 그룹 DM 비활성
```

### 3.2 그룹 정책

| Policy | 동작 |
|--------|------|
| `allowlist` (기본) | allowlist에 있는 그룹만 처리 |
| `open` | 모든 그룹 메시지 처리 |
| `disabled` | 그룹 메시지 무시 |

### 3.3 멘션 게이팅

길드 채널에서:
- `requireMention: true` (기본) → @봇 멘션 시에만 반응
- `requireMention: false` → 모든 메시지에 반응
- 멘션 패턴: 안전한 regex로 퍼지 매칭 지원

### 3.4 Decepticon 적용

```python
# Decepticon allowlist 설계
class AllowlistPolicy:
    # 글로벌 레벨
    operators: list[str]           # 승인된 운영자 Discord ID
    
    # 인게이지먼트 레벨
    engagement_access: dict[str, list[str]]  # engagement → operators
    
    # 역할 레벨
    roles: dict[str, set[str]]     # admin/operator/viewer
    
    # 채널 레벨
    channels: dict[str, str]       # channel_id → engagement 매핑
    
    def can_access(self, user_id, engagement, action) -> bool:
        if action == "view" and user_id in self.roles.get("viewer", set()):
            return True
        if action == "operate" and user_id in self.roles.get("operator", set()):
            return user_id in self.engagement_access.get(engagement, [])
        if action == "admin":
            return user_id in self.roles.get("admin", set())
        return False
```

## 4. SSRF Protection

### 4.1 OpenClaw의 SSRF 방어

**Source**: `src/plugin-sdk/ssrf-policy.ts`

```typescript
// SSRF 정책: 플러그인이 외부 URL 접근 시 검증
type SSRFPolicy = {
  allowedSchemes: string[];      // ["https", "http"]
  blockedHosts: string[];        // ["169.254.169.254", "localhost"]
  blockedCIDRs: string[];        // ["10.0.0.0/8", "172.16.0.0/12"]
  allowedHosts?: string[];       // 화이트리스트 모드
};

// 검증 항목:
// 1. URL 스키마 검증 (file://, gopher:// 차단)
// 2. 호스트 resolve → IP 확인
// 3. 내부 네트워크 IP 대역 차단 (cloud metadata 포함)
// 4. DNS rebinding 방지
```

### 4.2 Decepticon 적용

```
Decepticon에서의 SSRF 고려사항:
- 에이전트가 스캔 대상 URL을 처리할 때 SSRF 방지
- sandbox 내부에서 실행되므로 host network 접근 차단이 핵심
- Docker sandbox-net이 이를 담당 (현재 구현)
- 추가: 에이전트가 생성하는 URL도 검증 필요
  (prompt injection으로 내부 네트워크 스캔 시도 방지)
```

## 5. Sandbox Isolation

### 5.1 OpenClaw Sandbox 모델

**Source**: `src/agents/sandbox/`, `Dockerfile.sandbox*`

```
Sandbox 백엔드:

1. Docker (기본)
   ├── 격리된 파일시스템
   ├── 네트워크 제한 가능
   ├── 볼륨 마운트로 workspace 공유
   └── 선택적: Docker socket 전달 (nested sandbox)

2. SSH
   ├── 원격 머신에서 실행
   ├── SSH 키 기반 인증
   └── 파일 전송: SCP/SFTP

3. File Bridge
   ├── 호스트 ↔ sandbox 간 안전한 파일 접근
   ├── mutation-safe (쓰기 검증)
   └── 양방향 동기화
```

**Sandbox 모드**:
```
sandbox: "inherit"   → 부모 sandbox 설정 상속
sandbox: "require"   → 반드시 sandbox 내 실행
sandbox: false       → sandbox 비활성 (위험)
```

### 5.2 Docker Sandbox 상세

**Source**: `Dockerfile.sandbox`, `Dockerfile.sandbox-common`, `Dockerfile.sandbox-browser`

```dockerfile
# Dockerfile.sandbox (기본)
FROM node:24-slim
# 최소 필수 패키지만 설치
# non-root 사용자로 실행
# workspace 볼륨 마운트

# Dockerfile.sandbox-browser (브라우저 포함)
FROM node:24-slim
# + Chromium headless
# + 브라우저 자동화 도구
```

### 5.3 Decepticon과의 비교

```
OpenClaw Sandbox:                 Decepticon Sandbox:
├── Docker (generic)              ├── Docker Kali Linux (공격 특화)
├── Node.js runtime               ├── Python + 보안 도구
├── workspace 볼륨 공유           ├── /workspace 볼륨 공유
├── File Bridge (양방향)          ├── CompositeBackend (읽기/쓰기 분리)
└── SSH remote option             └── tmux 세션 관리

Decepticon 우위:
- Kali Linux = 사전 설치된 보안 도구 (nmap, nuclei, etc.)
- sandbox-net = 완전 격리 네트워크 (대상만 접근 가능)
- tmux 세션 = 장시간 실행 도구 관리
- PS1 polling = 명령 완료 감지
```

## 6. Tool Filesystem Policy

### 6.1 ToolFsPolicy

**Source**: `src/plugins/types.ts` (ToolFsPolicy references)

```typescript
type ToolFsPolicy = {
  // 도구가 접근할 수 있는 파일시스템 경계
  allowedPaths: string[];     // 허용 경로 (workspace, evidence)
  deniedPaths: string[];      // 거부 경로 (system, secrets)
  readOnly?: boolean;         // 읽기 전용 모드
};

// 도구 팩토리에서 사용:
const toolFactory = (ctx: ToolContext) => {
  // ctx.fsPolicy로 파일시스템 경계 강제
  return new BashTool({
    allowedPaths: ctx.fsPolicy?.allowedPaths,
    cwd: ctx.workspaceDir,
  });
};
```

### 6.2 Decepticon 적용

```python
# Decepticon SandboxPolicy
@dataclass
class SandboxPolicy:
    workspace: str              # /workspace/<engagement>
    evidence_dir: str           # /workspace/<engagement>/evidence
    tools_dir: str              # /workspace/<engagement>/.tools
    
    allowed_write: list[str]    # evidence, findings, reports만
    denied_paths: list[str]     # /etc, /root, /var 등
    
    network_policy: str         # "target_only" | "isolated" | "open"
    max_execution_time: int     # 초
    max_output_size: int        # 바이트
    
    def validate_path(self, path: str, mode: str) -> bool:
        """경로 접근 검증."""
        if mode == "write":
            return any(path.startswith(p) for p in self.allowed_write)
        return not any(path.startswith(p) for p in self.denied_paths)
```

## 7. Security Audit Framework

### 7.1 OpenClaw Doctor + Security Audit

**Source**: `src/plugin-sdk/security-audit.ts`, `SECURITY.md`

```bash
# 자동 진단
openclaw doctor
# - DM 정책 검증
# - allowlist 검증
# - 토큰 노출 확인
# - 설정 취약점 탐지

# 보안 감사
openclaw security audit
# - 모든 채널의 DM 정책 검사
# - allowlist 범위 검사
# - 노출된 포트/서비스 검사
# - 플러그인 보안 검사
```

### 7.2 보안 스캐닝 (설치 시)

```
플러그인 설치 시 자동 보안 검사:
1. 아카이브 무결성 (SHA-256)
2. 매니페스트 검증 (필수 필드, 스키마)
3. 설정 스키마 준수
4. 의존성 스캐닝 (선택적)
5. before_install 훅으로 커스텀 검사 가능
```

### 7.3 Decepticon Security Audit 설계

```python
# Decepticon 보안 감사 프레임워크
class DecepticonSecurityAudit:
    checks = [
        # RoE 검증
        "roe_loaded",              # RoE 파일 로드됨
        "roe_scope_defined",       # 스코프 정의됨
        "roe_time_window_set",     # 허용 시간대 설정
        "roe_exclusions_listed",   # 제외 대상 명시
        
        # OPSEC 검증
        "opsec_levels_assigned",   # 모든 목표에 OPSEC 레벨
        "sandbox_isolation",       # sandbox 네트워크 격리
        "evidence_encryption",     # 증거 암호화 설정
        "log_integrity",          # 로그 무결성 해시
        
        # 접근 제어
        "operator_allowlist",      # 운영자 allowlist 설정
        "discord_dm_pairing",      # DM 페어링 활성
        "channel_binding",         # 채널 → 인게이지먼트 바인딩
        
        # 인프라
        "api_key_not_exposed",     # API 키 환경변수 사용
        "sandbox_network_isolated",# Docker 네트워크 격리
        "gateway_auth_enabled",    # Gateway 인증 활성
    ]
    
    async def audit(self) -> AuditReport:
        results = {}
        for check in self.checks:
            results[check] = await getattr(self, f"check_{check}")()
        return AuditReport(results)
```

## 8. OpenClaw → Decepticon OPSEC 매핑 테이블

| OpenClaw Security | Decepticon OPSEC | 구현 방식 |
|-------------------|-----------------|----------|
| DM pairing | 운영자 인증 | 페어링 코드 → Discord ID allowlist |
| Allowlist (per-guild) | 인게이지먼트 접근 제어 | engagement → operators 매핑 |
| Mention gating | 명시적 지시 | @봇 멘션 시에만 목표 실행 |
| SSRF protection | 내부 네트워크 방어 | sandbox-net 격리 + URL 검증 |
| Docker sandbox | Kali sandbox | 공격 도구 격리 + 네트워크 제한 |
| ToolFsPolicy | SandboxPolicy | workspace/evidence만 쓰기 허용 |
| Config hot-reload | RoE hot-reload | RoE 변경 시 즉시 적용 |
| Security audit | OPSEC audit | RoE/OPSEC/접근제어 자동 검증 |
| before_tool_call | before_execute | 모든 명령 실행 전 RoE 검증 |
| after_tool_call | after_execute | 증거 자동 캡처 + KG 업데이트 |
| before_install | module_install | 공격 모듈 보안 스캐닝 |
| Device tokens | Session tokens | 운영자 세션 토큰 관리 |

## 9. 보안 모범 사례 (Decepticon 적용)

### 9.1 인증 & 접근 제어
```
1. 모든 접근에 인증 필수 (shared-secret 최소)
2. 운영자 allowlist (Discord 사용자 ID 기반)
3. 역할 기반 접근 (admin → operator → viewer)
4. 인게이지먼트별 접근 격리
5. 감사 로그 (모든 명령, 모든 결과)
```

### 9.2 실행 격리
```
1. Docker sandbox 필수 (Kali Linux)
2. sandbox-net 네트워크 격리
3. 대상만 접근 가능 (RoE 스코프)
4. 파일시스템 경계 (workspace만 쓰기)
5. 실행 시간 제한 (목표별 타임아웃)
```

### 9.3 증거 보호
```
1. 증거 파일 해시 무결성
2. 타임스탬프 기록 (변경 불가)
3. 암호화 저장 (선택적)
4. 접근 로그 (누가, 언제, 무엇을)
5. 보고서 생성 시 원본 보존
```

### 9.4 OPSEC 가드레일
```
1. before_execute: RoE 범위 검증 (모든 명령)
2. before_execute: 시간 윈도우 검증 (허용 시간대)
3. before_execute: OPSEC 레벨별 속도 제한
4. after_execute: 증거 자동 캡처
5. after_execute: 디컨플릭션 검증
6. on_violation: 즉시 알림 + 명령 차단
```
