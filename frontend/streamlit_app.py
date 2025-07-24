"""
Decepticon 모델 선택 페이지 - 첫 진입점
사용자가 AI 모델을 선택하고 초기화하는 메인 엔트리포인트

실행 방법:
streamlit run frontend/streamlit_app.py
"""

import streamlit as st
import asyncio
import os
import sys
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# .env 파일 로드
load_dotenv()

# 필요한 모듈들
from frontend.web.utils.page_utils import setup_page_config, setup_theme
from frontend.web.core.app_state import get_app_state_manager
from frontend.web.core.executor_manager import get_executor_manager
from frontend.web.model_selection_ui import ModelSelectionUI

# 아이콘 설정
ICON = "assets/logo.png"
ICON_TEXT = "assets/logo_text1.png"

# 페이지 설정
setup_page_config("Decepticon")
setup_theme()

# 상태 관리자들
app_state = get_app_state_manager()
executor_manager = get_executor_manager()

def main():
    """모델 선택 페이지 메인 (앱의 첫 진입점)"""
    
    # 로고 표시 (고정)
    st.logo(
        ICON_TEXT,
        icon_image=ICON,
        size="large",
        link="https://purplelab.framer.ai"
    )
    
    # 이중 보호: empty로 전체 앱 뷰 선언 + 내부에 고정 높이 컨테이너
    with st.empty():
        # 내부에 고정 높이 컨테이너로 무조건 전체 페이지 스크롤 방지
        with st.container(height=None, border=False):
            # 중앙 집중 레이아웃
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                # 현재 선택된 모델 표시 (있는 경우)
                if st.session_state.current_model:
                    current_model = st.session_state.current_model
                    st.success(f"✅ Current Model: {current_model.get('display_name', 'Unknown')}")
                    
                    # 모델 변경 확인
                    if st.button("🔄 Change Model", use_container_width=True):
                        # 모델 변경 시 상태 초기화
                        st.session_state.current_model = None
                        st.session_state.executor_ready = False
                        executor_manager.reset()
                        st.rerun()
                    
                    st.divider()
                
                # 모델 선택 UI
                theme_manager = st.session_state.theme_manager
                model_ui = ModelSelectionUI(theme_manager)
                
                # 모델 선택
                selected_model = model_ui.display_model_selection_ui()
                
                if selected_model:
                    # 모델 초기화 처리 (같은 컨테이너에서)
                    handle_model_initialization(selected_model)


def handle_model_initialization(model_info):
    """모델 초기화 처리 - 동일한 컨테이너에서"""
    
    async def initialize_model():
        """비동기 모델 초기화"""
        try:
            st.session_state.initialization_in_progress = True
            
            # 초기화 진행 (같은 컨테이너에서)
            with st.spinner(f"Initializing {model_info.get('display_name', 'Model')}..."):
                success = await executor_manager.initialize_with_model(model_info)
            
            if success:
                st.success(f"✅ {model_info.get('display_name', 'Model')} initialized successfully!")
                
                # 잠깐 대기 후 페이지 전환
                import time
                time.sleep(1.5)
                
                # Streamlit 네이티브 페이지 전환
                st.switch_page("pages/01_Chat.py")
            
            else:
                error_msg = st.session_state.initialization_error or "Unknown initialization error"
                st.error(f"❌ Initialization failed: {error_msg}")
                
                # 재시도 버튼 (같은 레이아웃에서)
                if st.button("🔄 Retry", use_container_width=True):
                    st.rerun()
        
        except Exception as e:
            st.error(f"❌ Initialization error: {str(e)}")
            
            # 재시도 버튼 (같은 레이아웃에서)
            if st.button("🔄 Retry", use_container_width=True):
                st.rerun()
        
        finally:
            st.session_state.initialization_in_progress = False
    
    # 비동기 실행
    asyncio.run(initialize_model())


if __name__ == "__main__":
    main()
