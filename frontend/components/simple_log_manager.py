"""
간단한 로그 관리 UI 컴포넌트
"""

import streamlit as st
import json
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.logging.conversation_logger import (
    get_conversation_logger,
    ConversationSession,
    EventType
)


class SimpleLogManagerUI:
    """간단한 로그 관리 UI 클래스"""
    
    def __init__(self):
        self.logger = get_conversation_logger()
        
    def display_simple_log_page(self):
        """간단한 로그 페이지 표시"""
        st.title("📊 :red[Session Logs]")
        
        # 뒤로가기 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.app_stage = "main_app"
                st.rerun()
        
        st.divider()
        
        # 현재 세션 정보 (간단하게)
        if self.logger.current_session:
            current = self.logger.current_session
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Current Session", "🟢 Active")
            with col2:
                st.metric("Messages", current.total_messages)
            with col3:
                st.metric("Events", current.total_events)
        else:
            st.info("No active session")
        
        st.divider()
        
        # 세션 목록 (간단하게)
        st.subheader("📋 All Sessions")
        
        # 모든 세션 로드
        sessions = self._load_all_sessions()
        
        if not sessions:
            st.info("No sessions found")
            return
        
        # 간단한 세션 카드 형태로 표시
        for session in sessions[:10]:  # 최근 10개만
            self._display_session_card(session)
    
    def _load_all_sessions(self) -> List[Dict[str, Any]]:
        """logs 폴더의 모든 세션 로드"""
        sessions = []
        logs_path = Path("logs")
        
        if not logs_path.exists():
            return sessions
        
        try:
            # logs 폴더 하위의 모든 JSON 파일 찾기
            for session_file in logs_path.rglob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 세션 정보 추출
                    sessions.append({
                        'file_path': str(session_file),
                        'session_id': session_data['session_id'],
                        'user_id': session_data.get('user_id', 'Unknown'),
                        'start_time': session_data['start_time'],
                        'platform': session_data.get('platform', 'unknown'),
                        'total_events': session_data.get('total_events', 0),
                        'total_messages': session_data.get('total_messages', 0),
                        'agents_used': session_data.get('agents_used', []),
                        'model_info': session_data.get('model_info', {}),
                        'duration': self._calculate_duration(session_data)
                    })
                    
                except Exception as e:
                    print(f"Error reading {session_file}: {e}")
                    continue
            
            # 시간순 정렬 (최신 순)
            sessions.sort(key=lambda x: x['start_time'], reverse=True)
            
        except Exception as e:
            print(f"Error loading sessions: {e}")
        
        return sessions
    
    def _calculate_duration(self, session_data: Dict[str, Any]) -> str:
        """세션 지속시간 계산"""
        try:
            if session_data.get('end_time'):
                start = datetime.fromisoformat(session_data['start_time'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(session_data['end_time'].replace('Z', '+00:00'))
                duration = end - start
                return str(duration).split('.')[0]
            else:
                return "In Progress"
        except:
            return "Unknown"
    
    def _display_session_card(self, session: Dict[str, Any]):
        """세션 카드 표시"""
        with st.container():
            # 세션 헤더
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                # 시간 포맷팅
                try:
                    dt = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                    time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    time_str = session['start_time'][:19]
                
                # 플랫폼 아이콘
                platform_icon = "🌐" if session['platform'] == 'web' else "💻"
                
                st.markdown(f"**{platform_icon} {time_str}**")
                st.caption(f"Session: {session['session_id'][:16]}...")
                
                # 모델 정보
                if session['model_info']:
                    model_name = session['model_info'].get('display_name', 'Unknown')
                    st.caption(f"🤖 Model: {model_name}")
                
                # 에이전트 정보
                if session['agents_used']:
                    agents_str = ", ".join(session['agents_used'][:3])
                    if len(session['agents_used']) > 3:
                        agents_str += f" +{len(session['agents_used']) - 3} more"
                    st.caption(f"👥 Agents: {agents_str}")
            
            with col2:
                st.metric("Messages", session['total_messages'])
                st.metric("Events", session['total_events'])
            
            with col3:
                # Replay 버튼 (가장 중요한 기능)
                if st.button("🎬 Replay", key=f"replay_{session['session_id']}", use_container_width=True):
                    self._start_replay(session['session_id'])
                
                # 다운로드 버튼
                if st.button("📄 Export", key=f"export_{session['session_id']}", use_container_width=True):
                    self._export_session(session['session_id'])
            
            st.divider()
    
    def _start_replay(self, session_id: str):
        """세션 재생 시작 - 메인 앱으로 이동"""
        try:
            # 세션 로드 확인
            session = self.logger.load_session(session_id)
            if not session:
                st.error(f"Failed to load session {session_id[:16]}...")
                return
            
            # 재생할 세션 ID를 세션 상태에 저장
            st.session_state.replay_session_id = session_id
            st.session_state.replay_mode = True
            st.session_state.replay_event_index = 0
            
            # 기존 상태 백업
            if "structured_messages" in st.session_state:
                st.session_state.backup_messages = st.session_state.structured_messages.copy()
            
            # 메인 앱으로 이동
            st.session_state.app_stage = "main_app"
            st.success(f"Starting replay for session {session_id[:16]}... ({session.total_events} events)")
            time.sleep(1)  # 사용자가 메시지를 볼 수 있도록 잠시 대기
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to start replay: {e}")
    
    def _export_session(self, session_id: str):
        """세션 내보내기"""
        try:
            # 세션 로드
            session = self.logger.load_session(session_id)
            if not session:
                st.error("Failed to load session")
                return
            
            # JSON으로 내보내기
            json_data = session.to_dict()
            st.download_button(
                "📄 Download JSON",
                json.dumps(json_data, indent=2, ensure_ascii=False),
                file_name=f"session_{session_id[:8]}.json",
                mime="application/json",
                key=f"download_{session_id}"
            )
            
        except Exception as e:
            st.error(f"Export failed: {e}")
