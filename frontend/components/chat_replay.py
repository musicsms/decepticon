"""
채팅 화면에서 세션 자동 재생 기능 (간단 버전)
"""

import streamlit as st
import time
import asyncio
from datetime import datetime
from typing import Optional, List
from src.utils.logging.conversation_logger import (
    get_conversation_logger,
    ConversationSession,
    EventType
)


class SimpleReplayManager:
    """간단한 자동 재생 관리자"""
    
    def __init__(self):
        self.logger = get_conversation_logger()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def start_replay(self, session_id: str):
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
        for key in ["replay_session", "replay_session_id"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def display_replay_header(self, container):
        """재생 헤더 표시"""
        if not self.is_replay_mode():
            return
        
        session = st.session_state.get("replay_session")
        if not session:
            return
        
        with container:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.info(f"🎬 **Replaying Session**: {session.session_id[:16]}... | {session.total_events} events | {session.total_messages} messages")
            
            with col2:
                if st.button("❌ Stop", use_container_width=True, key="stop_replay"):
                    self.stop_replay()
                    st.rerun()
    
    async def auto_replay_workflow(self, chat_area, agents_container, chat_ui):
        """자동 재생 워크플로우 (원래 워크플로우처럼)"""
        if not self.is_replay_mode():
            return
        
        session = st.session_state.get("replay_session")
        if not session or not session.events:
            st.error("No events to replay")
            return
        
        # 워크플로우 스타일로 재생
        with st.status("Replaying session...", expanded=True) as status:
            total_events = len(session.events)
            processed_events = 0
            
            for i, event in enumerate(session.events):
                try:
                    # 상태 업데이트
                    status.update(
                        label=f"Replaying event {i+1}/{total_events}: {event.event_type.name}",
                        state="running"
                    )
                    
                    # 이벤트를 메시지로 변환
                    frontend_message = self._convert_event_to_frontend_message(event)
                    
                    if frontend_message:
                        # 기존 메시지 목록에 추가
                        st.session_state.structured_messages.append(frontend_message)
                        
                        # UI에 표시
                        with chat_area:
                            self._display_replay_message(frontend_message, chat_ui)
                        
                        # 에이전트 상태 업데이트
                        if event.agent_name and agents_container:
                            self._update_agent_status_for_replay(event.agent_name, agents_container, chat_ui)
                    
                    processed_events += 1
                    
                    # 자연스러운 지연 (원래 워크플로우처럼)
                    await asyncio.sleep(0.8)  # 800ms 지연
                    
                except Exception as e:
                    st.error(f"Error replaying event: {e}")
                    continue
            
            # 완료
            status.update(label=f"Replay completed! {processed_events} events processed", state="complete")
    
    def _convert_event_to_frontend_message(self, event) -> Optional[dict]:
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
                "timestamp": timestamp
            }
        
        elif event.event_type == EventType.TOOL_EXECUTION:
            return {
                "type": "tool",
                "content": event.content or "",
                "tool_name": event.tool_name or "Tool",
                "timestamp": timestamp
            }
        
        return None
    
    def _display_replay_message(self, message: dict, chat_ui):
        """재생 메시지 표시"""
        try:
            if message["type"] == "user":
                chat_ui.display_user_message(message["content"])
            
            elif message["type"] == "ai":
                # 에이전트 메시지 형태로 변환
                agent_message = {
                    "type": "agent",
                    "agent_id": message.get("agent_name", "agent").lower(),
                    "display_name": message.get("agent_name", "Agent"),
                    "avatar": "🤖",
                    "data": {
                        "content": message["content"]
                    },
                    "timestamp": message["timestamp"]
                }
                chat_ui.display_agent_message(agent_message, streaming=False)
            
            elif message["type"] == "tool":
                # 도구 메시지 형태로 변환
                tool_message = {
                    "type": "tool",
                    "display_name": message.get("tool_name", "Tool"),
                    "data": {
                        "content": message["content"]
                    },
                    "timestamp": message["timestamp"]
                }
                chat_ui.display_tool_message(tool_message)
                
        except Exception as e:
            st.error(f"Error displaying message: {e}")
    
    def _update_agent_status_for_replay(self, agent_name: str, agents_container, chat_ui):
        """재생용 에이전트 상태 업데이트"""
        try:
            # 간단한 상태 업데이트
            if hasattr(st.session_state, 'active_agent'):
                # 이전 에이전트를 완료로 설정
                if st.session_state.active_agent and st.session_state.active_agent not in st.session_state.get('completed_agents', []):
                    if 'completed_agents' not in st.session_state:
                        st.session_state.completed_agents = []
                    st.session_state.completed_agents.append(st.session_state.active_agent)
                
                # 현재 에이전트 설정
                st.session_state.active_agent = agent_name.lower()
            
            # 에이전트 상태 표시 업데이트
            if hasattr(chat_ui, 'display_agent_status'):
                chat_ui.display_agent_status(
                    agents_container,
                    st.session_state.get('active_agent'),
                    None,
                    st.session_state.get('completed_agents', [])
                )
        except Exception as e:
            # 에러가 발생해도 재생은 계속
            print(f"Error updating agent status: {e}")
