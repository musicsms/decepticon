import streamlit as st
import time
import asyncio
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기존 DecepticonApp import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.theme_manager import ThemeManager
from frontend.model import ModelSelectionUI
from frontend.executor import DirectExecutor
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


# 테마 관리자 초기화
if "theme_manager" not in st.session_state:
    st.session_state.theme_manager = ThemeManager()

theme_manager = st.session_state.theme_manager
theme_manager.apply_theme()

# DecepticonApp 클래스를 위한 기본 함수들
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

# 모델 선택 UI 초기화
if "model_ui" not in st.session_state:
    st.session_state.model_ui = ModelSelectionUI(theme_manager)

model_ui = st.session_state.model_ui

# 비동기 실행기 초기화 함수 (기존 app.py에서 가져옴)
async def initialize_executor_async(model_info=None):
    """비동기 실행기 초기화 - 속도 최적화"""
    try:
        log_debug(f"Starting optimized async executor initialization with model: {model_info}")
        
        # DirectExecutor 생성
        if "direct_executor" not in st.session_state:
            st.session_state.direct_executor = DirectExecutor()
        
        executor = st.session_state.direct_executor
        
        # 로거 초기화 확인 (안전 장치)
        if "logger" not in st.session_state or st.session_state.logger is None:
            st.session_state.logger = get_logger()
            st.session_state.replay_system = get_replay_system()
            log_debug("Logger initialized during executor setup")
        
        # 최소한의 로깅 세션 시작 - 모델 정보 포함
        model_display_name = model_info.get('display_name', 'Unknown Model') if model_info else 'Default Model'
        session_id = st.session_state.logger.start_session(model_display_name)
        st.session_state.logging_session_id = session_id
        log_debug(f"Started logging session: {session_id} with model: {model_display_name}")
        
        # 대기 시간 없이 바로 초기화 시작
        if model_info:
            await executor.initialize_swarm(model_info)
            st.session_state.current_model = model_info
            log_debug(f"Executor initialized with model: {model_info['display_name']}")
        else:
            await executor.initialize_swarm()
            log_debug("Executor initialized with default settings")
        
        st.session_state.executor_ready = True
        st.session_state.initialization_in_progress = False
        st.session_state.initialization_error = None
        
        log_debug("Optimized executor initialization completed successfully")
        return True
        
    except Exception as e:
        error_msg = f"Failed to initialize AI agents: {str(e)}"
        log_debug(f"Executor initialization failed: {error_msg}")
        
        st.session_state.executor_ready = False
        st.session_state.initialization_in_progress = False
        st.session_state.initialization_error = error_msg
        
        return False

# 기존 run_model_selection 메서드 내용을 여기에 구현
st.logo(
    ICON_TEXT,
    icon_image=ICON,
    size="large",
    link="https://purplelab.framer.ai"
)

selected_model = model_ui.display_model_selection_ui()

if selected_model:
    # col2 레이아웃에 맞춘 실제 초기화 진행
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.spinner(f"Initializing {selected_model['display_name']} for red team operations..."):
            async def init_and_proceed():
                try:
                    success = await initialize_executor_async(selected_model)
                    
                    if success:
                        st.success(f"{selected_model['display_name']} initialized successfully!")
                        time.sleep(0.8)  # 짧은 대기 시간
                        st.switch_page("pages/main.py")
                    else:
                        # 실패 시 에러 메시지
                        st.error(f"Failed to initialize {selected_model['display_name']}")
                        if st.session_state.get('initialization_error'):
                            st.error(st.session_state.initialization_error)
                
                except Exception as e:
                    st.error(f"Initialization error: {str(e)}")
            
            asyncio.run(init_and_proceed())