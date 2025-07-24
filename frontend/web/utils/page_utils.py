"""
페이지 공통 유틸리티 모듈
- 페이지 설정 및 레이아웃
- 공통 UI 컴포넌트
- 네비게이션 헬퍼
"""

import streamlit as st
import os
import sys
from typing import Optional, Dict, Any

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from web.theme_manager import ThemeManager
from web.core.app_state import get_app_state_manager

# 아이콘 및 이미지 경로
ICON = "assets/logo.png"
ICON_TEXT = "assets/logo_text1.png"


def setup_page_config(page_title: str = "Decepticon", page_icon: str = "🤖"):
    """페이지 기본 설정"""
    st.set_page_config(
        page_title=page_title,
        page_icon=ICON,
        layout="wide",
    )


def setup_theme():
    """테마 설정 초기화"""
    # 테마 관리자 초기화
    if "theme_manager" not in st.session_state:
        st.session_state.theme_manager = ThemeManager()
    
    # 테마 적용
    theme_manager = st.session_state.theme_manager
    theme_manager.apply_theme()
    
    return theme_manager


def display_logo(link: str = "https://purplelab.framer.ai"):
    """로고 표시"""
    st.logo(
        ICON_TEXT,
        icon_image=ICON,
        size="large",
        link=link
    )


def display_current_model_info():
    """현재 모델 정보 표시 (사이드바용)"""
    if st.session_state.current_model:
        model_name = st.session_state.current_model.get('display_name', 'Unknown Model')
        provider = st.session_state.current_model.get('provider', 'Unknown')
        
        # 테마에 따른 색상 설정
        is_dark = st.session_state.get('dark_mode', True)
        
        if is_dark:
            bg_color = "#1a1a1a"
            border_color = "#333333"
            text_color = "#ffffff"
            subtitle_color = "#888888"
            icon_color = "#4a9eff"
        else:
            bg_color = "#f8f9fa"
            border_color = "#e9ecef"
            text_color = "#212529"
            subtitle_color = "#6c757d"
            icon_color = "#0d6efd"
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 1px solid {border_color};
            border_radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s ease;
        ">
            <div style="
                color: {icon_color};
                font-size: 18px;
                line-height: 1;
            ">🤖</div>
            <div style="flex: 1; min-width: 0;">
                <div style="
                    color: {text_color};
                    font-weight: 600;
                    font-size: 14px;
                    margin: 0;
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                ">{model_name}</div>
                <div style="
                    color: {subtitle_color};
                    font-size: 12px;
                    margin: 2px 0 0 0;
                    opacity: 0.8;
                ">{provider}</div>
            </div>
            <div style="
                width: 8px;
                height: 8px;
                background: #10b981;
                border-radius: 50%;
                flex-shrink: 0;
            "></div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # 모델이 선택되지 않은 경우
        is_dark = st.session_state.get('dark_mode', True)
        
        if is_dark:
            bg_color = "#1a1a1a"
            border_color = "#444444"
            text_color = "#888888"
            icon_color = "#666666"
        else:
            bg_color = "#f8f9fa"
            border_color = "#dee2e6"
            text_color = "#6c757d"
            icon_color = "#adb5bd"
        
        st.markdown(f"""
        <div style="
            background: {bg_color};
            border: 1px dashed {border_color};
            border_radius: 8px;
            padding: 12px 16px;
            margin: 8px 0;
            display: flex;
            align-items: center;
            gap: 12px;
            opacity: 0.7;
        ">
            <div style="
                color: {icon_color};
                font-size: 18px;
                line-height: 1;
            ">🤖</div>
            <div style="flex: 1;">
                <div style="
                    color: {text_color};
                    font-weight: 500;
                    font-size: 14px;
                    margin: 0;
                ">No Model Selected</div>
                <div style="
                    color: {text_color};
                    font-size: 12px;
                    margin: 2px 0 0 0;
                    opacity: 0.6;
                ">Choose a model to start</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def create_navigation_sidebar():
    """네비게이션 사이드바 생성"""
    with st.sidebar:
        # 현재 모델 정보
        display_current_model_info()
        st.divider()
        
        # 네비게이션 버튼들
        if st.button("🤖 Change Model", use_container_width=True, help="Switch to a different AI model"):
            st.switch_page("pages/01_🤖_Model_Selection.py")
            
        if st.button("💬 Main Chat", use_container_width=True, help="Go to main chat interface"):
            st.switch_page("pages/02_💬_Main_Chat.py")
        
        if st.button("📋 Chat History", use_container_width=True, help="View conversation history and logs"):
            st.switch_page("pages/03_📋_Logs.py")
        
        st.divider()
        
        # 설정 섹션
        st.markdown("### ⚙️ Settings")
        
        # 테마 토글
        theme_manager = st.session_state.get('theme_manager')
        if theme_manager:
            theme_manager.create_theme_toggle(st)
        
        # Debug 모드 토글
        app_state = get_app_state_manager()
        debug_mode = st.checkbox(
            "🐞 Debug Mode", 
            value=st.session_state.debug_mode,
            help="Show detailed debugging information"
        )
        app_state.set_debug_mode(debug_mode)


def display_session_stats():
    """세션 통계 표시 (사이드바용)"""
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
    """디버그 정보 표시 (사이드바용)"""
    if not st.session_state.debug_mode:
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
        
        if "logging" in debug_info:
            st.markdown("**Logging Info:**")
            st.json(debug_info["logging"])


def create_new_chat_button():
    """새 채팅 버튼 생성"""
    app_state = get_app_state_manager()
    
    if st.button("✨ New Chat", use_container_width=True, help="Start a fresh conversation"):
        app_state.create_new_conversation()
        st.success("✨ New chat session started!")
        st.rerun()


def show_page_header(title: str, subtitle: Optional[str] = None):
    """페이지 헤더 표시"""
    display_logo()
    st.title(title)
    if subtitle:
        st.markdown(subtitle)


def check_model_required(redirect_page: str = "streamlit_app.py") -> bool:
    """모델이 필요한 페이지에서 모델 선택 여부 확인
    
    Args:
        redirect_page: 모델이 없을 때 리다이렉트할 페이지
        
    Returns:
        bool: 모델이 선택되어 있으면 True, 없으면 False
    """
    if not st.session_state.current_model:
        st.warning("⚠️ Please select a model first")
        if st.button("Go to Model Selection", type="primary"):
            st.switch_page(redirect_page)
        return False
    return True


def handle_error_display(error_msg: str, retry_callback=None):
    """에러 표시 및 재시도 처리"""
    st.error(error_msg)
    
    if retry_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Retry", use_container_width=True):
                retry_callback()


def create_loading_spinner(text: str = "Loading..."):
    """로딩 스피너 생성"""
    return st.spinner(text)


class PageLayout:
    """페이지 레이아웃 헬퍼 클래스"""
    
    @staticmethod
    def two_column_layout(ratio: list = [2, 1]):
        """2컬럼 레이아웃 생성"""
        return st.columns(ratio)
    
    @staticmethod
    def three_column_layout(ratio: list = [1, 2, 1]):
        """3컬럼 레이아웃 생성"""
        return st.columns(ratio)
    
    @staticmethod
    def center_content():
        """컨텐츠 중앙 정렬용 컬럼 반환"""
        col1, col2, col3 = st.columns([1, 2, 1])
        return col2
    
    @staticmethod
    def create_container(height: Optional[int] = None, border: bool = False):
        """컨테이너 생성"""
        if height:
            return st.container(height=height, border=border)
        return st.container(border=border)
