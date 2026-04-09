# OpenClaw Plugin SDK & Extension Architecture Deep Dive

> Decepticon의 공격 모듈 시스템(AttackModuleRegistry) 구현을 위한 OpenClaw 플러그인 아키텍처 완전 분석

## 1. 플러그인 설계 원칙

| 원칙 | 설명 | Decepticon 적용 |
|------|------|----------------|
| **Core stays lean** | 코어에 기능 추가 대신 플러그인으로 분리 | 공격 모듈은 모두 플러그인 |
| **Extension-agnostic core** | 코어가 특정 확장을 이름으로 참조하면 안됨 | 스캐너/익스플로잇 모듈은 코어에서 분리 |
| **Capability registration** | 플러그인이 능력을 명시적으로 등록 | 모듈이 자신의 공격 능력을 등록 |
| **Manifest-first** | 코드 실행 없이 메타데이터 로딩 가능 | 모듈 디스커버리 시 코드 실행 불필요 |
| **Narrow subpath imports** | 각 import는 구체적이어야 (startup 빠르게) | 필요한 모듈만 로딩 |

## 2. Plugin Loading Pipeline (4단계)

**Source**: `src/plugins/loader.ts`, `src/plugins/discovery.ts`

```
Phase 1: Manifest + Discovery
    ↓ (코드 실행 없이 메타데이터만 읽기)
Phase 2: Enablement + Validation
    ↓ (설정 대조, 스키마 검증, 적격성 확인)
Phase 3: Runtime Loading
    ↓ (jiti를 통한 플러그인 코드 로딩, register(api) 호출)
Phase 4: Surface Consumption
    ↓ (도구, 채널, 프로바이더, 훅 노출)
```

### Phase 1: Manifest + Discovery

**코드 실행 없이** 플러그인 메타데이터를 수집한다.

**디스커버리 소스** (우선순위 순):
1. **Bundled plugins** — OpenClaw 패키지에 포함된 플러그인
2. **Workspace plugins** — `<workspace>/plugins/`
3. **Global plugins** — `~/.openclaw/plugins/`
4. **npm packages** — `openclaw.plugin.json` 매니페스트 보유 패키지
5. **ClawHub** — 커뮤니티 마켓플레이스에서 설치된 플러그인

**매니페스트 형식** (`openclaw.plugin.json`):
```json
{
  "id": "my-scanner",
  "name": "My Scanner Plugin",
  "description": "Nuclei-based vulnerability scanner",
  "version": "1.0.0",
  "providers": ["my-scanner-provider"],
  "cliBackends": [],
  "configSchema": {
    "type": "object",
    "additionalProperties": false,
    "properties": {
      "templates": { "type": "string", "description": "Nuclei template path" }
    }
  },
  "providerAuthEnvVars": {},
  "channelEnvVars": {}
}
```

### Phase 2: Enablement + Validation

설정과 환경을 대조하여 플러그인 활성화 여부를 결정한다.

**활성화 소스**:
| Source | 예시 |
|--------|------|
| 매니페스트 메타데이터 | auto-enable 조건 |
| Config enablement | `config.plugins.<id>.enabled: true` |
| Capability ownership | 모델 프로바이더 자동 활성화 |
| Memory slot selection | 독점 메모리 플러그인 선택 |
| Bundled defaults | 번들 플러그인 자동 활성화 |

**검증 항목**:
- Config schema compliance (zod `.safeParse()` 또는 `.validate()`)
- JSON schema 검증 (fallback)
- 에러 메시지 집계

**PluginLoadOptions**:
```typescript
type PluginLoadOptions = {
  config?: OpenClawConfig;
  activationSourceConfig?: OpenClawConfig;
  autoEnabledReasons?: Record<string, string[]>;
  workspaceDir?: string;
  env?: NodeJS.ProcessEnv;
  logger?: PluginLogger;
  coreGatewayHandlers?: Record<string, GatewayRequestHandler>;
  runtimeOptions?: CreatePluginRuntimeOptions;
};
```

### Phase 3: Runtime Loading

jiti를 통해 플러그인 코드를 실제 로딩하고 `register(api)` 호출한다.

```typescript
// 플러그인 진입점 패턴
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

export const plugin = definePluginEntry({
  id: "nuclei-scanner",
  configSchema: nucleiConfigSchema,
  register(api) {
    // 능력 등록
    api.registerTool(nucleiScanToolFactory, { optional: false });
    api.registerHook(scanCompletionHook);
  }
});
```

### Phase 4: Surface Consumption

등록된 능력(도구, 채널, 프로바이더, 훅)이 에이전트와 Gateway에 노출된다.

```
등록된 능력 → PluginRegistry에 저장
    ↓
에이전트 실행 시:
  - 도구: 에이전트에 도구 목록 제공
  - 프로바이더: 모델 선택 시 사용 가능
  - 훅: 라이프사이클 이벤트에 자동 연결
  - 채널: 메시지 라우팅에 포함
```

## 3. Capability Registration Model

### 3.1 OpenClawPluginApi — 전체 등록 메서드

**Source**: `src/plugins/types.ts`

```typescript
type OpenClawPluginApi = {
  // === 텍스트 추론 ===
  registerProvider(provider: ProviderPlugin): void;
  registerCliBackend(backend: CliBackendPlugin): void;
  
  // === 채널/메시징 ===
  registerChannel(registration: ChannelPlugin): void;
  
  // === 도구 ===
  registerTool(factory: ToolFactory, opts?: ToolOptions): void;
  
  // === 훅 ===
  registerHook(hook: PluginHook, opts?: HookOptions): void;
  
  // === 미디어 생성 ===
  registerImageGenerationProvider(...): void;
  registerMusicGenerationProvider(...): void;
  registerVideoGenerationProvider(...): void;
  
  // === 음성/오디오 ===
  registerSpeechProvider(...): void;
  registerRealtimeTranscriptionProvider(...): void;
  registerRealtimeVoiceProvider(...): void;
  
  // === 미디어 이해 ===
  registerMediaUnderstandingProvider(...): void;
  
  // === 웹 ===
  registerWebFetchProvider(...): void;
  registerWebSearchProvider(...): void;
  
  // === 컨텍스트 ===
  registerCompactionProvider(...): void;
  
  // === 총 15+ 등록 메서드 ===
};
```

### 3.2 Capability 유형별 설명

| Capability | 등록 메서드 | 예시 플러그인 | Decepticon 대응 |
|------------|-----------|-------------|----------------|
| Text inference | `registerProvider` | anthropic, openai | LLM 프로바이더 (LiteLLM이 대체) |
| CLI inference | `registerCliBackend` | anthropic, openai | — |
| Channel | `registerChannel` | discord, telegram, matrix | Discord 레드팀 채널 |
| Tool | `registerTool` | browser, canvas | bash, nmap, nuclei 도구 |
| Hook | `registerHook` | lifecycle hooks | OPSEC 가드레일 훅 |
| Image generation | `registerImageGenerationProvider` | openai, google | — |
| Speech synthesis | `registerSpeechProvider` | elevenlabs | — |
| Transcription | `registerRealtimeTranscriptionProvider` | openai | — |
| Voice | `registerRealtimeVoiceProvider` | openai | — |
| Media understanding | `registerMediaUnderstandingProvider` | openai, google | 스크린샷 분석 |
| Web fetch | `registerWebFetchProvider` | firecrawl | 웹 정찰 |
| Web search | `registerWebSearchProvider` | google | OSINT 검색 |
| Compaction | `registerCompactionProvider` | custom | 컨텍스트 관리 |

### 3.3 Plugin Shapes (플러그인 형태)

| Shape | 설명 | 예시 |
|-------|------|------|
| **plain-capability** | 단일 능력 유형 | mistral = provider only |
| **hybrid-capability** | 복수 능력 유형 | openai = text + speech + image |
| **hook-only** | 능력 없이 훅만 | 레거시 패턴 |
| **non-capability** | 도구/명령/서비스만 | CLI 확장 |

## 4. Tool Context Injection

### 4.1 OpenClawPluginToolContext

**Source**: `src/plugins/types.ts`

모든 도구는 실행 시 **풍부한 컨텍스트**를 주입받는다:

```typescript
type OpenClawPluginToolContext = {
  // === 설정 ===
  config?: OpenClawConfig;          // 전체 Gateway 설정
  runtimeConfig?: OpenClawConfig;   // 런타임 오버라이드 포함
  
  // === 파일시스템 ===
  fsPolicy?: ToolFsPolicy;         // 파일시스템 경계 정책
  workspaceDir?: string;           // 에이전트 작업 디렉토리
  agentDir?: string;               // 에이전트 상태 디렉토리
  
  // === 에이전트 ===
  agentId?: string;                // 실행 중인 에이전트 ID
  
  // === 세션 ===
  sessionKey?: string;             // 세션 라우팅 키
  sessionId?: string;              // 임시 UUID (reset 시 재생성)
  
  // === 브라우저 ===
  browser?: {
    sandboxBridgeUrl?: string;     // 샌드박스 브라우저 URL
    allowHostControl?: boolean;     // 호스트 브라우저 제어 허용
  };
  
  // === 메시징 ===
  messageChannel?: string;         // 메시지가 온 채널
  agentAccountId?: string;         // 채널 계정 ID
  
  // === 보안 ===
  deliveryContext?: DeliveryContext; // 전달 컨텍스트
  requesterSenderId?: string;       // 요청자 ID
  senderIsOwner?: boolean;          // 소유자 여부
  sandboxed?: boolean;              // 샌드박스 내 실행 여부
};
```

### 4.2 Tool Factory 패턴

```typescript
// 도구 팩토리: 컨텍스트 → 도구 인스턴스
type OpenClawPluginToolFactory = (
  ctx: OpenClawPluginToolContext
) => AnyAgentTool | AnyAgentTool[] | null | undefined;

// 예시: 조건부 도구 생성
const nucleiToolFactory: OpenClawPluginToolFactory = (ctx) => {
  // 샌드박스 아닌 환경에서는 도구 비활성
  if (!ctx.sandboxed) return null;
  
  // 도구 인스턴스 반환
  return createNucleiTool({
    workdir: ctx.workspaceDir,
    config: ctx.config?.plugins?.nuclei,
  });
};
```

### 4.3 ToolFsPolicy (파일시스템 정책)

```typescript
// 도구별 파일시스템 경계 강제
type ToolFsPolicy = {
  allowedPaths: string[];    // 접근 허용 경로
  deniedPaths: string[];     // 접근 거부 경로
  readOnly?: boolean;        // 읽기 전용 여부
};
```

**Decepticon 적용**: 각 공격 모듈이 자신의 workspace와 evidence 디렉토리만 접근 가능하도록 제한

## 5. Hook System Internals

### 5.1 전체 훅 이벤트 목록

**Source**: `src/plugins/hooks.ts`

| Category | Hook | When | Return |
|----------|------|------|--------|
| **Agent** | `before_agent_start` | 에이전트 시작 전 | — |
| | `before_agent_reply` | LLM 호출 전 | claim/silence 가능 |
| | `agent_end` | 에이전트 완료 후 | — |
| **Model** | `before_model_resolve` | 모델 선택 전 | provider/model 오버라이드 |
| | `before_prompt_build` | 프롬프트 빌드 전 | context 주입 |
| **Tool** | `before_tool_call` | 도구 실행 전 | block 가능 |
| | `after_tool_call` | 도구 실행 후 | 결과 변환 |
| | `tool_result_persist` | 결과 저장 전 | redact/변환 |
| **Message** | `message_received` | 인바운드 메시지 | — |
| | `message_sending` | 아웃바운드 전 | cancel 가능 |
| | `message_sent` | 전송 완료 후 | — |
| | `before_message_write` | 메시지 기록 전 | 변환 |
| **Dispatch** | `before_dispatch` | 라우팅 전 | — |
| | `reply_dispatch` | 응답 라우팅 | — |
| | `inbound_claim` | 인바운드 클레임 | 라우팅 변경 |
| **LLM I/O** | `llm_input` | LLM 요청 전 | — |
| | `llm_output` | LLM 응답 후 | — |
| **Subagent** | `subagent_spawning` | 서브에이전트 스폰 전 | — |
| | `subagent_delivery_target` | 전달 대상 결정 | — |
| | `subagent_ended` | 서브에이전트 완료 | — |
| **Session** | `session_start` | 세션 시작 | — |
| | `session_end` | 세션 종료 | — |
| **Gateway** | `gateway_start` | Gateway 시작 | — |
| | `gateway_stop` | Gateway 종료 | — |
| **Compaction** | `before_compaction` | 압축 전 | — |
| | `after_compaction` | 압축 후 | — |
| **Install** | `before_install` | 설치 전 | block 가능 |

### 5.2 훅 실행 모델

```
훅 등록 시:
  api.registerHook(hook, { priority?: number })

훅 실행 시:
  1. 우선순위 순서로 정렬
  2. 비동기 지원 (async hooks)
  3. 에러 발생 시 로깅 후 계속 실행 (다음 훅)
  4. 결과 집계 (이벤트 컨텍스트에 폴딩)

Terminal 동작:
  - before_tool_call: { block: true } → 이후 핸들러 중단
  - message_sending: { cancel: true } → 이후 핸들러 중단
  - before_install: { block: true } → 이후 핸들러 중단
  - { block: false } / { cancel: false } → no-op (이전 block/cancel 유지)
```

### 5.3 Decepticon OPSEC 훅 매핑

| OpenClaw Hook | Decepticon OPSEC Hook |
|---------------|----------------------|
| `before_tool_call` | RoE 범위 검증, OPSEC 레벨 체크, 속도 제한 |
| `after_tool_call` | 증거 자동 캡처, KG 업데이트 |
| `before_agent_reply` | 민감정보 필터링, OPSEC 등급 주입 |
| `agent_end` | 자동 보고서 생성, Discord 알림 |
| `subagent_spawning` | 스폰 전 RoE 검증, sandbox 할당 |
| `subagent_ended` | 목표 상태 업데이트, 다음 목표 스케줄링 |
| `before_prompt_build` | OPPLAN battle tracker 주입 |
| `tool_result_persist` | 증거 경로 기록, 해시 무결성 |

## 6. ClawHub & Marketplace

### 6.1 ClawHub (공식 마켓플레이스)

**Source**: `src/plugins/clawhub.ts`

```typescript
type ClawHubPluginInstallRecordFields = {
  source: "clawhub";
  clawhubUrl: string;
  clawhubPackage: string;
  clawhubFamily: "extension" | "plugin" | "bundle" | "integration";
  clawhubChannel?: "stable" | "beta" | "dev";
  version?: string;
  integrity?: string;     // SHA-256 해시
  resolvedAt?: string;
  installedAt?: string;
};
```

**설치 흐름**:
```
1. 플러그인 spec 파싱 (예: @user/plugin@1.0.0)
    ↓
2. ClawHub API에서 패키지 메타데이터 fetch
    ↓
3. Gateway + Plugin API 버전 호환성 확인
    ↓
4. 패키지 아카이브 다운로드 + SHA-256 무결성 검증
    ↓
5. 플러그인 디렉토리에 추출 + 설치
    ↓
6. 매니페스트 + 설정 스키마 검증
```

**에러 코드**:
```typescript
const CLAWHUB_INSTALL_ERROR_CODE = {
  INVALID_SPEC: "invalid_spec",
  PACKAGE_NOT_FOUND: "package_not_found",
  VERSION_NOT_FOUND: "version_not_found",
  NO_INSTALLABLE_VERSION: "no_installable_version",
  SKILL_PACKAGE: "skill_package",
  UNSUPPORTED_FAMILY: "unsupported_family",
  PRIVATE_PACKAGE: "private_package",
  INCOMPATIBLE_PLUGIN_API: "incompatible_plugin_api",
  INCOMPATIBLE_GATEWAY: "incompatible_gateway",
  MISSING_ARCHIVE_INTEGRITY: "missing_archive_integrity",
  ARCHIVE_INTEGRITY_MISMATCH: "archive_integrity_mismatch",
};
```

### 6.2 Community Marketplace

**Source**: `src/plugins/marketplace.ts`

```typescript
type MarketplaceEntrySource = 
  | { kind: "path"; path: string }         // 로컬 경로
  | { kind: "github"; repo: string }       // GitHub 레포
  | { kind: "git"; url: string }           // Git URL
  | { kind: "git-subdir"; url: string; path: string }  // Git 서브디렉토리
  | { kind: "url"; url: string };          // 직접 URL

type MarketplaceManifest = {
  name?: string;
  version?: string;
  plugins: MarketplacePluginEntry[];       // 플러그인 목록
};
```

### 6.3 보안 스캐닝

설치 시 자동 보안 검사:
- 아카이브 무결성 (SHA-256)
- 매니페스트 검증
- 설정 스키마 준수
- 선택적 의존성 스캐닝

## 7. Plugin SDK Subpath Architecture

### 7.1 모듈 구조

```
src/plugin-sdk/
  ├── plugin-entry.ts              # definePluginEntry
  ├── core.ts                      # 코어 API
  │
  ├── channel-core.ts              # 채널 진입점
  ├── channel-contract.ts          # 채널 인터페이스
  ├── channel-config-helpers.ts    # 설정 헬퍼
  ├── channel-inbound.ts           # 디바운스, 멘션 매칭
  ├── channel-reply-pipeline.ts    # 응답 파이프라인
  │
  ├── provider-entry.ts            # 프로바이더 진입점
  ├── provider-auth-*.ts           # 인증 방식별 (30+ 파일)
  ├── provider-model-shared.ts     # 모델 카탈로그
  ├── provider-stream*.ts          # 스트리밍 래퍼
  │
  ├── config-schema.ts             # Zod 스키마
  ├── setup-tools.ts               # 바이너리 감지, 아카이브 추출
  ├── ssrf-policy.ts               # SSRF 보호
  ├── security-audit.ts            # 보안 감사
  │
  └── thread-bindings-runtime.ts   # 스레드 바인딩
```

### 7.2 Import Convention

```typescript
// 올바른 사용 (specific subpath)
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { defineChannelPluginEntry } from "openclaw/plugin-sdk/channel-core";

// 잘못된 사용 (bundled-only helper)
import { slack } from "openclaw/plugin-sdk/slack";  // ❌ third-party에서 사용 불가
```

### 7.3 Extension Boundary Rules

| Rule | 설명 |
|------|------|
| Import boundary | 확장은 `openclaw/plugin-sdk/*`만 import 가능 |
| Core agnostic | 코어에 확장 이름 하드코딩 금지 |
| No prototype mutation | 프로토타입 변형으로 행동 공유 금지 |
| Backwards compatible | 새 seam은 버전화된 호환 계약으로만 |
| Self-import 금지 | 자기 패키지를 `plugin-sdk/<self>`로 import 금지 |

## 8. Skills System

### 8.1 스킬 vs 플러그인

| 측면 | Skill | Plugin |
|------|-------|--------|
| 형식 | Markdown (SKILL.md) | TypeScript 코드 |
| 로딩 | 에이전트 프롬프트에 주입 | jiti 런타임 로딩 |
| 능력 | 텍스트 지침 + 도구 지정 | 코드 실행, API 등록 |
| 배포 | ClawHub 또는 workspace | npm 또는 ClawHub |
| 제한 | `allowed-tools` 지정 가능 | `fsPolicy`, config schema |

### 8.2 스킬 로딩

**Source**: `src/agents/skills/workspace.ts`

**제한값**:
```typescript
maxCandidatesPerRoot: 300     // 디렉토리당 최대 후보
maxSkillsLoadedPerSource: 200 // 소스당 최대 로딩
maxSkillsInPrompt: 150        // 프롬프트 내 최대 스킬
maxSkillsPromptChars: 30000   // 프롬프트 토큰 제한
maxSkillFileBytes: 256000     // 스킬 파일 크기 제한
```

**로딩 우선순위**:
1. Workspace: `<workspace>/skills`
2. Project agent: `<workspace>/.agents/skills`
3. Personal agent: `~/.agents/skills`
4. Managed: `~/.openclaw/skills`
5. Bundled (OpenClaw 기본 제공)
6. Extra dirs: `skills.load.extraDirs`

### 8.3 스킬 프론트매터

```yaml
---
name: nuclei-scanner
description: Run Nuclei vulnerability scans
metadata:
  openclaw:
    emoji: "🔍"
    os: ["linux"]
    requires:
      bins: ["nuclei"]
      env: ["NUCLEI_TEMPLATES"]
    install:
      - id: nuclei
        kind: "go"
        package: "github.com/projectdiscovery/nuclei/v3/cmd/nuclei"
        bins: ["nuclei"]
allowed-tools: ["bash"]
---

# Nuclei Scanner Skill

Use this skill to run Nuclei template-based vulnerability scanning...
```

## 9. Decepticon AttackModuleRegistry 설계

### 9.1 OpenClaw → Decepticon 매핑

| OpenClaw | Decepticon |
|----------|-----------|
| `PluginRegistry` | `AttackModuleRegistry` |
| `definePluginEntry` | `define_attack_module` |
| `registerProvider` | `register_scanner` |
| `registerChannel` | `register_channel` (Discord) |
| `registerTool` | `register_tool` |
| `registerHook` | `register_opsec_hook` |
| `ToolFsPolicy` | `SandboxPolicy` |
| `OpenClawPluginToolContext` | `AttackToolContext` |
| ClawHub | 커뮤니티 모듈 레지스트리 |

### 9.2 Python 인터페이스 설계

```python
from abc import ABC, abstractmethod

class AttackModule(ABC):
    """OpenClaw definePluginEntry에 대응."""
    
    id: str
    name: str
    version: str
    capabilities: list[str]  # ["scanner", "exploiter", "reporter"]
    
    @abstractmethod
    def register(self, registry: AttackModuleRegistry) -> None:
        """능력 등록. OpenClaw register(api)에 대응."""
        ...

class AttackModuleRegistry:
    """OpenClaw PluginRegistry에 대응."""
    
    def register_scanner(self, scanner: ScannerPlugin) -> None: ...
    def register_exploiter(self, exploiter: ExploiterPlugin) -> None: ...
    def register_reporter(self, reporter: ReporterPlugin) -> None: ...
    def register_tool(self, factory: ToolFactory) -> None: ...
    def register_hook(self, hook: OPSECHook) -> None: ...
    
    def discover(self, dirs: list[str]) -> list[AttackModule]: ...
    def load(self, module: AttackModule) -> None: ...
    def get_tools(self, context: AttackToolContext) -> list[Tool]: ...
    def get_hooks(self, event: str) -> list[OPSECHook]: ...

class AttackToolContext:
    """OpenClaw OpenClawPluginToolContext에 대응."""
    
    config: DecepticonConfig
    sandbox: DockerSandbox
    engagement: str           # 인게이지먼트 이름
    objective: Objective       # 현재 목표
    roe: RulesOfEngagement    # RoE
    workspace: str            # 작업 디렉토리
    evidence_dir: str         # 증거 저장 디렉토리
    session_key: str          # 세션 키
```

### 9.3 4단계 로딩 파이프라인 (Python)

```python
# Phase 1: Discovery (코드 실행 없이)
modules = registry.discover([
    "decepticon/modules/",       # 번들 모듈
    "~/.decepticon/modules/",    # 사용자 모듈
    engagement.workspace + "/modules/",  # 인게이지먼트 모듈
])

# Phase 2: Validation
for module in modules:
    if not module.validate_config(config):
        log.warn(f"Module {module.id} config invalid, skipping")
        continue

# Phase 3: Loading
for module in validated_modules:
    module.register(registry)

# Phase 4: Surface consumption
tools = registry.get_tools(context)
hooks = registry.get_hooks("before_tool_call")
```
