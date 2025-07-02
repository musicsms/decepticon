import streamlit as st
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기존 DecepticonApp import
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.theme_manager import ThemeManager
from frontend.components.log_manager import LogManagerUI

ICON = "assets\logo.png"
ICON_TEXT = "assets\logo_text1.png"

# Streamlit 페이지 설정 
st.set_page_config(
    page_title="Decepticon",
    page_icon="📊",
    layout="wide",
)

# 페이지 네비게이션 사이드바 숨김
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
    
    section[data-testid="stSidebar"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# 테마 관리자 초기화
if "theme_manager" not in st.session_state:
    st.session_state.theme_manager = ThemeManager()

theme_manager = st.session_state.theme_manager
theme_manager.apply_theme()

# 로그 관리 UI 초기화
if "log_manager_ui" not in st.session_state:
    st.session_state.log_manager_ui = LogManagerUI()

log_manager_ui = st.session_state.log_manager_ui

# 재현 모드에서 메인 페이지로 자동 리디렉션
if st.session_state.get("replay_mode", False):
    st.info("🎬 Replay mode activated - redirecting to main chat...")
    st.switch_page("pages/main.py")

# 기존 run_log_manager 메서드 내용을 여기에 구현
log_manager_ui.display_log_page()