"""
간단한 재현 시스템 - 기존 워크플로우와 동일한 방식으로 재생
"""

import streamlit as st
import time
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional

from src.utils.logging.minimal_logger import get_minimal_logger, MinimalSession

class SimpleReplaySystem:
    """간단한 재현 시스템 - 추가 UI 없이 기존 워크플로우처럼 재생"""
    
    def __init__(self):
        self.logger = get_minimal_logger()
    
    def start_replay(self, session_id: str) -> bool:
        """재현 시작 - 기존 워크플로우와 동일하게"""
        try:
            # 세션 로드
            session = self.logger.load_session(session_id)
            if not session:
                return False
            
            # 재현 모드 설정 (부수적 UI 요소 없이)
            st.session_state.replay_mode = True
            st.session_state.replay_session = session
            st.session_state.replay_session_id = session_id
            
            # 기존 메시지 백업
            if "structured_messages" in st.session_state:
                st.session_state.backup_messages = st.session_state.structured_messages.copy()
            
            # 재현용 메시지 초기화
            st.session_state.structured_messages = []
            
            # 에이전트 상태 초기화
            st.session_state.active_agent = None
            st.session_state.completed_agents = []
            
            return True
            
        except Exception as e:
            return False
    
    def stop_replay(self):
        """재현 중지"""
        st.session_state.replay_mode = False
        
        # 기존 메시지 복원
        if "backup_messages" in st.session_state:
            st.session_state.structured_messages = st.session_state.backup_messages
            del st.session_state.backup_messages
        
        # 재현 관련 상태 정리
        for key in ["replay_session", "replay_session_id"]:
            if key in st.session_state:
                del st.session_state[key]
    
    def is_replay_mode(self) -> bool:
        """재현 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    async def execute_replay(self, chat_area, agents_container, chat_ui):
        """재현 실행 - 기존 워크플로우와 동일한 방식 (부수적 UI 없이)"""
        session = st.session_state.get("replay_session")
        if not session or not session.events:
            return
        
        # 기존 워크플로우와 동일한 상태 표시 (부수적 메시지 없이)
        with st.status("Processing...", expanded=True) as status:
            
            for i, event in enumerate(session.events):
                try:
                    # 상태 업데이트 (기존 워크플로우처럼)
                    status.update(
                        label=f"Processing...",
                        state="running"
                    )
                    
                    # 이벤트를 프론트엔드 메시지로 변환
                    frontend_message = self._convert_to_frontend_message(event)
                    
                    if frontend_message:
                        # 메시지 리스트에 추가
                        st.session_state.structured_messages.append(frontend_message)
                        
                        # UI에 표시 (기존 방식과 동일)
                        with chat_area:
                            self._display_message(frontend_message, chat_ui)
                        
                        # 에이전트 상태 업데이트
                        if event.agent_name:
                            self._update_agent_status(event.agent_name, agents_container, chat_ui)
                    
                    # 자연스러운 지연 (기존 워크플로우처럼)
                    await asyncio.sleep(0.8)
                    
                except Exception as e:
                    continue
            
            # 완료 (기존 워크플로우처럼)
            status.update(label="Processing complete!", state="complete")
    
    def _convert_to_frontend_message(self, event) -> Optional[Dict[str, Any]]:
        """이벤트를 프론트엔드 메시지로 변환"""
        timestamp = datetime.now().isoformat()
        
        if event.event_type.value == "user_input":
            return {
                "type": "user",
                "content": event.content,
                "timestamp": timestamp
            }
        
        elif event.event_type.value == "agent_response":
            # 기존 메시지 프로세서와 동일한 형태로 변환
            return {
                "type": "agent",
                "agent_id": event.agent_name.lower() if event.agent_name else "agent",
                "display_name": event.agent_name or "Agent",
                "avatar": self._get_agent_avatar(event.agent_name),
                "data": {
                    "content": event.content
                },
                "timestamp": timestamp,
                "id": f"replay_agent_{event.agent_name}_{timestamp}"
            }
        
        elif event.event_type.value == "tool_command":
            return {
                "type": "tool_command",
                "display_name": event.tool_name or "Tool",
                "avatar": "🔧",
                "data": {
                    "command": event.content
                },
                "timestamp": timestamp,
                "id": f"replay_tool_cmd_{event.tool_name}_{timestamp}"
            }
        
        elif event.event_type.value == "tool_output":
            return {
                "type": "tool_output",
                "display_name": event.tool_name or "Tool",
                "avatar": "🔧",
                "data": {
                    "content": event.content
                },
                "timestamp": timestamp,
                "id": f"replay_tool_out_{event.tool_name}_{timestamp}"
            }
        
        return None
    
    def _display_message(self, message: Dict[str, Any], chat_ui):
        """메시지 표시 - 기존 chat_ui 방식 사용"""
        try:
            message_type = message.get("type")
            
            if message_type == "user":
                chat_ui.display_user_message(message["content"])
            
            elif message_type == "agent":
                chat_ui.display_agent_message(message, streaming=False)
            
            elif message_type == "tool_command":
                chat_ui.display_tool_command(message)
            
            elif message_type == "tool_output":
                chat_ui.display_tool_output(message)
                
        except Exception as e:
            print(f"Error displaying message: {e}")
    
    def _update_agent_status(self, agent_name: str, agents_container, chat_ui):
        """에이전트 상태 업데이트 - 기존 방식과 동일"""
        try:
            # 이전 에이전트를 완료로 표시
            if "active_agent" in st.session_state and st.session_state.active_agent:
                if "completed_agents" not in st.session_state:
                    st.session_state.completed_agents = []
                if st.session_state.active_agent not in st.session_state.completed_agents:
                    st.session_state.completed_agents.append(st.session_state.active_agent)
            
            # 현재 에이전트 설정
            st.session_state.active_agent = agent_name.lower()
            
            # 상태 표시 업데이트 (기존 방식)
            if hasattr(chat_ui, 'display_agent_status'):
                chat_ui.display_agent_status(
                    agents_container,
                    st.session_state.get('active_agent'),
                    None,
                    st.session_state.get('completed_agents', [])
                )
        except Exception as e:
            print(f"Error updating agent status: {e}")
    
    def _get_agent_avatar(self, agent_name: str) -> str:
        """에이전트 아바타 반환"""
        if not agent_name:
            return "🤖"
        
        agent_avatars = {
            "supervisor": "👨‍💼",
            "planner": "🧠",
            "reconnaissance": "🔍",
            "initial_access": "🔑",
            "execution": "💻",
            "persistence": "🔐",
            "privilege_escalation": "🔒",
            "defense_evasion": "🕵️",
            "summary": "📋"
        }
        
        agent_key = agent_name.lower()
        for key, avatar in agent_avatars.items():
            if key in agent_key:
                return avatar
        
        return "🤖"

# 전역 인스턴스
_replay_system: Optional[SimpleReplaySystem] = None

def get_replay_system() -> SimpleReplaySystem:
    """전역 재현 시스템 인스턴스 반환"""
    global _replay_system
    if _replay_system is None:
        _replay_system = SimpleReplaySystem()
    return _replay_system
