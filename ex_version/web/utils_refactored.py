# frontend/web/utils.py - 리팩토링 버전
"""
핵심 유틸리티 함수만 남김 - 불필요한 래퍼 함수 제거
"""
from dotenv import load_dotenv
import streamlit as st
import os
import sys
from typing import Dict, Any, Optional
from web.core.app_state import get_app_state_manager

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# 상수
ICON = "assets/logo.png"
ICON_TEXT = "assets/logo_text1.png"


def setup_page_config(page_title: str = "Decepticon"):
    """페이지 기본 설정"""
    st.set_page_config(
        page_title=page_title,
        page_icon=ICON,
        layout="wide",
    )


def setup_theme():
    """테마 설정 초기화"""
    from web.theme_manager import ThemeManager
    
    if "theme_manager" not in st.session_state:
        st.session_state.theme_manager = ThemeManager()
    
    theme_manager = st.session_state.theme_manager
    theme_manager.apply_theme()
    return theme_manager


def display_current_model_info():
    """현재 모델 정보 표시"""
    if not st.session_state.get('current_model'):
        return
        
    model = st.session_state.current_model
    model_name = model.get('display_name', 'Unknown Model')
    provider = model.get('provider', 'Unknown')
    
    # 다크/라이트 모드에 따른 색상
    is_dark = st.session_state.get('dark_mode', True)
    
    colors = {
        'bg': "#1a1a1a" if is_dark else "#f8f9fa",
        'border': "#333333" if is_dark else "#e9ecef", 
        'text': "#ffffff" if is_dark else "#212529",
        'subtitle': "#888888" if is_dark else "#6c757d",
        'icon': "#4a9eff" if is_dark else "#0d6efd"
    }
    
    st.markdown(f"""
    <div style="
        background: {colors['bg']};
        border: 1px solid {colors['border']};
        border-radius: 8px;
        padding: 12px 16px;
        margin: 8px 0;
        display: flex;
        align-items: center;
        gap: 12px;
    ">
        <div style="color: {colors['icon']}; font-size: 18px;">🤖</div>
        <div style="flex: 1;">
            <div style="color: {colors['text']}; font-weight: 600; font-size: 14px;">
                {model_name}
            </div>
            <div style="color: {colors['subtitle']}; font-size: 12px; margin-top: 2px;">
                {provider}
            </div>
        </div>
        <div style="width: 8px; height: 8px; background: #10b981; border-radius: 50%;"></div>
    </div>
    """, unsafe_allow_html=True)


def display_session_stats():
    """세션 통계 표시"""
    app_state = get_app_state_manager()
    stats = app_state.get_session_stats()
    
    with st.expander("📊 Session Stats", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Messages", stats["messages_count"])
            st.metric("Events", stats["events_count"])
        with col2:
            st.metric("Steps", stats["steps_count"])
            st.metric("Time", f"{stats['elapsed_time']}s")


def display_debug_info():
    """디버그 정보 표시"""
    if not st.session_state.get('debug_mode'):
        return
    
    app_state = get_app_state_manager()
    debug_info = app_state.get_debug_info()
    
    with st.expander("🔍 Debug Info", expanded=False):
        st.markdown("**Session Info:**")
        session_info = {
            "user_id": debug_info["user_id"],
            "thread_id": debug_info["thread_id"][:8] + "..." if len(debug_info["thread_id"]) > 8 else debug_info["thread_id"],
        }
        st.json(session_info)


def check_model_required(redirect_page: str = "streamlit_app.py") -> bool:
    """모델 선택 여부 확인"""
    if not st.session_state.get('current_model'):
        st.warning("⚠️ Please select a model first")
        if st.button("Go to Model Selection", type="primary"):
            st.switch_page(redirect_page)
        return False
    return True


def get_env_config() -> Dict[str, Any]:
    """환경 설정 로드"""
    load_dotenv()
    
    return {
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "theme": os.getenv("THEME", "dark"),
        "docker_container": os.getenv("DOCKER_CONTAINER", "decepticon-kali"),
        "chat_height": int(os.getenv("CHAT_HEIGHT", "700"))
    }


def validate_environment() -> Dict[str, Any]:
    """환경 설정 검증"""
    config = get_env_config()
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config": config
    }
    
    # API 키 확인
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]
    available_keys = [key for key in api_keys if os.getenv(key) and os.getenv(key) != "your-api-key"]
    
    if not available_keys:
        validation_result["errors"].append("No API keys configured")
        validation_result["valid"] = False
    else:
        validation_result["warnings"].append(f"Available API keys: {', '.join(available_keys)}")
    
    # CLI 모듈 확인
    try:
        from src.graphs.swarm import create_dynamic_swarm
        from src.utils.message import extract_message_content
    except ImportError as e:
        validation_result["errors"].append(f"CLI modules not available: {str(e)}")
        validation_result["valid"] = False
    
    return validation_result
