"""
간소화된 로그 관리 UI 컴포넌트 - 기본 기능만 제공
"""

import streamlit as st
from typing import Dict, Any, List, Optional

from src.utils.logging.minimal_logger import get_minimal_logger

class LogManagerUI:
    """간소화된 로그 관리 UI 클래스"""
    
    def __init__(self):
        self.logger = get_minimal_logger()
        
    def display_log_overview(self, container):
        """로그 개요 표시 - 간소화"""
        with container:
            st.subheader("📊 Log Overview")
            
            # 세션 목록 가져오기
            all_sessions = self.logger.list_sessions()
            sessions = all_sessions[:10]  # 최근 10개만
            
            if sessions:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Sessions", len(sessions))
                with col2:
                    total_events = sum(s.get('event_count', 0) for s in sessions)
                    st.metric("Total Events", total_events)
            else:
                st.info("No sessions found")
    
    def display_session_history(self, container, user_id: Optional[str] = None):
        """세션 히스토리 표시 - 간소화"""
        with container:
            st.subheader("📅 Session History")
            
            # 세션 목록 가져오기
            all_sessions = self.logger.list_sessions()
            sessions = all_sessions[:20]  # 최근 20개만
            
            if not sessions:
                st.info("No sessions found")
                return
            
            # 간단한 세션 리스트
            for session in sessions:
                self._display_simple_session_row(session)
    
    def _display_simple_session_row(self, session: Dict[str, Any]):
        """간단한 세션 행 표시"""
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            start_time = session['start_time'][:19].replace('T', ' ')
            st.text(f"📅 {start_time}")
            st.caption(f"Session: {session['session_id'][:16]}...")
            # 미리보기는 성능상 이유로 제거
        
        with col2:
            st.text(f"📊 {session.get('event_count', 0)} events")
        
        with col3:
            if st.button("🎬 Replay", key=f"simple_replay_{session['session_id']}"):
                self._start_simple_replay(session['session_id'])
        
        st.divider()
    
    def _start_simple_replay(self, session_id: str):
        """간단한 재현 시작"""
        try:
            st.session_state.replay_session_id = session_id
            st.session_state.replay_mode = True
            st.session_state.app_stage = "main_app"
            st.success(f"Starting replay for session {session_id[:16]}...")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to start replay: {e}")
