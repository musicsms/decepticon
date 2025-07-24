"""
채팅 화면에서 세션 자동 재생 기능 - Executor 통합 버전
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.logging.replay import get_replay_system
from frontend.web.message import CLIMessageProcessor

class ReplayManager:
    """자동 재생 관리자 - Executor 및 MessageProcessor와 통합"""
    
    def __init__(self):
        self.replay_system = get_replay_system()
        self.message_processor = CLIMessageProcessor()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def handle_replay_in_main_app(self, chat_area, agents_container, chat_ui, terminal_ui) -> bool:
        """메인 앱에서 재현 처리 - Executor와 통합된 방식 + 터미널 처리"""
        if not self.is_replay_mode():
            return False
        
        replay_session_id = st.session_state.get("replay_session_id")
        if not replay_session_id:
            return False
        
        try:
            # 재현 시작
            if self.replay_system.start_replay(replay_session_id):
                # Executor와 통합된 비동기 재현 실행 (터미널 UI 포함)
                asyncio.run(self._execute_replay_with_executor(chat_area, agents_container, chat_ui, terminal_ui))
                
                # 재현 완료 후 정리
                self.replay_system.stop_replay()
                
                return True
            
        except Exception as e:
            st.error(f"Replay error: {e}")
            # 에러 발생 시 재현 모드 해제
            self.replay_system.stop_replay()
        
        return False
    
    async def _execute_replay_with_executor(self, chat_area, agents_container, chat_ui, terminal_ui):
        """Executor와 동일한 방식으로 재현 실행 + 터미널 처리"""
        session = st.session_state.get("replay_session")
        if not session or not session.events:
            return
        
        # 재현 시작 메시지
        with st.status("🎬 Replaying session...", expanded=True) as status:
            
            # 모든 이벤트를 Executor 스타일로 변환하여 처리
            replay_messages = []
            terminal_messages = []
            event_history = []
            agent_activity = {}
            
            status.update(label=f"Processing {len(session.events)} events...", state="running")
            
            # 전체 이벤트를 MessageProcessor를 통해 변환
            for i, event in enumerate(session.events):
                try:
                    # 이벤트를 Executor 스타일 이벤트로 변환
                    executor_event = self._convert_to_executor_event(event)
                    
                    if executor_event:
                        # MessageProcessor를 사용하여 frontend 메시지로 변환 (Executor와 동일)
                        frontend_message = self.message_processor.process_cli_event(executor_event)
                        
                        # 중복 확인
                        if not self.message_processor.is_duplicate_message(
                            frontend_message, replay_messages
                        ):
                            replay_messages.append(frontend_message)
                            
                            # tool 메시지인 경우 터미널 메시지에도 추가
                            if frontend_message.get("type") == "tool":
                                terminal_messages.append(frontend_message)
                            
                            # 이벤트 히스토리에 추가
                            event_history.append(executor_event)
                            
                            # 에이전트 활동 추적
                            agent_name = executor_event.get("agent_name", "Unknown")
                            if agent_name not in agent_activity:
                                agent_activity[agent_name] = 0
                            agent_activity[agent_name] += 1
                    
                    # 진행 상황 업데이트
                    if (i + 1) % 10 == 0:  # 10개마다 업데이트
                        status.update(label=f"Processed {i + 1}/{len(session.events)} events...", state="running")
                        
                except Exception as e:
                    print(f"Error processing event {i}: {e}")
                    continue
            
            # 메시지들을 한번에 세션 상태에 설정 (Executor와 동일한 변수명 사용)
            st.session_state.frontend_messages = replay_messages  # ✅ 올바른 변수명
            st.session_state.structured_messages = replay_messages  # Chat UI에서 사용하는 변수명
            st.session_state.terminal_messages = terminal_messages
            st.session_state.event_history = event_history
            
            # 터미널 UI에 메시지 적용 및 초기화 강화
            if terminal_ui:
                try:
                    # 터미널 CSS 재적용 (리플레이 모드에서 필수)
                    terminal_ui.apply_terminal_css()
                    
                    # 터미널 히스토리 완전 초기화
                    terminal_ui.clear_terminal()
                    
                    # 재현된 터미널 메시지들 처리 (초기 메시지는 추가하지 않음)
                    if terminal_messages:
                        terminal_ui.process_structured_messages(terminal_messages)
                    
                    # 세션 상태에 터미널 히스토리 저장
                    st.session_state.terminal_history = terminal_ui.terminal_history
                    
                    # 디버그 정보 (디버그 모드에서만)
                    if st.session_state.get("debug_mode", False):
                        st.write(f"Debug - Replay terminal processing: {len(terminal_messages)} messages")
                        st.write(f"Debug - Terminal history after replay: {len(terminal_ui.terminal_history)}")
                    
                except Exception as term_error:
                    st.error(f"Terminal processing error during replay: {term_error}")
                    print(f"Terminal processing error during replay: {term_error}")
            
            # 에이전트 상태 업데이트 (마지막 에이전트 활성화)
            if agent_activity:
                completed_agents = []
                active_agent = None
                
                # 에이전트 목록에서 마지막을 active로, 나머지를 completed로
                agent_list = list(agent_activity.keys())
                if len(agent_list) > 1:
                    completed_agents = [agent.lower() for agent in agent_list[:-1]]
                    active_agent = agent_list[-1].lower()
                elif len(agent_list) == 1:
                    active_agent = agent_list[0].lower()
                
                st.session_state.completed_agents = completed_agents
                st.session_state.active_agent = active_agent
                
                # 에이전트 상태 업데이트 함수 호출 (app.py의 _update_agent_status_from_events와 동일)
                if hasattr(chat_ui, 'display_agent_status'):
                    chat_ui.display_agent_status(
                        agents_container,
                        active_agent,
                        None,
                        completed_agents
                    )
            
            # 재현 완료 표시
            st.session_state.replay_completed = True
            
            # 완료
            status.update(
                label=f"✅ Replay Complete! Loaded {len(replay_messages)} messages, {len(terminal_messages)} terminal events, {len(agent_activity)} agents active", 
                state="complete"
            )
    
    def _convert_to_executor_event(self, event) -> Optional[Dict[str, Any]]:
        """이벤트를 Executor 스타일 이벤트로 변환"""
        timestamp = datetime.now().isoformat()
        
        if event.event_type.value == "user_input":
            return {
                "type": "message",
                "message_type": "user",
                "agent_name": "User",
                "content": event.content,
                "timestamp": timestamp
            }
        
        elif event.event_type.value == "agent_response":
            executor_event = {
                "type": "message",
                "message_type": "ai",
                "agent_name": event.agent_name or "Agent",
                "content": event.content,
                "timestamp": timestamp
            }
            
            # Tool calls 정보 복원 (이벤트에 저장되어 있는 경우)
            if hasattr(event, 'tool_calls') and event.tool_calls:
                executor_event["tool_calls"] = event.tool_calls
            
            return executor_event
        
        elif event.event_type.value == "tool_command":
            return {
                "type": "message",
                "message_type": "tool",
                "agent_name": "Tool",
                "tool_name": event.tool_name or "Unknown Tool",
                "content": f"Command: {event.content}",
                "timestamp": timestamp
            }
        
        elif event.event_type.value == "tool_output":
            return {
                "type": "message",
                "message_type": "tool",
                "agent_name": "Tool",
                "tool_name": event.tool_name or "Tool Output",
                "content": event.content,
                "timestamp": timestamp
            }
        
        return None
