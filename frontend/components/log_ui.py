"""
로그 관리 UI - 세션 목록과 재현 기능 제공
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any, List

from src.utils.logging.logger import get_logger

class LogManagerUI:
    """로그 관리자"""
    
    def __init__(self):
        self.logger = get_logger()
    
    def display_log_page(self):
        """로그 페이지"""
        st.title("📋 Session Logs")
        
        # 뒤로가기 버튼
        if st.button("← Back to Main", use_container_width=True):
            st.session_state.app_stage = "main_app"
            st.rerun()
        
        st.divider()
        
        # 세션 목록 로드
        sessions = self.logger.list_sessions(limit=20)
        
        if not sessions:
            st.info("No sessions found")
            return
        
        st.markdown(f"**{len(sessions)} recent sessions**")
        
        # 세션 목록을 카드 형태로 표시
        for session in sessions:
            self._display_session_card(session)
    
    def _display_session_card(self, session: Dict[str, Any]):
        """세션 카드 표시"""
        with st.container():
            # 세션 기본 정보
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # 시간 표시
                try:
                    dt = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = session['start_time'][:19]
                
                st.markdown(f"**📅 {time_str}**")
                st.caption(f"Session: {session['session_id'][:16]}...")
                
                # 내용 미리보기
                if session.get('preview'):
                    preview_text = session['preview']
                    st.caption(f"💬 {preview_text}")
                
                # 이벤트 수
                st.caption(f"📊 {session['event_count']} events")
            
            with col2:
                # 재현 버튼 (가장 중요한 기능)
                if st.button("🎬 Replay", key=f"replay_{session['session_id']}", use_container_width=True):
                    self._start_replay(session['session_id'])
            
            st.divider()
    
    def _start_replay(self, session_id: str):
        """세션 재현 시작"""
        try:
            # 재현할 세션 ID 저장
            st.session_state.replay_session_id = session_id
            st.session_state.replay_mode = True
            
            # 메인 앱으로 이동
            st.session_state.app_stage = "main_app"
            
            st.success(f"Starting replay for session {session_id[:16]}...")
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to start replay: {e}")
