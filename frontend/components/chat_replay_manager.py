"""
통합된 채팅 재현 관리자
SimpleReplayManager와 ChatReplayManager를 통합한 버전
"""

import streamlit as st
import time
import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.utils.logging.conversation_logger import (
    get_conversation_logger,
    ConversationSession,
    EventType
)


class ChatReplayManager:
    """통합된 채팅 재현 관리자"""
    
    def __init__(self):
        self.logger = get_conversation_logger()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def start_replay_mode(self):
        """재생 모드 시작 (세션 상태에서 session_id 가져오기)"""
        if "replay_session_id" in st.session_state:
            session_id = st.session_state.replay_session_id
            print(f"[DEBUG] Starting replay mode for session: {session_id}")
            return self.start_replay(session_id)
        else:
            print(f"[DEBUG] No replay_session_id found in session state")
            return False
    
    def start_replay(self, session_id: str) -> bool:
        """재생 시작"""
        try:
            # 세션 로드
            session = self.logger.load_session(session_id)
            if not session:
                st.error("Failed to load session for replay")
                return False
            
            # 재생 모드 설정
            st.session_state.replay_mode = True
            st.session_state.replay_session = session
            st.session_state.replay_session_id = session_id
            st.session_state.replay_event_index = st.session_state.get("replay_event_index", 0)
            
            # 기존 메시지 백업
            if "structured_messages" in st.session_state:
                st.session_state.backup_messages = st.session_state.structured_messages.copy()
            
            # 재생용 메시지 준비
            st.session_state.structured_messages = []
            
            return True
            
        except Exception as e:
            st.error(f"Failed to start replay: {e}")
            return False
    
    def stop_replay(self):
        """재생 중지"""
        st.session_state.replay_mode = False
        
        # 기존 메시지 복원
        if "backup_messages" in st.session_state:
            st.session_state.structured_messages = st.session_state.backup_messages
            del st.session_state.backup_messages
        
        # 재생 관련 상태 정리
        for key in ["replay_session", "replay_session_id", "replay_event_index"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def display_replay_controls(self, container):
        """재생 컨트롤 표시"""
        if not self.is_replay_mode():
            return
        
        session = st.session_state.get("replay_session")
        if not session:
            return
        
        with container:
            # 재생 헤더
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.info(f"🎬 **Replaying Session**: {session.session_id[:16]}... | {session.total_events} events | {session.total_messages} messages")
            
            with col2:
                if st.button("❌ Stop", use_container_width=True, key="stop_replay"):
                    self.stop_replay()
                    st.rerun()
            
            # 재생 진행 컨트롤
            if len(session.events) > 1:
                current_idx = st.session_state.get("replay_event_index", 0)
                max_idx = len(session.events) - 1
                
                # 슬라이더
                new_idx = st.slider(
                    "Event Progress", 
                    0, max_idx, current_idx,
                    key="replay_progress_slider"
                )
                
                if new_idx != current_idx:
                    st.session_state.replay_event_index = new_idx
                    st.rerun()
                
                # 재생 버튼들
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    if st.button("⏮️", key="replay_first"):
                        st.session_state.replay_event_index = 0
                        st.rerun()
                with col2:
                    if st.button("⏪", key="replay_prev"):
                        if current_idx > 0:
                            st.session_state.replay_event_index = current_idx - 1
                            st.rerun()
                with col3:
                    if st.button("▶️" if not st.session_state.get("auto_replay", False) else "⏸️", key="replay_play"):
                        st.session_state.auto_replay = not st.session_state.get("auto_replay", False)
                        st.rerun()
                with col4:
                    if st.button("⏩", key="replay_next"):
                        if current_idx < max_idx:
                            st.session_state.replay_event_index = current_idx + 1
                            st.rerun()
                with col5:
                    if st.button("⏭️", key="replay_last"):
                        st.session_state.replay_event_index = max_idx
                        st.rerun()
            
            st.divider()
    
    def get_replay_messages(self) -> List[Dict[str, Any]]:
        """현재 재생 인덱스까지의 메시지 반환"""
        if not self.is_replay_mode():
            return []
        
        session = st.session_state.get("replay_session")
        if not session or not session.events:
            return []
        
        current_idx = st.session_state.get("replay_event_index", 0)
        events_to_show = session.events[:current_idx + 1]
        
        messages = []
        for event in events_to_show:
            frontend_message = self._convert_event_to_frontend_message(event)
            if frontend_message:
                messages.append(frontend_message)
        
        # 자동 재생 처리
        if st.session_state.get("auto_replay", False):
            max_idx = len(session.events) - 1
            if current_idx < max_idx:
                time.sleep(1)  # 1초 지연
                st.session_state.replay_event_index = current_idx + 1
                st.rerun()
            else:
                # 재생 완료
                st.session_state.auto_replay = False
        
        return messages
    
    def display_replay_message(self, message: Dict[str, Any], container):
        """재생 메시지 표시"""
        try:
            message_type = message.get("type", "")
            
            if message_type == "user":
                with container.chat_message("user"):
                    st.write(message.get("content", ""))
            
            elif message_type == "ai":
                avatar = message.get("avatar", "🤖")
                display_name = message.get("display_name", "Agent")
                content = message.get("content", "")
                
                with container.chat_message("assistant", avatar=avatar):
                    st.markdown(f"**{display_name}**")
                    st.write(content)
            
            elif message_type == "tool":
                tool_name = message.get("tool_display_name", "Tool")
                content = message.get("content", "")
                
                with container.chat_message("tool", avatar="🔧"):
                    st.markdown(f"**🔧 {tool_name}**")
                    st.code(content)
                    
        except Exception as e:
            st.error(f"Error displaying replay message: {e}")
    
    def _convert_event_to_frontend_message(self, event) -> Optional[Dict[str, Any]]:
        """이벤트를 프론트엔드 메시지 형태로 변환"""
        timestamp = datetime.now().isoformat()
        
        if event.event_type == EventType.USER_INPUT:
            return {
                "type": "user",
                "content": event.content or "",
                "timestamp": timestamp
            }
        
        elif event.event_type == EventType.AGENT_RESPONSE:
            return {
                "type": "ai",
                "content": event.content or "",
                "agent_name": event.agent_name or "Agent",
                "display_name": event.agent_name or "Agent",
                "avatar": self._get_agent_avatar(event.agent_name),
                "timestamp": timestamp
            }
        
        elif event.event_type == EventType.TOOL_EXECUTION:
            return {
                "type": "tool",
                "content": event.content or "",
                "tool_name": event.tool_name or "Tool",
                "tool_display_name": event.tool_name or "Tool",
                "timestamp": timestamp
            }
        
        return None
    
    def _get_agent_avatar(self, agent_name: str) -> str:
        """에이전트 아바타 반환"""
        if not agent_name:
            return "🤖"
        
        agent_avatars = {
            "planner": "🧠",
            "reconnaissance": "🔍", 
            "initial_access": "🔑",
            "execution": "💻",
            "persistence": "🔐",
            "privilege_escalation": "🔒",
            "defense_evasion": "🕵️",
            "summary": "📋",
        }
        
        agent_key = agent_name.lower()
        for key, avatar in agent_avatars.items():
            if key in agent_key or agent_key in key:
                return avatar
        
        return "🤖"


# 하위 호환성을 위한 별칭
SimpleReplayManager = ChatReplayManager
