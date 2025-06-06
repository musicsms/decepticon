import streamlit as st
import time
import os
import asyncio
from datetime import datetime
import json
from pathlib import Path
import re
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

ICON = "assets\logo.png"
ICON_TEXT = "assets\logo_text1.png"

# Streamlit 페이지 설정 
st.set_page_config(
    page_title="Decepticon",
    page_icon=ICON,
    layout="wide",
    # 테마는 테마 매니저에서 관리
)

# 테마 관리자 임포트 
from frontend.theme_manager import ThemeManager

# 테마 매니저 생성 및 세션 초기화
if "theme_manager" not in st.session_state:
    st.session_state.theme_manager = ThemeManager()

# 테마 매니저 인스턴스 가져오기
theme_manager = st.session_state.theme_manager

# 테마 및 기본 CSS 적용
theme_manager.apply_theme()

# 직접 실행 모듈 import
from frontend.direct_executor import DirectExecutor
from frontend.cli_message_processor import CLIMessageProcessor
from frontend.chat_ui import ChatUI
from frontend.terminal_ui import TerminalUI

# 모델 선택을 위한 CLI 모듈 import
MODEL_SELECTION_AVAILABLE = False
try:
    from src.utils.llm.models import list_available_models, check_ollama_connection
    MODEL_SELECTION_AVAILABLE = True
except ImportError as e:
    print(f"Model selection modules not available: {e}")
    MODEL_SELECTION_AVAILABLE = False

# 터미널 UI CSS 적용
terminal_ui = TerminalUI()
terminal_ui.apply_terminal_css()


def get_env_config() -> dict:
    """환경 설정 로드"""
    return {
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "theme": os.getenv("THEME", "dark"),
        "docker_container": os.getenv("DOCKER_CONTAINER", "decepticon-kali"),
        "chat_height": int(os.getenv("CHAT_HEIGHT", "700"))
    }


def log_debug(message: str, data=None):
    """디버그 로깅"""
    config = get_env_config()
    if config.get("debug_mode", False):
        print(f"[DEBUG] {message}")
        if data:
            print(f"[DEBUG] Data: {data}")


class DecepticonApp:
    """DecepticonV2 Direct CLI Execution 애플리케이션 - CLI와 완전히 동일한 방식"""
    
    def __init__(self):
        """애플리케이션 초기화"""
        # 환경 설정 로드
        self.env_config = get_env_config()
        
        # 메시지 처리
        self.message_processor = CLIMessageProcessor()
        self.chat_ui = ChatUI()
        self.terminal_ui = terminal_ui
        
        # 테마 매니저
        self.theme_manager = st.session_state.theme_manager
        
        self._initialize_session_state()
        
        # DirectExecutor를 세션 상태에서 관리
        self._setup_executor()
        
        # 디버그 로그
        log_debug("App initialized", {"config": self.env_config})
    
    def _initialize_session_state(self):
        """세션 상태 초기화"""
        defaults = {
            "executor_ready": False,
            "messages": [],
            "structured_messages": [],
            "terminal_messages": [],
            "current_model": None,
            "workflow_running": False,
            "show_controls": False,
            "initialization_in_progress": False,
            "initialization_error": None,
            # 에이전트 상태 추적 - CLI 방식으로 단순화
            "active_agent": None,
            "completed_agents": [],
            "current_step": 0,
            # UI 상태
            "keep_initial_ui": True,
            "agent_status_placeholders": {},
            "terminal_placeholder": None,
            # 이벤트 기록
            "event_history": [],
        }
        
        # 환경변수에서 디버그 모드 설정
        defaults["debug_mode"] = self.env_config.get("debug_mode", False)
        
        # 세션 상태 초기화
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def _setup_executor(self):
        """DirectExecutor 설정 및 세션 상태 연동"""
        # DirectExecutor를 세션 상태에 저장
        if "direct_executor" not in st.session_state:
            st.session_state.direct_executor = DirectExecutor()
            log_debug("DirectExecutor created and stored in session state")
        
        # 현재 인스턴스에서 사용할 executor 참조
        self.executor = st.session_state.direct_executor
        
        # 상태 동기화
        if self.executor.is_ready() != st.session_state.executor_ready:
            st.session_state.executor_ready = self.executor.is_ready()
            log_debug(f"Executor ready state synchronized: {st.session_state.executor_ready}")
    
    def reset_session(self):
        """세션 초기화"""
        log_debug("Resetting session")
        
        # 세션 상태 초기화
        reset_keys = [
            "executor_ready", "messages", "structured_messages", "terminal_messages",
            "workflow_running", "active_agent", "completed_agents", "current_step",
            "agent_status_placeholders", "terminal_placeholder", "event_history",
            "initialization_in_progress", "initialization_error", "current_model"
        ]
        
        for key in reset_keys:
            if key in st.session_state:
                if key in ["agent_status_placeholders"]:
                    st.session_state[key] = {}
                elif key in ["messages", "structured_messages", "terminal_messages", 
                           "completed_agents", "event_history"]:
                    st.session_state[key] = []
                elif key in ["current_step"]:
                    st.session_state[key] = 0
                else:
                    st.session_state[key] = False
        
        # DirectExecutor 재생성
        st.session_state.direct_executor = DirectExecutor()
        self.executor = st.session_state.direct_executor
        
        log_debug("Session reset completed")
        st.rerun()
    
    def toggle_controls(self):
        """컨트롤 패널 토글"""
        st.session_state.show_controls = not st.session_state.show_controls
        log_debug(f"Controls toggled: {st.session_state.show_controls}")
    
    def set_debug_mode(self, mode):
        """디버그 모드 설정"""
        st.session_state.debug_mode = mode
        log_debug(f"Debug mode set to: {mode}")
    
    def display_model_selection(self):
        """LLM 모델 선택 화면 - 안전한 에러 처리"""
        if not MODEL_SELECTION_AVAILABLE:
            st.error("Model selection not available. Please check CLI dependencies.")
            st.info(
                "To enable model selection, ensure the following modules are available:\n"
                "- src.utils.llm.models\n"
                "- All CLI dependencies\n\n"
                "You can still use the application with default settings."
            )
            return None
        
        st.markdown("### 🤖 Model Selection")
        st.markdown("Choose your AI model for red team operations")
        
        try:
            with st.spinner("Loading available models..."):
                models = list_available_models()
                ollama_info = check_ollama_connection()
            
            # 사용 가능한 모델만 필터링
            available_models = [m for m in models if m.get("api_key_available", False)]
            
            if not available_models:
                st.error("""
                **No models available**
                
                Setup required:
                - Set API keys in .env file (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
                - Or install Ollama from https://ollama.ai/
                """)
                return None
            
            # 모델 선택 UI
            model_options = []
            for model in available_models:
                display_text = f"{model['display_name']} ({model['provider']})"
                model_options.append(display_text)
            
            selected_index = st.selectbox(
                "Select Model:",
                range(len(model_options)),
                format_func=lambda x: model_options[x],
                key="model_selector"
            )
            
            selected_model = available_models[selected_index]
            
            # Ollama 상태 표시
            if ollama_info["connected"]:
                st.success(f"🦙 Ollama: Running ({ollama_info['count']} models available)")
            
            # 모델 정보 표시
            with st.expander("Model Details", expanded=False):
                st.json({
                    "Display Name": selected_model['display_name'],
                    "Provider": selected_model['provider'],
                    "Model Name": selected_model['model_name']
                })
            
            return selected_model
            
        except Exception as e:
            st.error(f"Error loading models: {str(e)}")
            log_debug(f"Model selection error: {str(e)}")
            return None
    
    async def initialize_executor_async(self, model_info=None):
        """비동기 실행기 초기화"""
        try:
            log_debug(f"Starting async executor initialization with model: {model_info}")
            
            if model_info:
                await self.executor.initialize_swarm(model_info)
                st.session_state.current_model = model_info
                log_debug(f"Executor initialized with model: {model_info['display_name']}")
            else:
                await self.executor.initialize_swarm()
                log_debug("Executor initialized with default settings")
            
            # 상태 업데이트
            st.session_state.executor_ready = True
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = None
            
            log_debug("Executor initialization completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize AI agents: {str(e)}"
            log_debug(f"Executor initialization failed: {error_msg}")
            
            # 에러 상태 업데이트
            st.session_state.executor_ready = False
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = error_msg
            
            return False
    
    def initialize_executor(self, model_info=None):
        """실행기 초기화 (동기 래퍼)"""
        if st.session_state.initialization_in_progress:
            st.warning("Initialization already in progress...")
            return
        
        try:
            # 초기화 시작
            st.session_state.initialization_in_progress = True
            st.session_state.initialization_error = None
            
            with st.status("Initializing AI agents...", expanded=True) as status:
                if model_info:
                    status.update(label=f"Setting up {model_info['display_name']}...")
                else:
                    status.update(label="Initializing with current settings...")
                
                # 비동기 초기화 실행
                result = asyncio.run(self.initialize_executor_async(model_info))
                
                if result:
                    status.update(label="✅ AI agents ready!", state="complete")
                    log_debug("Executor initialization completed")
                    time.sleep(1)
                    st.rerun()
                else:
                    status.update(label="❌ Initialization failed!", state="error")
                    if st.session_state.initialization_error:
                        st.error(st.session_state.initialization_error)
                    
        except Exception as e:
            error_msg = f"Initialization error: {str(e)}"
            st.session_state.initialization_error = error_msg
            st.session_state.initialization_in_progress = False
            st.error(error_msg)
            log_debug(f"Initialization exception: {error_msg}")
    
    def _extract_agent_name_from_namespace(self, namespace):
        """namespace에서 에이전트 이름 추출 - CLI와 동일한 로직"""
        if not namespace or len(namespace) == 0:
            return None
        
        namespace_str = namespace[0]
        if ':' in namespace_str:
            return namespace_str.split(':')[0]
        
        return namespace_str
    
    def _update_agent_status_from_events(self, agents_container):
        """이벤트 히스토리에서 에이전트 상태 업데이트 - CLI와 동일한 방식"""
        # 최근 이벤트에서 활성 에이전트 찾기
        active_agent = None
        for event in reversed(st.session_state.event_history):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    active_agent = agent_name.lower()
                    break
        
        # 상태 업데이트
        if active_agent and active_agent != st.session_state.active_agent:
            # 이전 활성 에이전트를 완료 목록에 추가
            if st.session_state.active_agent and st.session_state.active_agent not in st.session_state.completed_agents:
                st.session_state.completed_agents.append(st.session_state.active_agent)
            
            st.session_state.active_agent = active_agent
            log_debug(f"Active agent updated to: {active_agent}")
        
        # UI 상태 업데이트
        if st.session_state.get("keep_initial_ui", True) and (
            st.session_state.active_agent or st.session_state.completed_agents
        ):
            st.session_state.keep_initial_ui = False
        
        # 상태 표시 업데이트
        self.chat_ui.display_agent_status(
            agents_container,
            st.session_state.active_agent,
            None,  # active_stage 제거
            st.session_state.completed_agents
        )
    
    async def execute_workflow(self, user_input: str, chat_area, agents_container):
        """워크플로우 실행 - CLI와 완전히 동일한 방식"""
        # 상태 검증
        if not st.session_state.executor_ready:
            st.error("AI agents not ready. Please initialize first.")
            log_debug("Workflow execution rejected: executor not ready")
            return
        
        if not self.executor.is_ready():
            st.error("Executor state mismatch. Please reset and try again.")
            log_debug("Workflow execution rejected: executor state mismatch")
            return
        
        if st.session_state.workflow_running:
            st.warning("Another workflow is already running. Please wait.")
            return
        
        log_debug(f"Executing workflow: {user_input[:50]}...")
        
        # 사용자 메시지 추가
        user_message = self.message_processor._create_user_message(user_input)
        st.session_state.structured_messages.append(user_message)
        
        # UI에 사용자 메시지 표시
        with chat_area:
            self.chat_ui.display_user_message(user_input)
        
        # 워크플로우 실행 상태 설정
        st.session_state.workflow_running = True
        
        try:
            with st.status("🤖 AI agents working...", expanded=True) as status:
                event_count = 0
                agent_activity = {}  # 에이전트 활동 추적
                
                # CLI 워크플로우 직접 실행 - CLI와 완전히 동일
                async for event in self.executor.execute_workflow(user_input):
                    event_count += 1
                    st.session_state.event_history.append(event)
                    
                    try:
                        # 디버그 모드에서 이벤트 표시
                        if st.session_state.debug_mode:
                            with chat_area:
                                st.json(event)
                        
                        event_type = event.get("type", "")
                        
                        if event_type == "message":
                            # CLI 메시지를 프론트엔드 형식으로 변환 - CLI와 완전히 동일
                            frontend_message = self.message_processor.process_cli_event(event)
                            
                            # 중복 검사 - CLI와 동일한 로직
                            if not self.message_processor.is_duplicate_message(
                                frontend_message, st.session_state.structured_messages
                            ):
                                st.session_state.structured_messages.append(frontend_message)
                                
                                # 에이전트 활동 추적
                                agent_name = event.get("agent_name", "Unknown")
                                if agent_name not in agent_activity:
                                    agent_activity[agent_name] = 0
                                agent_activity[agent_name] += 1
                                
                                # 상태 업데이트
                                status.update(
                                    label=f"🤖 {agent_name} working... (Step {event_count})",
                                    state="running"
                                )
                                
                                # 메시지 표시 - CLI와 동일한 방식
                                with chat_area:
                                    self._display_message(frontend_message)
                                
                                # 터미널 메시지 처리 - CLI와 동일한 방식
                                if frontend_message.get("type") == "tool":
                                    st.session_state.terminal_messages.append(frontend_message)
                                    if st.session_state.terminal_placeholder:
                                        self.terminal_ui.process_structured_messages([frontend_message])
                        
                        elif event_type == "workflow_complete":
                            status.update(label="✅ Workflow completed!", state="complete")
                            log_debug(f"Workflow completed. Processed {event_count} events")
                        
                        elif event_type == "error":
                            error_msg = event.get("error", "Unknown error")
                            status.update(label=f"❌ Error: {error_msg}", state="error")
                            st.error(f"Workflow error: {error_msg}")
                            log_debug(f"Workflow error: {error_msg}")
                        
                        # 에이전트 상태 업데이트 - CLI와 동일한 방식
                        self._update_agent_status_from_events(agents_container)
                        
                    except Exception as e:
                        log_debug(f"Event processing error: {str(e)}")
                        if st.session_state.debug_mode:
                            st.error(f"Event processing error: {str(e)}")
                
                # 완료 후 요약 표시
                if agent_activity:
                    summary_text = f"Completed! Events: {event_count}, Active agents: {', '.join(agent_activity.keys())}"
                    status.update(label=f"✅ {summary_text}", state="complete")
        
        except Exception as e:
            st.error(f"Workflow execution error: {str(e)}")
            log_debug(f"Workflow execution error: {str(e)}")
        
        finally:
            st.session_state.workflow_running = False
    
    def _display_message(self, message):
        """메시지 표시 - CLI와 동일"""
        message_type = message.get("type", "")
        
        if message_type == "ai":
            self.chat_ui.display_agent_message(message, streaming=True)
        elif message_type == "tool":
            self.chat_ui.display_tool_message(message)
    
    def run(self):
        """애플리케이션 실행"""
        # 테마 상태 확인
        current_theme = self.theme_manager.get_current_theme()
        log_debug(f"Running Decepticon with theme: {current_theme}")
        
        st.logo(
            ICON_TEXT,
            icon_image=ICON,
            size="large",
            link="https://purplelab.framer.ai"
        )

        # 메인 제목
        st.title(":red[Decepticon]")
        
        # 환경 정보 표시 (디버그 모드)
        if st.session_state.debug_mode:
            with st.expander("🔧 Environment Info", expanded=False):
                st.json(self.env_config)
                
                # Executor 상태 정보
                if hasattr(self, 'executor'):
                    st.subheader("Executor State")
                    st.json(self.executor.get_state_dict())
        
        # 사이드바 설정
        sidebar = st.sidebar
        
        # 1. 타이틀
        title_container = sidebar.container()
        title_container.title("Agent Status")
        
        # 2. 에이전트 목록
        agents_container = sidebar.container()
        self.chat_ui.display_agent_status(
            agents_container,
            st.session_state.active_agent,
            None,  # active_stage 제거
            st.session_state.completed_agents
        )
        
        # 3. 구분선
        divider_container = sidebar.container()
        divider_container.divider()
        
        # 4. 컨트롤 패널
        control_container = sidebar.container()
        cols = control_container.columns(2)
        
        # 컨트롤 패널 버튼
        if cols[0].button("⚙️ Control", use_container_width=True):
            self.toggle_controls()
        
        # 테마 토글
        self.theme_manager.create_theme_toggle(cols[1])
        
        # 5. 컨트롤 패널 내용
        control_panel_container = sidebar.container()
        if st.session_state.show_controls:
            with control_panel_container.expander("Control", expanded=True):
                # 실행기 상태
                if st.session_state.executor_ready and self.executor.is_ready():
                    st.success("✅ AI Agents Ready")
                    if st.session_state.current_model:
                        st.info(f"Model: {st.session_state.current_model.get('display_name', 'Unknown')}")
                    if st.button("Reset Session"):
                        self.reset_session()
                elif st.session_state.initialization_in_progress:
                    st.info("🔄 Initializing...")
                elif st.session_state.initialization_error:
                    st.error(f"❌ Init Error: {st.session_state.initialization_error}")
                else:
                    st.warning("⚠️ AI Agents Not Ready")
                
                # 디버그 모드
                debug_mode = st.checkbox("Debug Mode", value=st.session_state.debug_mode)
                self.set_debug_mode(debug_mode)
                
                # 워크플로우 상태
                if st.session_state.workflow_running:
                    st.info("🔄 Workflow Running...")
                
                # 통계
                st.subheader("Statistics")
                st.text(f"Messages: {len(st.session_state.structured_messages)}")
                st.text(f"Events: {len(st.session_state.event_history)}")
                st.text(f"Step: {st.session_state.current_step}")
        
        # 레이아웃: 두 개의 열로 분할 (채팅과 터미널)
        chat_column, terminal_column = st.columns([2, 1])
        
        # 터미널 영역 초기화
        with terminal_column:
            st.session_state.terminal_placeholder = self.terminal_ui.create_terminal(terminal_column)
            
            # 저장된 터미널 메시지 복원
            if st.session_state.terminal_messages:
                self.terminal_ui.process_structured_messages(st.session_state.terminal_messages)
        
        # 채팅 영역 처리
        with chat_column:
            # 실행기 초기화 확인
            if not st.session_state.executor_ready:
                if st.session_state.initialization_in_progress:
                    st.info("🔄 Initializing AI agents... Please wait.")
                    return
                
                if st.session_state.initialization_error:
                    st.error(f"❌ Initialization failed: {st.session_state.initialization_error}")
                    if st.button("🔄 Retry Initialization"):
                        st.session_state.initialization_error = None
                        st.rerun()
                
                st.info("🤖 Initialize AI agents to start red team operations")
                
                # 모델 선택
                selected_model = self.display_model_selection()
                
                if selected_model and st.button("🚀 Initialize AI Agents", type="primary"):
                    self.initialize_executor(selected_model)
                return
            
            # 채팅 영역
            chat_height = self.env_config.get("chat_height", 700)
            chat_container = st.container(height=chat_height, border=False)
            
            with chat_container:
                # 메시지 표시 영역
                messages_area = st.container()
                
                # 입력창 영역
                input_container = st.container()
                
                # 기존 메시지 표시
                with messages_area:
                    if st.session_state.debug_mode:
                        st.warning("Debug Mode: Event data will be displayed during processing")
                    
                    # 저장된 구조화 메시지 표시
                    if not st.session_state.workflow_running:
                        self.chat_ui.display_messages(st.session_state.structured_messages, messages_area)
                
                # 사용자 입력 처리
                with input_container:
                    user_input = st.chat_input("Type your red team request here...")
                    
                    if user_input and not st.session_state.workflow_running:
                        asyncio.run(self.execute_workflow(user_input, messages_area, agents_container))


if __name__ == "__main__":
    app = DecepticonApp()
    app.run()
