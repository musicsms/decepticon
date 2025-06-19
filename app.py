import streamlit as st
import time
import os
import asyncio
import uuid
from datetime import datetime
from dotenv import load_dotenv
import hashlib

# .env 파일 로드
load_dotenv()

# persistence 설정 추가
from src.utils.memory import (
    get_persistence_status, 
    get_debug_info, 
    create_thread_config,
    create_memory_namespace
)

# 로깅 시스템 사용 - 재현에 필요한 정보만
from src.utils.logging.logger import get_logger
from src.utils.logging.replay import get_replay_system

ICON = "assets\logo.png"
ICON_TEXT = "assets\logo_text1.png"

# Streamlit 페이지 설정 
st.set_page_config(
    page_title="Decepticon",
    page_icon=ICON,
    layout="wide",
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
from frontend.executor import DirectExecutor
from frontend.message import CLIMessageProcessor
from frontend.chat_ui import ChatUI
from frontend.terminal_ui import TerminalUI
from frontend.model import ModelSelectionUI
from frontend.components.log_manager import LogManagerUI
from frontend.components.chat_replay import ReplayManager

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
    """Decepticon 애플리케이션 - 간소화된 로그 시스템"""
    
    def __init__(self):
        """애플리케이션 초기화"""
        self.env_config = get_env_config()
        self.message_processor = CLIMessageProcessor()
        self.chat_ui = ChatUI()
        self.terminal_ui = terminal_ui
        self.theme_manager = st.session_state.theme_manager
        
        # 모델 선택 UI 초기화
        self.model_ui = ModelSelectionUI(self.theme_manager)
        
        # 로그 관리 UI 초기화
        self.log_manager_ui = LogManagerUI()
        
        # 재생 기능 초기화
        self.chat_replay = ReplayManager()
        
        self._initialize_session_state()
        self._initialize_user_session()
        self._setup_executor()
        
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
            "active_agent": None,
            "completed_agents": [],
            "current_step": 0,
            "keep_initial_ui": True,
            "agent_status_placeholders": {},
            "terminal_placeholder": None,
            "event_history": [],
            "app_stage": "model_selection",  # 앱 단계: model_selection, main_app, log_manager
        }
        
        defaults["debug_mode"] = self.env_config.get("debug_mode", False)
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
                log_debug(f"Initialized session state: {key} = {default_value}")
    
    def _initialize_user_session(self):
        """사용자 세션 및 thread config 초기화"""
        # 사용자 ID 생성 (브라우저 기반)
        if "user_id" not in st.session_state:
            # 브라우저 세션 기반 고유 ID 생성
            browser_info = f"{st.session_state.get('_session_id', '')}{datetime.now().strftime('%Y%m%d')}"
            user_hash = hashlib.md5(browser_info.encode()).hexdigest()[:8]
            st.session_state.user_id = f"user_{user_hash}"
            log_debug(f"Generated user ID: {st.session_state.user_id}")
        
        # Thread configuration 생성
        if "thread_config" not in st.session_state:
            st.session_state.thread_config = create_thread_config(
                user_id=st.session_state.user_id,
                conversation_id=None  # 기본 대화
            )
            log_debug(f"Created thread config: {st.session_state.thread_config}")
        
        # 메모리 네임스페이스 생성
        if "memory_namespace" not in st.session_state:
            st.session_state.memory_namespace = create_memory_namespace(
                user_id=st.session_state.user_id,
                namespace_type="memories"
            )
            log_debug(f"Created memory namespace: {st.session_state.memory_namespace}")
        
        # 로깅 시스템 초기화 - 재현에 필요한 정보만
        if "logger" not in st.session_state:
            st.session_state.logger = get_logger()
            st.session_state.replay_system = get_replay_system()
            log_debug("Minimal logger initialized")
    
    def _setup_executor(self):
        """DirectExecutor 설정"""
        if "direct_executor" not in st.session_state:
            st.session_state.direct_executor = DirectExecutor()
            log_debug("DirectExecutor created and stored in session state")
        
        self.executor = st.session_state.direct_executor
        
        if self.executor.is_ready() != st.session_state.executor_ready:
            st.session_state.executor_ready = self.executor.is_ready()
            log_debug(f"Executor ready state synchronized: {st.session_state.executor_ready}")
    
    def reset_session(self):
        """세션 초기화 - 터미널 UI 완전 초기화 포함"""
        log_debug("Resetting session")
        
        # 현재 로그 세션 종료
        if hasattr(st.session_state, 'logger') and st.session_state.logger.current_session:
            st.session_state.logger.end_session()
        
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
                    st.session_state[key] = False if key != "current_model" else None
        
        # 🔥 터미널 UI 완전 초기화 추가
        # 터미널 히스토리 초기화
        st.session_state.terminal_history = []
        
        # 터미널 플레이스홀더 초기화
        st.session_state.terminal_placeholder = None
        
        # TerminalUI 인스턴스의 상태 초기화
        if hasattr(self, 'terminal_ui'):
            self.terminal_ui.clear_terminal()
            # processed_messages도 초기화
            self.terminal_ui.processed_messages = set()
            self.terminal_ui.terminal_history = []
        
        # 재현 관련 상태 초기화 (혹시 남아있을 수 있는 재현 모드 해제)
        for replay_key in ["replay_mode", "replay_session_id", "replay_completed"]:
            if replay_key in st.session_state:
                st.session_state.pop(replay_key, None)
        
        # 모델 선택 상태 초기화
        self.model_ui.reset_selection()
        
        # 모델 선택 단계로 돌아가기
        st.session_state.app_stage = "model_selection"
        
        # DirectExecutor 재생성
        st.session_state.direct_executor = DirectExecutor()
        self.executor = st.session_state.direct_executor
        
        log_debug("Session reset completed - including terminal UI cleanup")
        st.rerun()
    
    async def initialize_executor_async(self, model_info=None):
        """비동기 실행기 초기화"""
        try:
            log_debug(f"Starting async executor initialization with model: {model_info}")
            
            # 최소한의 로깅 세션 시작 - 모델 정보 포함
            model_display_name = model_info.get('display_name', 'Unknown Model') if model_info else 'Default Model'
            session_id = st.session_state.minimal_logger.start_session(model_display_name)
            st.session_state.logging_session_id = session_id
            log_debug(f"Started logging session: {session_id} with model: {model_display_name}")
            
            if model_info:
                await self.executor.initialize_swarm(model_info)
                st.session_state.current_model = model_info
                log_debug(f"Executor initialized with model: {model_info['display_name']}")
            else:
                await self.executor.initialize_swarm()
                log_debug("Executor initialized with default settings")
            
            st.session_state.executor_ready = True
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = None
            
            log_debug("Executor initialization completed successfully")
            return True
            
        except Exception as e:
            error_msg = f"Failed to initialize AI agents: {str(e)}"
            log_debug(f"Executor initialization failed: {error_msg}")
            
            st.session_state.executor_ready = False
            st.session_state.initialization_in_progress = False
            st.session_state.initialization_error = error_msg
            
            return False
    
    def toggle_controls(self):
        """컨트롤 패널 토글"""
        st.session_state.show_controls = not st.session_state.show_controls
        log_debug(f"Controls toggled: {st.session_state.show_controls}")
    
    def set_debug_mode(self, mode):
        """디버그 모드 설정"""
        st.session_state.debug_mode = mode
        log_debug(f"Debug mode set to: {mode}")
    
    def _update_agent_status_from_events(self, agents_container):
        """이벤트 히스토리에서 에이전트 상태 업데이트"""
        active_agent = None
        for event in reversed(st.session_state.event_history):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    active_agent = agent_name.lower()
                    break
        
        if active_agent and active_agent != st.session_state.active_agent:
            if st.session_state.active_agent and st.session_state.active_agent not in st.session_state.completed_agents:
                st.session_state.completed_agents.append(st.session_state.active_agent)
            
            st.session_state.active_agent = active_agent
            log_debug(f"Active agent updated to: {active_agent}")
        
        if st.session_state.get("keep_initial_ui", True) and (
            st.session_state.active_agent or st.session_state.completed_agents
        ):
            st.session_state.keep_initial_ui = False
        
        self.chat_ui.display_agent_status(
            agents_container,
            st.session_state.active_agent,
            None,
            st.session_state.completed_agents
        )
    
    async def execute_workflow(self, user_input: str, chat_area, agents_container):
        """워크플로우 실행 - 간소화된 로깅"""
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
        
        # 최소한의 로깅 - 재현에 필요한 정보만
        st.session_state.minimal_logger.log_user_input(user_input)
        
        user_message = self.message_processor._create_user_message(user_input)
        st.session_state.structured_messages.append(user_message)
        
        with chat_area:
            self.chat_ui.display_user_message(user_input)
        
        st.session_state.workflow_running = True
        
        try:
            with st.status("Processing...", expanded=True) as status:
                event_count = 0
                agent_activity = {}
                
                async for event in self.executor.execute_workflow(
                    user_input,
                    config=st.session_state.thread_config
                ):
                    event_count += 1
                    st.session_state.event_history.append(event)
                    
                    try:
                        if st.session_state.debug_mode:
                            with chat_area:
                                st.json(event)
                        
                        event_type = event.get("type", "")
                        
                        if event_type == "message":
                            frontend_message = self.message_processor.process_cli_event(event)
                            
                            if not self.message_processor.is_duplicate_message(
                                frontend_message, st.session_state.structured_messages
                            ):
                                st.session_state.structured_messages.append(frontend_message)
                                
                                agent_name = event.get("agent_name", "Unknown")
                                message_type = event.get("message_type", "unknown")
                                content = event.get("content", "")
                                
                                # 최소한의 로깅 - 재현에 필요한 정보만
                                if message_type == "ai":
                                    st.session_state.minimal_logger.log_agent_response(
                                        agent_name=agent_name,
                                        content=content
                                    )
                                elif message_type == "tool":
                                    tool_name = event.get("tool_name", "Unknown Tool")
                                    if "command" in event:  # 도구 명령
                                        st.session_state.minimal_logger.log_tool_command(
                                            tool_name=tool_name,
                                            command=event.get("command", content)
                                        )
                                    else:  # 도구 출력
                                        st.session_state.minimal_logger.log_tool_output(
                                            tool_name=tool_name,
                                            output=content
                                        )
                                
                                if agent_name not in agent_activity:
                                    agent_activity[agent_name] = 0
                                agent_activity[agent_name] += 1
                                
                                status.update(
                                    label=f"Processing...",
                                    state="running"
                                )
                                
                                with chat_area:
                                    self._display_message(frontend_message)
                                
                                if frontend_message.get("type") == "tool":
                                    st.session_state.terminal_messages.append(frontend_message)
                                    if st.session_state.terminal_placeholder:
                                        self.terminal_ui.process_structured_messages([frontend_message])
                        
                        elif event_type == "workflow_complete":
                            status.update(label="Processing complete!", state="complete")
                            log_debug(f"Workflow completed. Processed {event_count} events")
                        
                        elif event_type == "error":
                            error_msg = event.get("error", "Unknown error")
                            status.update(label=f"Error: {error_msg}", state="error")
                            st.error(f"Workflow error: {error_msg}")
                            log_debug(f"Workflow error: {error_msg}")
                        
                        self._update_agent_status_from_events(agents_container)
                        
                    except Exception as e:
                        log_debug(f"Event processing error: {str(e)}")
                        if st.session_state.debug_mode:
                            st.error(f"Event processing error: {str(e)}")
                
                if agent_activity:
                    summary_text = f"Completed! Events: {event_count}, Active agents: {', '.join(agent_activity.keys())}"
                    status.update(label=f"{summary_text}", state="complete")
        
        except Exception as e:
            st.error(f"Workflow execution error: {str(e)}")
            log_debug(f"Workflow execution error: {str(e)}")
        
        finally:
            st.session_state.workflow_running = False
            # 세션 자동 저장
            st.session_state.minimal_logger.save_session()
    
    def _display_message(self, message):
        """메시지 표시"""
        message_type = message.get("type", "")
        
        if message_type == "ai":
            self.chat_ui.display_agent_message(message, streaming=True)
        elif message_type == "tool":
            self.chat_ui.display_tool_message(message)
    



    def run_model_selection(self):
        """모델 선택 단계 실행"""
        st.logo(
            ICON_TEXT,
            icon_image=ICON,
            size="large",
            link="https://purplelab.framer.ai"
        )
        
        selected_model = self.model_ui.display_model_selection_ui()
        
        if selected_model:
            with st.spinner(f"Initializing {selected_model['display_name']}..."):
                async def init_and_proceed():
                    try:
                        success = await self.initialize_executor_async(selected_model)
                        
                        if success:
                            st.session_state.app_stage = "main_app"
                            st.success(f"{selected_model['display_name']} initialized successfully!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to initialize {selected_model['display_name']}")
                            if st.session_state.initialization_error:
                                st.error(st.session_state.initialization_error)
                    
                    except Exception as e:
                        st.error(f"Initialization error: {str(e)}")
                
                asyncio.run(init_and_proceed())




    def run_main_app(self):
        """메인 애플리케이션 실행"""
        current_theme = self.theme_manager.get_current_theme()
        log_debug(f"Running Decepticon with theme: {current_theme}")

        st.logo(
            ICON_TEXT,
            icon_image=ICON,
            size="large",
            link="https://purplelab.framer.ai"
        )

        st.title(":red[Decepticon]")

        # 사이드바 설정
        sidebar = st.sidebar

        title_container = sidebar.container()
        title_container.title("Agent Status")

        agents_container = sidebar.container()
        self.chat_ui.display_agent_status(
            agents_container,
            st.session_state.active_agent,
            None,
            st.session_state.completed_agents
        )

        divider_container = sidebar.container()
        divider_container.divider()

        control_container = sidebar.container()
        cols = control_container.columns(2)

        if cols[0].button("Control", use_container_width=True):
            self.toggle_controls()

        self.theme_manager.create_theme_toggle(cols[1])

        control_panel_container = sidebar.container()
        if st.session_state.show_controls:
            with control_panel_container.expander("Control", expanded=True):
                # AI Agent 상태
                if st.session_state.executor_ready and self.executor.is_ready():
                    st.success("✅ AI Agents Ready")
                elif st.session_state.initialization_in_progress:
                    st.info("🛠️ Initializing...")
                elif st.session_state.initialization_error:
                    st.error(f"❌ Init Error: {st.session_state.initialization_error}")
                else:
                    st.warning("⚠️ AI Agents Not Ready")

                # 모델 정보
                if st.session_state.current_model:
                    st.info(f"🧠 Model: {st.session_state.current_model.get('display_name', 'Unknown')}")

                # Control 버튼
                if st.button("🔁 Change Model"):
                    st.session_state.app_stage = "model_selection"
                    st.rerun()

                if st.button("🔄 Reset Session"):
                    self.reset_session()

                if st.button("📊 View Logs"):
                    st.session_state.app_stage = "log_manager"
                    st.rerun()

                # Debug 모드
                debug_mode = st.checkbox("🐞 Debug Mode", value=st.session_state.debug_mode)
                self.set_debug_mode(debug_mode)

                # 통계 정보
                st.divider()
                st.subheader("📈 Statistics")
                st.text(f"Messages: {len(st.session_state.structured_messages)}")
                st.text(f"Events: {len(st.session_state.event_history)}")
                st.text(f"Step: {st.session_state.current_step}")

                # Debug 모드일 때 세션 정보
                if st.session_state.debug_mode:
                    st.subheader("🗂️ Session Info")
                    session_info = {
                        "user_id": st.session_state.get("user_id", "Not set"),
                        "thread_config": st.session_state.get("thread_config", {}),
                    }
                    st.json(session_info)

                    st.subheader("🧾 Logging Info")
                    if hasattr(st.session_state, 'logger'):
                        current_session = st.session_state.logger.current_session
                        if current_session:
                            logging_info = {
                                "session_id": current_session.session_id,
                                "events_count": len(current_session.events),
                            }
                            st.json(logging_info)
                        else:
                            st.text("No active logging session")
                    else:
                        st.text("Logger not initialized")

        # 레이아웃: 두 개의 열로 분할 (채팅과 터미널)
        chat_column, terminal_column = st.columns([2, 1])

        # 터미널 영역 초기화
        with terminal_column:
            # 터미널 플레이스홀더가 None인 경우 (새 채팅 시작 후 또는 Reset Session 후) 터미널 히스토리 클리어
            if st.session_state.terminal_placeholder is None:
                # 터미널 히스토리 초기화 보장
                if "terminal_history" not in st.session_state:
                    st.session_state.terminal_history = []
                # 터미널 UI 청소
                self.terminal_ui.clear_terminal()
                
            st.session_state.terminal_placeholder = self.terminal_ui.create_terminal(terminal_column)

            # 저장된 터미널 메시지 복원 (재현 모드에서도 올바르게 동작)
            if st.session_state.terminal_messages:
                self.terminal_ui.process_structured_messages(st.session_state.terminal_messages)

        # 채팅 영역 처리
        with chat_column:
            chat_height = self.env_config.get("chat_height", 700)
            chat_container = st.container(height=chat_height, border=False)

            with chat_container:
                # 메시지 표시 영역
                messages_area = st.container()

                # 재생 모드 처리
                if self.chat_replay.is_replay_mode():
                    log_debug("Replay mode detected - starting replay")
                    try:
                        replay_handled = self.chat_replay.handle_replay_in_main_app(
                            messages_area, agents_container, self.chat_ui
                        )
                        if replay_handled:
                            log_debug("Replay completed - updating terminal UI with all tool messages")
                            # 재현 완료 후 모든 터미널 메시지를 한 번에 업데이트
                            if st.session_state.terminal_messages and st.session_state.terminal_placeholder:
                                # 기존 터미널 클리어 후 새 메시지들 추가
                                self.terminal_ui.clear_terminal()
                                self.terminal_ui.process_structured_messages(st.session_state.terminal_messages)
                        else:
                            # 재생 실패 시 에러 처리
                            st.error("Failed to start replay.")
                    except Exception as e:
                        st.error(f"Replay error: {e}")
                        log_debug(f"Replay error: {e}")
                        # 에러 발생 시 재생 모드 해제
                        st.session_state.pop("replay_mode", None)
                        st.session_state.pop("replay_session_id", None)

                # 기존 메시지 표시 (재생된 메시지 포함)
                with messages_area:
                    if st.session_state.debug_mode:
                        st.warning("Debug Mode: Event data will be displayed during processing")

                    if not st.session_state.workflow_running:
                        self.chat_ui.display_messages(st.session_state.structured_messages, messages_area)

            # 사용자 입력 처리 (chat_container 밖에서) - 디버깅 강화
            replay_mode = self.chat_replay.is_replay_mode()
            replay_completed = st.session_state.get("replay_completed", False)
            
            # 디버깅용 상태 표시
            if st.session_state.get("debug_mode", False):
                st.write(f"DEBUG - replay_mode: {replay_mode}, replay_completed: {replay_completed}")
            
            log_debug(f"Input container logic - replay_mode: {replay_mode}, replay_completed: {replay_completed}")
            
            if not replay_mode and not replay_completed:
                # 정상 모드 - 사용자 입력창 표시
                log_debug("Showing normal input container")
                user_input = st.chat_input("Type your red team request here...")

                if user_input and not st.session_state.workflow_running:
                    asyncio.run(self.execute_workflow(user_input, messages_area, agents_container))
                    
            elif not replay_mode and replay_completed:
                # 재현 완료 후 - 버튼 표시 (chat UI 밖 아래)
                log_debug("Showing replay completed button outside chat container")
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("🔄 Start New Chat", use_container_width=True, type="primary", key="start_new_chat_btn"):
                        # 재현 모드 해제하고 완전히 새로운 채팅 세션 시작
                        log_debug("Start New Chat button clicked - creating completely new chat session")
                        
                        # 재현 관련 플래그 제거
                        st.session_state.pop("replay_mode", None)
                        st.session_state.pop("replay_session_id", None)
                        st.session_state.pop("replay_completed", None)
                        
                        # 메시지 및 채팅 관련 상태 초기화
                        st.session_state.structured_messages = []
                        st.session_state.terminal_messages = []
                        st.session_state.event_history = []
                        st.session_state.active_agent = None
                        st.session_state.completed_agents = []
                        st.session_state.current_step = 0
                        st.session_state.workflow_running = False
                        st.session_state.keep_initial_ui = True
                        
                        # 에이전트 상태 플레이스홀더 초기화
                        st.session_state.agent_status_placeholders = {}
                        
                        # 터미널 플레이스홀더도 초기화 (중요!)
                        st.session_state.terminal_placeholder = None
                        
                        # 터미널 히스토리도 완전 초기화
                        st.session_state.terminal_history = []
                        
                        # 터미널 UI 초기화 (기존 터미널 컨텐츠 클리어)
                        if hasattr(self, 'terminal_ui'):
                            self.terminal_ui.clear_terminal()
                        
                        # 🔥 핵심: Thread Config 완전 초기화 (새로운 conversation_id로)
                        new_conversation_id = str(uuid.uuid4())  # 새로운 고유 ID 생성
                        st.session_state.thread_config = create_thread_config(
                            user_id=st.session_state.user_id,
                            conversation_id=new_conversation_id
                        )
                        log_debug(f"Created new thread config with conversation_id: {new_conversation_id}")
                        log_debug(f"New thread_id: {st.session_state.thread_config['configurable']['thread_id']}")
                        
                        # DirectExecutor 재초기화 (새로운 thread_id로)
                        st.session_state.direct_executor = DirectExecutor()
                        self.executor = st.session_state.direct_executor
                        
                        # Executor를 현재 모델로 재초기화 (새로운 thread_config 사용)
                        current_model = st.session_state.get('current_model')
                        if current_model:
                            asyncio.run(self.executor.initialize_swarm(
                                model_info=current_model,
                                thread_config=st.session_state.thread_config  # 새로운 thread_config 전달
                            ))
                            st.session_state.executor_ready = True
                            log_debug(f"DirectExecutor reinitialized with new thread_config and model: {current_model['display_name']}")
                        
                        # 현재 로깅 세션 종료 및 새 세션 시작 - 모델 정보 포함
                        if hasattr(st.session_state, 'logger') and st.session_state.logger.current_session:
                            st.session_state.logger.end_session()
                        
                        # 현재 모델 정보 가져오기
                        model_display_name = current_model.get('display_name', 'Unknown Model') if current_model else 'No Model'
                        
                        session_id = st.session_state.logger.start_session(model_display_name)
                        st.session_state.logging_session_id = session_id
                        log_debug(f"Started new logging session: {session_id} with model: {model_display_name}")
                        
                        st.success("New chat session started! Your model is ready with fresh memory.")
                        st.rerun()
            else:
                # 재현 진행 중 - 빈 공간 유지
                log_debug("Replay in progress - showing empty container")
                if replay_mode:
                    st.info("🎞️ Replay in progress...")
                else:
                    st.empty()

    def run_log_manager(self):
        """로그 관리 화면 실행"""
        self.log_manager_ui.display_log_page()
    
    def run(self):
        """애플리케이션 실행 - 단계별 라우팅"""
        # 재현 모드일 때 강제로 메인 앱으로 이동 (로그 관리자에서 벗어나기)
        if st.session_state.get("replay_mode", False):
            if st.session_state.app_stage != "main_app":
                print(f"Replay mode detected, switching from {st.session_state.app_stage} to main_app")
                st.session_state.app_stage = "main_app"
                st.rerun()
        
        # 현재 앱 단계에 따라 다른 화면 표시
        if st.session_state.app_stage == "model_selection":
            self.run_model_selection()
        elif st.session_state.app_stage == "main_app":
            self.run_main_app()
        elif st.session_state.app_stage == "log_manager":
            self.run_log_manager()
        else:
            # 기본값: 모델 선택
            st.session_state.app_stage = "model_selection"
            st.rerun()


if __name__ == "__main__":
    app = DecepticonApp()
    app.run()
