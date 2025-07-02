"""
로그 관리 UI 컴포넌트
"""

import streamlit as st
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.utils.logging.logger import get_logger

class LogManagerUI:
    """로그 관리 UI 클래스 - 재현 기능에 집중"""
    
    def __init__(self):
        self.logger = get_logger()
        
    def display_log_page(self):
        """로그 페이지 표시"""
        st.title("📊 :red[Session Logs]")
        
        # 뒤로가기 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.app_stage = "main_app"
                st.rerun()
        
        # 세션 목록 로드
        all_sessions = self.logger.list_sessions()
        sessions = all_sessions[:20]  # 최근 20개만 표시
        
        if not sessions:
            st.info("No sessions found")
            return
        
        # 세션 목록 표시
        st.subheader("📋 Recent Sessions")
        st.caption(f"Showing {len(sessions)} most recent sessions")
        
        for session in sessions:
            self._display_session_card(session)
    
    def _display_session_card(self, session: Dict[str, Any]):
        """세션 카드 표시"""
        with st.container():
            # 세션 헤더
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                # 시간 포맷팅
                try:
                    dt = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = session['start_time'][:19]
                
                st.markdown(f"**🕒 {time_str}**")
                st.caption(f"Session: {session['session_id'][:16]}...")
                
                # 내용 미리보기 (첫 번째 사용자 입력 찾기)
                preview_text = session.get('preview', "No user input found")
                st.caption(f"💬 {preview_text}")
                
                # 모델 정보 표시 (있는 경우)
                model_info = session.get('model')
                if model_info:
                    st.caption(f"🤖 Model: {model_info}")
            
            with col2:
                st.metric("Events", session.get('event_count', 0))
            
            with col3:
                # Replay 버튼 (가장 중요한 기능)
                if st.button("🎬 Replay", key=f"replay_{session['session_id']}", use_container_width=True):
                    self._start_replay(session['session_id'])
            
            with col4:
                # Export 버튼 - 바로 다운로드
                export_filename = f"session_{session['session_id'][:8]}_{datetime.now().strftime('%Y%m%d')}.json"
                
                export_data = self._prepare_export_data(session['session_id'])
                if export_data:
                    st.download_button(
                        label="💾 Export",
                        data=export_data,
                        file_name=export_filename,
                        mime="application/json",
                        key=f"export_{session['session_id']}",
                        use_container_width=True
                    )
                else:
                    st.button("❌ Export", disabled=True, key=f"export_disabled_{session['session_id']}", use_container_width=True)
            
            st.divider()
            
    def _prepare_export_data(self, session_id: str) -> str:
        try:
            print(f"Preparing export for session: {session_id}")
            
            # 세션 데이터 로드
            session = self.logger.load_session(session_id)
            if not session:
                print(f"Failed to load session: {session_id}")
                # 직접 파일 검색 시도
                for session_file in Path("logs").rglob(f"session_{session_id}.json"):
                    print(f"Found session file: {session_file}")
                    try:
                        with open(session_file, 'r', encoding='utf-8') as f:
                            session_data = json.load(f)
                        print(f"Successfully read session file with {len(session_data.get('events', []))} events")
                        session = session_data  # 원래 데이터 사용
                        break
                    except Exception as file_e:
                        print(f"Error reading session file: {file_e}")
                        continue
                
                if not session:
                    print(f"No session found for ID: {session_id}")
                    return None
            
            print(f"Successfully loaded session: {session_id}")
            
            # session이 MinimalSession 객체인 경우와 dict인 경우 모두 처리
            if hasattr(session, 'events'):  # MinimalSession 객체
                events_data = [event.to_dict() if hasattr(event, 'to_dict') else event for event in session.events]
                session_info = {
                    "session_id": session.session_id,
                    "start_time": session.start_time,
                    "total_events": len(session.events)
                }
                # 모델 정보 추가
                if hasattr(session, 'model') and session.model:
                    session_info["model"] = session.model
            else:  # dict 데이터
                events_data = session.get('events', [])
                session_info = {
                    "session_id": session.get('session_id', session_id),
                    "start_time": session.get('start_time', 'Unknown'),
                    "total_events": len(events_data)
                }
                # 모델 정보 추가 (dict에서)
                if session.get('model'):
                    session_info["model"] = session.get('model')
            
            # 익스포트용 데이터 구조 생성
            export_data = {
                "session_info": session_info,
                "events": events_data,
                "export_metadata": {
                    "exported_at": datetime.now().isoformat(),
                    "exported_by": "Decepticon Log Manager",
                    "version": "1.0"
                }
            }
            
            # JSON 문자열로 변환
            json_data = json.dumps(export_data, indent=2, ensure_ascii=False)
            print(f"Export data prepared successfully, size: {len(json_data)} characters")
            return json_data
            
        except Exception as e:
            print(f"Export error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _start_replay(self, session_id: str):
        """세션 재생 시작 - 메인 앱으로 이동"""
        try:
            # 재생할 세션 ID를 세션 상태에 저장
            st.session_state.replay_session_id = session_id
            st.session_state.replay_mode = True
            st.session_state.replay_completed = False  # 재현 완료 플래그 종석
            
            # 메인 앱으로 이동
            st.session_state.app_stage = "main_app"
            st.success(f"Starting replay for session {session_id[:16]}...")
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to start replay: {e}")