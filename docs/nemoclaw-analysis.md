# NVIDIA NemoClaw 기술 분석

> 분석일: 2026-03-19 | 대상 버전: NemoClaw Alpha (GTC 2026 발표)
>
> 이 문서는 NVIDIA NemoClaw의 아키텍처, 기술 스택, 보안 메커니즘을
> Decepticon 관점에서 분석한 레퍼런스 자료입니다.

---

## 1. 개요

NVIDIA NemoClaw는 2026년 3월 16일 GTC 2026에서 발표된 **오픈소스 AI 에이전트
보안/거버넌스 스택**이다. 자율형 AI 에이전트 플랫폼인 OpenClaw에 엔터프라이즈급
보안 레이어를 추가하는 것이 핵심 목적이다.

- **NemoClaw = OpenClaw + OpenShell + Nemotron**
- 에이전트 레이어(OpenClaw)와 제어 레이어(NemoClaw/OpenShell)가 분리된 아키텍처
- OpenClaw 경쟁자가 아닌 **enterprise wrapper** — 방어적 거버넌스 도구
- 라이선스: Apache 2.0
- 현재 상태: **Alpha** (rough edges 예상, 프로덕션 미권장)

### 배경: OpenClaw

| 시점 | 이벤트 |
|------|--------|
| 2025-11 | Peter Steinberger가 "Clawdbot" 공개 |
| 2026-01 | 바이럴 확산, Anthropic 상표 이의 → "Moltbot" → "OpenClaw" 리네이밍 |
| 2026-02-14 | Steinberger, OpenAI 합류; 프로젝트 오픈소스 재단 이관 |
| 2026-03-16 | NVIDIA, GTC 2026에서 NemoClaw 발표 |

Jensen Huang: *"OpenClaw is the operating system for personal AI... as big as HTML, as big as Linux."*

---

## 2. 아키텍처

### 2.1 핵심 컴포넌트

```
┌──────────────────────────────────────────────────────┐
│  NemoClaw Stack                                      │
│                                                      │
│  ┌─────────────┐  ┌──────────────────────────────┐   │
│  │  TypeScript  │  │  Python Blueprint             │   │
│  │  Plugin      │  │  (nemoclaw-blueprint/)        │   │
│  │             │──▶│  - blueprint.yaml (manifest)  │   │
│  │  openclaw   │  │  - orchestrator/runner.py     │   │
│  │  nemoclaw   │  │  - policies/*.yaml            │   │
│  │  CLI cmds   │  └──────────┬───────────────────┘   │
│  └─────────────┘             │                       │
│                              ▼                       │
│  ┌───────────────────────────────────────────────┐   │
│  │  NVIDIA OpenShell Runtime                      │   │
│  │                                                │   │
│  │  ┌──────────┐ ┌──────────┐ ┌───────────────┐  │   │
│  │  │ Gateway  │ │ Sandbox  │ │ Policy Engine │  │   │
│  │  │ (K3s)   │ │ (OCI)    │ │ (out-of-proc) │  │   │
│  │  └──────────┘ └──────────┘ └───────────────┘  │   │
│  │                                                │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │ Privacy Router (inference routing)       │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └───────────────────────────────────────────────┘   │
│                                                      │
│  ┌───────────────────────────────────────────────┐   │
│  │  Nemotron 3 Super 120B (local inference)      │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

| 컴포넌트 | 역할 |
|----------|------|
| **TypeScript Plugin** | OpenClaw CLI에 `openclaw nemoclaw` 명령 등록. launch/connect/status/logs/slash 명령 제공 |
| **Python Blueprint** | 버전 관리되는 오케스트레이션 아티팩트. 샌드박스 생성, 정책 적용, 추론 설정 담당 |
| **OpenShell Gateway** | K3s 기반 control-plane API. 샌드박스 라이프사이클 및 인증 경계 조율 |
| **Sandbox** | 격리된 OCI 컨테이너. 정책 기반 egress 라우팅으로 에이전트 실행 |
| **Policy Engine** | **out-of-process** 정책 평가. 에이전트가 접근/수정/종료 불가 |
| **Privacy Router** | 추론 요청을 로컬(Nemotron) 또는 클라우드(Claude, GPT 등)로 라우팅 |

### 2.2 인프라 런타임

모든 컴포넌트가 **단일 Docker 컨테이너 내부의 K3s Kubernetes 클러스터**로 실행된다.
별도의 K8s 설치가 불필요하다.

### 2.3 Blueprint 라이프사이클

```
Resolve → Verify → Plan → Apply → Status
```

1. **Resolve** — 아티팩트 위치, `blueprint.yaml`의 `min_openshell_version` / `min_openclaw_version` 확인
2. **Verify** — 다이제스트 검증
3. **Plan** — 생성/갱신할 OpenShell 리소스 결정 (gateway, providers, sandbox, inference route, policy)
4. **Apply** — `openshell` CLI 호출로 리소스 적용
5. **Status** — 현재 상태 리포트

### 2.4 디렉토리 구조

```
NemoClaw/
├── .agents/skills/              # 에이전트 스킬 디렉토리
├── bin/                         # 실행 바이너리
├── docs/                        # 문서
├── nemoclaw-blueprint/          # Python blueprint
│   ├── blueprint.yaml           # 매니페스트 (버전, 프로필, 호환성)
│   ├── orchestrator/runner.py   # CLI runner
│   └── policies/
│       └── openclaw-sandbox.yaml  # 기본 보안 정책
├── nemoclaw/                    # TypeScript 플러그인
├── scripts/                     # 유틸리티 스크립트
├── test/                        # 테스트
├── Dockerfile                   # 샌드박스 이미지 빌드
├── install.sh / uninstall.sh    # 설치/제거
├── package.json                 # Node.js 의존성
└── pyproject.toml               # Python 의존성
```

---

## 3. 보안 메커니즘: OpenShell

### 3.1 Defense-in-Depth 4계층 정책

OpenShell은 **deny-by-default** 원칙을 따른다. 에이전트는 제로 권한에서 시작하며,
명시적으로 승인된 행동만 수행할 수 있다.

| 계층 | 보호 대상 | 정책 유형 | 적용 시점 |
|------|----------|----------|----------|
| **Filesystem** | `/sandbox`, `/tmp` 외 읽기/쓰기 차단 | Static | 샌드박스 생성 시 고정 |
| **Network** | 허용되지 않은 아웃바운드 연결 차단 | Dynamic | 런타임 핫-리로드 가능 |
| **Process** | 권한 상승, 위험한 syscall 차단 | Static | 샌드박스 생성 시 고정 |
| **Inference** | 모델 API 호출을 통제된 백엔드로 라우팅 | Dynamic | 런타임 핫-리로드 가능 |

### 3.2 Out-of-Process 정책 엔진

핵심 설계 결정: 정책 평가가 **에이전트의 주소 공간 외부**에서 실행된다.

- 에이전트가 정책 엔진에 접근, 수정, 종료 불가
- Binary → Destination → Method → Path 4단계 평가
- 침해된 에이전트도 정책을 우회할 수 없음

#### 커널 수준 격리 메커니즘

OpenShell은 3가지 Linux 커널 메커니즘을 결합한다:

| 메커니즘 | 역할 | 요구사항 |
|----------|------|---------|
| **Landlock** | 파일시스템 접근 제한 (fine-grained path-level) | Linux Kernel >= 5.13 |
| **seccomp** | 위험 syscall 차단 (raw socket, kernel module loading 등) | 표준 Linux |
| **Network namespaces** | 네트워크 격리 | 표준 Linux |

또한 OPA/Rego 정책으로 per-binary 수준의 세밀한 제어가 가능하다.

> **참고:** 현재 Linux만 지원. Windows WSL2는 실험적이며 GPU 감지 이슈 존재.

### 3.3 YAML 정책 설정

정책 파일은 선언적 YAML이며 4개 도메인을 커버한다:

```yaml
# nemoclaw-blueprint/policies/openclaw-sandbox.yaml (개념적 구조)

filesystem:
  # Static — 생성 시 고정, 변경 불가
  read_write:
    - /sandbox
    - /tmp
  read_only:
    - /usr
    - /bin
    - /lib

network:
  # Dynamic — openshell policy set 으로 런타임 변경 가능
  allow:
    - host: api.nvidia.com
      port: 443
      methods: [GET, POST]
    - host: github.com
      port: 443
  # 미등록 목적지는 TUI에서 실시간 승인/거부 프롬프트

process:
  # Static — 생성 시 고정
  block_privilege_escalation: true
  blocked_syscalls:
    - ptrace
    - mount
    - unshare

inference:
  # Dynamic — 런타임 변경 가능
  default_provider: nvidia
  default_model: nvidia/nemotron-3-super-120b-a12b
  privacy_routing:
    sensitive: local     # Nemotron 로컬
    general: cloud       # Claude, GPT 등 클라우드
```

**정책 적용 모드:**

| 모드 | 방법 | 지속성 |
|------|------|--------|
| **Static (영구)** | YAML 편집 후 `nemoclaw onboard`로 샌드박스 재생성 | 다음 생성 시 적용 |
| **Dynamic (세션)** | `openshell policy set` | 즉시 적용, 중지 시 리셋 |

**정책 관리 CLI:**

```bash
# 정책 적용 (핫 리로드)
openshell policy set demo --policy examples/policy.yaml --wait

# 정책 자동 생성 (plain-language → YAML)
generate-sandbox-policy  # 자연어 요구사항에서 YAML 정책 생성
```

**Operator 승인 플로우:** 에이전트가 미등록 호스트에 접근 시도 시 OpenShell이 요청을
차단하고, TUI(`openshell term`)에서 운영자에게 실시간 승인/거부를 프롬프트한다.
승인된 엔드포인트는 세션 정책에 자동 추가된다.

### 3.4 Intent Verification

단순한 행동 제한을 넘어, NemoClaw는 **의도 검증(intent verification)** 메커니즘을
사용한다. 에이전트가 수행하려는 행동의 의도를 분석하고, 정책과 대조하여 실행 전에
검증한다.

### 3.5 Privacy Router 상세

추론 요청이 샌드박스에서 직접 외부로 나가지 않는다. OpenShell이 모든 호출을 가로채
정책에 따라 라우팅한다.

| 데이터 민감도 | 라우팅 | 모델 |
|-------------|--------|------|
| **민감** | 로컬 (on-premise) | Nemotron 3 Super 120B |
| **비민감** | 클라우드 | Claude, GPT-5 등 프론티어 모델 |

- 클라우드 라우팅 전 **Gretel 차등 프라이버시 기술**로 PII 자동 스트리핑
- 모든 라우팅 결정이 감사 로그에 기록 (컴플라이언스용)
- 라우팅은 비용/프라이버시 정책을 따르며, 에이전트의 선호가 아닌 운영자의 정책이 우선

### 3.6 Credential 관리

- 크레덴셜은 named provider bundle로 관리
- 샌드박스 파일시스템에 **절대 기록되지 않음** — 환경변수로 주입
- `openshell provider create`로 명시적 생성 또는 셸 환경에서 자동 검색

**Provider 설정 예시 (Ollama 로컬):**

```bash
openshell provider create \
  --name ollama-local \
  --type openai \
  --credential "OPENAI_API_KEY=ollama" \
  --config "OPENAI_BASE_URL=http://host.openshell.internal:11434/v1"

openshell inference set --provider ollama-local --model nemotron-3-super:120b --no-verify
```

---

## 4. Nemotron 3 Super 120B

NemoClaw의 기본 로컬 추론 모델이다.

### 4.1 아키텍처 스펙

| 항목 | 스펙 |
|------|------|
| **아키텍처** | Mamba2-Transformer Hybrid Latent MoE + Multi-Token Prediction |
| **전체 파라미터** | 120.6B |
| **활성 파라미터** | 12.7B per forward pass (12.1B excluding embeddings) |
| **레이어** | 88 layers (interleaved Mamba-2 + sparse attention anchor layers) |
| **Mamba:Transformer 비율** | 75:25 |
| **컨텍스트 윈도우** | 1M tokens (네이티브) |
| **학습 토큰** | 25T (10T 고유 큐레이션 토큰) |
| **학습 정밀도** | NVFP4 (네이티브 4비트 학습) |
| **지원 언어** | EN, FR, DE, IT, JA, ES, ZH |
| **학습 3단계** | Pretraining → Supervised Fine-tuning → Reinforcement Learning |
| **배포 포맷** | BF16, FP8, NVFP4, GGUF |
| **API 가격** | $0.30/M input, $0.75/M output (NVIDIA cloud) |
| **라이선스** | 오픈 (weights, datasets, recipes 모두 공개) |

### 4.2 핵심 혁신

1. **LatentMoE** — 토큰을 작은 잠재 차원으로 프로젝션 후 전문가 라우팅 → 바이트당 정확도 향상
2. **Multi-Token Prediction (MTP)** — 다음 한 토큰이 아닌 여러 후속 토큰 동시 예측 → 5x 처리량
3. **Mamba-2 레이어 (75%)** — 선형 스케일링 긴 시퀀스 처리 (SSM)
4. **NVFP4 네이티브 학습** — 사후 양자화가 아닌 처음부터 4비트 정밀도로 학습

### 4.3 성능 벤치마크

| 벤치마크 | 점수 | 비고 |
|---------|------|------|
| **PinchBench** (OpenClaw 에이전트) | 85.6% | 동급 최고 오픈 모델 |
| **SWE-Bench Verified** | 60.47% | Qwen3.5 대비 ~6pt 뒤지나 2.2x 처리량 |
| **AI Intelligence Index** | 36 | 이전 Super 대비 +17pt |
| **RULER** (1M context) | Best in class | GPT-OSS-120B, Qwen3.5-122B 능가 |
| **처리량** (8K/16K) | 442-462 tok/s | GPT-OSS 2.2x, Qwen3.5 7.5x |

**MTP 효율:** 평균 acceptance length 3.45 토큰/검증 스텝 (DeepSeek-R1: 2.70)
→ 별도 draft 모델 없이 native speculative decoding으로 최대 **3x wall-clock 속도 향상**

### 4.4 하드웨어 요구사항

전체 120B 파라미터가 VRAM에 상주해야 하므로 단일 소비자 GPU 불가.

| 구성 | 가능 여부 |
|------|----------|
| RTX 4090 (24GB) | 불가 |
| Dual 48GB (RTX 6000 Ada 등) | 최소 구성 |
| DGX Station / DGX Spark | 권장 |
| GeForce RTX PC/노트북 (FP4 양자화) | 제한적 가능 |

---

## 5. CLI 명령어 레퍼런스

### 5.1 호스트 측 (nemoclaw CLI)

```bash
# 설치
curl -fsSL https://www.nvidia.com/nemoclaw.sh | bash

# 온보딩 (7단계 대화형 설정)
# preflight → gateway → sandbox → inference → provider → OpenClaw config → policy
nemoclaw onboard

# 샌드박스 연결
nemoclaw <name> connect

# 상태 확인
nemoclaw <name> status

# 로그 스트리밍
nemoclaw <name> logs --follow

# OpenShell TUI (모니터링 + 승인)
openshell term
```

### 5.2 샌드박스 내부 (OpenClaw CLI)

```bash
# TUI 모드 (대화형 채팅)
sandbox@my-assistant:~$ openclaw tui

# CLI 단일 메시지 모드
sandbox@my-assistant:~$ openclaw agent --agent main --local -m "prompt" --session-id test
```

### 5.3 OpenShell CLI

```bash
# 샌드박스 생성 (에이전트 지정)
openshell sandbox create -- claude

# GPU 지원 샌드박스
openshell sandbox create --gpu --from [gpu-enabled-sandbox] -- claude

# 샌드박스 접속
openshell sandbox connect [name]

# 정책 적용 (핫-리로드)
openshell policy set <name> --policy file.yaml --wait

# 추론 설정
openshell inference set --provider <p> --model <m>
openshell inference get  # 현재 라우팅 설정 확인

# 상태 및 로그
openshell status            # gateway 상태
openshell sandbox list      # 활성 샌드박스 목록
openshell logs [name] --tail

# TUI (k9s 스타일 모니터링, 2초 자동 리프레시)
openshell term  # Tab=패널전환, j/k=이동, Enter=선택, :=명령
```

### 5.4 지원 에이전트

OpenShell은 다양한 에이전트를 지원한다:

| 에이전트 | 인증 | 플래그 |
|---------|------|-------|
| **Claude Code** | `ANTHROPIC_API_KEY` | (기본) |
| **OpenCode** | `OPENAI_API_KEY` / `OPENROUTER_API_KEY` | (기본) |
| **Codex** | `OPENAI_API_KEY` | (기본) |
| **OpenClaw** | 커뮤니티 | `--from openclaw` |
| **Ollama** | 로컬 추론 | `--from ollama` |

### 5.5 시스템 요구사항

| 리소스 | 최소 | 권장 |
|--------|------|------|
| CPU | 4 vCPU | 4+ vCPU |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB | 40 GB |
| 샌드박스 이미지 | ~2.4 GB (압축) | |
| OS | Ubuntu 22.04+ | |
| Node.js | 20+ | |
| 컨테이너 런타임 | Docker (Linux) / Colima (macOS) | |

---

## 6. 파트너 생태계

### 6.1 Agent Toolkit 파트너

Adobe, Salesforce, SAP, ServiceNow, Siemens, CrowdStrike, Atlassian, Palantir,
IBM Red Hat, Box, LangChain

### 6.2 보안 통합 파트너

Cisco (AI Defense + OpenShell 통합), CrowdStrike, Google, Microsoft Security, TrandAI
→ 각 보안 도구에 OpenShell 가드레일 내장 목표

CrowdStrike는 "Secure-by-Design AI Blueprint"를 발표하여 CrowdStrike Falcon을
OpenShell에 직접 통합한다.

### 6.3 하드웨어 파트너

Dell — GB300 Desktop에 NemoClaw + OpenShell **프리인스톨** 첫 번째 하드웨어 파트너

---

## 7. Decepticon과의 비교 분석

NemoClaw와 Decepticon은 AI 에이전트 보안의 **반대편**에 위치한다.

| 관점 | NemoClaw | Decepticon |
|------|----------|------------|
| **목적** | 방어 — AI 에이전트를 안전하게 실행 | 공격 — AI 에이전트로 레드팀 테스트 |
| **핵심 가치** | 샌드박싱, 정책 강제, 격리 | 자동화된 공격 시뮬레이션 |
| **에이전트 모델** | 범용 에이전트 (코딩, 지원 등) | 보안 특화 에이전트 (recon, exploit, postexploit) |
| **프레임워크** | OpenClaw + OpenShell + Nemotron | LangChain / LangGraph |
| **샌드박스** | 에이전트 자체를 격리 (방어) | 공격 도구를 격리 실행 (Kali Docker) |
| **정책 엔진** | 에이전트 행동 제한 | RoE (교전규칙)로 공격 범위 제한 |
| **추론 라우팅** | Privacy Router (로컬 vs 클라우드) | LiteLLM Proxy (멀티 프로바이더) |
| **배후** | NVIDIA (엔터프라이즈) | PurpleAILAB (오픈소스) |

### 7.1 Decepticon에 참고할 수 있는 NemoClaw 설계

| NemoClaw 설계 | Decepticon 적용 가능성 |
|--------------|----------------------|
| **4-layer YAML 정책** | RoE를 filesystem/network/process/inference 4계층으로 세분화 |
| **Out-of-process 정책 엔진** | Ralph 루프에 독립 정책 검증 프로세스 추가 |
| **Intent verification** | 에이전트 행동 의도 분석 → RoE 위반 사전 차단 |
| **Privacy Router** | 민감한 타겟 정보는 로컬 모델, 전략 계획은 클라우드 모델 |
| **Hot-reloadable 정책** | 엔게이지먼트 중 RoE 동적 갱신 |
| **generate-sandbox-policy** | 자연어 RoE → 정책 YAML 자동 생성 |
| **Blueprint 라이프사이클** | Ralph iteration에 resolve→verify→plan→apply→status 패턴 적용 |

### 7.2 NemoClaw 관점에서 Decepticon이 공격 대상으로 고려할 점

NemoClaw/OpenShell이 방어 측에 배치되면, Decepticon의 레드팀은 다음을 검증해야 한다:

| 검증 포인트 | 공격 시나리오 |
|------------|-------------|
| 정책 엔진 우회 | out-of-process 정책이 실제로 에이전트에서 분리되어 있는지 |
| Landlock/seccomp 탈출 | 커널 >= 5.13 환경에서 Landlock 바이패스 가능성 |
| 네트워크 정책 피벗 | 허용된 엔드포인트를 통한 간접 데이터 유출 |
| PII 스트리핑 무력화 | Gretel 차등 프라이버시의 인코딩 우회 |
| TUI 승인 피로 공격 | 대량 승인 요청으로 운영자 판단력 저하 유도 |
| Blueprint 검증 우회 | 다이제스트 검증 단계 조작 |

---

## 8. 알려진 한계점 (Alpha)

- OpenShell 인터셉션 레이어의 성능(지연/처리량) 영향 데이터 미공개
- YAML 기반 정책 관리는 운영 성숙도 필요
- 독립 보안 감사 미실시
- Windows WSL2에서 GPU 감지 불안정
- macOS Podman 미지원
- 로컬 추론 (Ollama, vLLM) 불안정
- DGX Spark에서 Nemotron 3 Super 로컬 추론 지연 30-90초

---

## 9. 참고 자료

- [NVIDIA NemoClaw GitHub](https://github.com/NVIDIA/NemoClaw)
- [NVIDIA OpenShell GitHub](https://github.com/NVIDIA/OpenShell)
- [NVIDIA NemoClaw 공식 발표](https://nvidianews.nvidia.com/news/nvidia-announces-nemoclaw)
- [NemoClaw Developer Guide — Architecture](https://docs.nvidia.com/nemoclaw/latest/reference/architecture.html)
- [NemoClaw Developer Guide — Network Policies](https://docs.nvidia.com/nemoclaw/latest/reference/network-policies.html)
- [Nemotron 3 Super 기술 리포트](https://research.nvidia.com/labs/nemotron/files/NVIDIA-Nemotron-3-Super-Technical-Report.pdf)
- [Nemotron 3 Super NIM Model Card](https://build.nvidia.com/nvidia/nemotron-3-super-120b-a12b/modelcard)
- [OpenShell 기술 블로그](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/)
- [VentureBeat — NemoClaw Deep Dive](https://venturebeat.com/technology/nvidia-lets-its-claws-out-nemoclaw-brings-security-scale-to-the-agent)
- [The New Stack — NemoClaw is OpenClaw with Guardrails](https://thenewstack.io/nemoclaw-openclaw-with-guardrails/)
- [TechCrunch — NVIDIA's OpenClaw Security Solution](https://techcrunch.com/2026/03/16/nvidias-version-of-openclaw-could-solve-its-biggest-problem-security/)
- [Geeky Gadgets — NemoClaw Enterprise Security](https://www.geeky-gadgets.com/nvidia-nemoclaw-enterprise-security/)
- [Nemotron 3 Super 연구 페이지](https://research.nvidia.com/labs/nemotron/Nemotron-3-Super/)
- [Hugging Face — Nemotron 3 Super 120B BF16](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16)
- [CrowdStrike — Secure-by-Design AI Blueprint](https://www.crowdstrike.com/en-us/press-releases/crowdstrike-nvidia-unveil-secure-by-design-ai-blueprint-for-ai-agents/)
- [PinchBench Leaderboard](https://pinchbench.com/)
- [DEV Community — OpenClaw vs NanoClaw vs NemoClaw](https://dev.to/mechcloud_academy/architecting-the-agentic-future-openclaw-vs-nanoclaw-vs-nvidias-nemoclaw-9f8)
