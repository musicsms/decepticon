"""
워크플로우 실행 처리 모듈
- 사용자 입력 처리
- 워크플로우 이벤트 스트림 관리
- 메시지 처리 및 UI 업데이트
"""

import streamlit as st
import asyncio
from typing import Dict, Any, List, Optional
import os
import sys

# 프로젝트 루트 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from web.message import CLIMessageProcessor
from web.core.executor_manager import get_executor_manager


class WorkflowHandler:
    """워크플로우 실행 핸들러"""
    
    def __init__(self):
        """워크플로우 핸들러 초기화"""
        self.message_processor = CLIMessageProcessor()
        self.executor_manager = get_executor_manager()
    
    async def execute_user_input(
        self, 
        user_input: str,
        chat_ui,
        terminal_ui,
        agents_container,
        chat_area
    ) -> bool:
        """사용자 입력 실행
        
        Args:
            user_input: 사용자 입력 텍스트
            chat_ui: 채팅 UI 인스턴스
            terminal_ui: 터미널 UI 인스턴스  
            agents_container: 에이전트 상태 컨테이너
            chat_area: 채팅 영역 컨테이너
            
        Returns:
            bool: 실행 성공 여부
        """
        if not self.executor_manager.is_ready():
            st.error("AI agents not ready. Please initialize first.")
            return False
        
        if st.session_state.workflow_running:
            st.warning("Another workflow is already running. Please wait.")
            return False
        
        # 사용자 메시지 처리
        user_message = self.message_processor._create_user_message(user_input)
        st.session_state.structured_messages.append(user_message)
        
        # 사용자 메시지 표시
        with chat_area:
            chat_ui.display_user_message(user_input)
        
        # 워크플로우 실행
        st.session_state.workflow_running = True
        
        try:
            with st.status("Processing...", expanded=True) as status:
                event_count = 0
                agent_activity = {}
                
                async for event in self.executor_manager.execute_workflow(
                    user_input,
                    config=st.session_state.thread_config
                ):
                    event_count += 1
                    st.session_state.event_history.append(event)
                    
                    try:
                        # 디버그 모드에서 이벤트 표시
                        if st.session_state.debug_mode:
                            with chat_area:
                                st.json(event)
                        
                        # 이벤트 처리
                        success = await self._process_event(
                            event, 
                            chat_ui, 
                            terminal_ui, 
                            chat_area, 
                            status,
                            agent_activity
                        )
                        
                        if not success:
                            break
                        
                        # 에이전트 상태 업데이트
                        self._update_agent_status(agents_container, chat_ui)
                        
                    except Exception as e:
                        if st.session_state.debug_mode:
                            st.error(f"Event processing error: {str(e)}")
                
                # 완료 상태 업데이트
                if agent_activity:
                    summary_text = f"Completed! Events: {event_count}, Active agents: {', '.join(agent_activity.keys())}"
                    status.update(label=summary_text, state="complete")
        
        except Exception as e:
            st.error(f"Workflow execution error: {str(e)}")
            return False
        
        finally:
            st.session_state.workflow_running = False
            # 세션 자동 저장
            if "logger" in st.session_state and st.session_state.logger:
                st.session_state.logger.save_session()
        
        return True
    
    async def _process_event(
        self,
        event: Dict[str, Any],
        chat_ui,
        terminal_ui, 
        chat_area,
        status,
        agent_activity: Dict[str, int]
    ) -> bool:
        """단일 이벤트 처리
        
        Args:
            event: 처리할 이벤트
            chat_ui: 채팅 UI 인스턴스
            terminal_ui: 터미널 UI 인스턴스
            chat_area: 채팅 영역
            status: 상태 표시기
            agent_activity: 에이전트 활동 추적
            
        Returns:
            bool: 처리 성공 여부
        """
        event_type = event.get("type", "")
        
        if event_type == "message":
            return await self._process_message_event(
                event, chat_ui, terminal_ui, chat_area, status, agent_activity
            )
        elif event_type == "workflow_complete":
            status.update(label="Processing complete!", state="complete")
            return True
        elif event_type == "error":
            error_msg = event.get("error", "Unknown error")
            status.update(label=f"Error: {error_msg}", state="error")
            st.error(f"Workflow error: {error_msg}")
            return False
        
        return True
    
    async def _process_message_event(
        self,
        event: Dict[str, Any],
        chat_ui,
        terminal_ui,
        chat_area,
        status,
        agent_activity: Dict[str, int]
    ) -> bool:
        """메시지 이벤트 처리"""
        # 메시지 변환
        frontend_message = self.message_processor.process_cli_event(event)
        
        # 중복 메시지 체크
        if self.message_processor.is_duplicate_message(
            frontend_message, st.session_state.structured_messages
        ):
            return True
        
        # 메시지 저장
        st.session_state.structured_messages.append(frontend_message)
        
        # 로깅 처리
        self._log_message_event(event, frontend_message)
        
        # 에이전트 활동 추적
        agent_name = event.get("agent_name", "Unknown")
        if agent_name not in agent_activity:
            agent_activity[agent_name] = 0
        agent_activity[agent_name] += 1
        
        # 상태 업데이트
        status.update(label="Processing...", state="running")
        
        # UI에 메시지 표시
        with chat_area:
            self._display_message(frontend_message, chat_ui)
        
        # 터미널 메시지 처리 - 수정된 버전
        if frontend_message.get("type") == "tool":
            # terminal_messages 초기화 확인
            if "terminal_messages" not in st.session_state:
                st.session_state.terminal_messages = []
            
            # 터미널 메시지 저장
            st.session_state.terminal_messages.append(frontend_message)
            
            # 직접 터미널 UI에 메시지 추가
            try:
                tool_name = frontend_message.get("tool_display_name", "Tool")
                content = frontend_message.get("content", "")
                
                if tool_name and content:
                    # 명령어와 출력 추가
                    terminal_ui.add_command(tool_name)
                    terminal_ui.add_output(content)
                    
                    # 디버깅 로그
                    if st.session_state.get("debug_mode", False):
                        print(f"Debug - Added to terminal: {tool_name} -> {content[:100]}...")
                        
            except Exception as e:
                if st.session_state.get("debug_mode", False):
                    print(f"Debug - Terminal message processing error: {e}")
        
        return True
    
    def _log_message_event(self, event: Dict[str, Any], frontend_message: Dict[str, Any]):
        """메시지 이벤트 로깅"""
        if "logger" not in st.session_state or not st.session_state.logger:
            return
        
        logger = st.session_state.logger
        agent_name = event.get("agent_name", "Unknown")
        message_type = event.get("message_type", "unknown")
        content = event.get("content", "")
        
        if message_type == "ai":
            logger.log_agent_response(
                agent_name=agent_name,
                content=content,
                tool_calls=frontend_message.get("tool_calls")
            )
        elif message_type == "tool":
            tool_name = event.get("tool_name", "Unknown Tool")
            if "command" in event:  # 도구 명령
                logger.log_tool_command(
                    tool_name=tool_name,
                    command=event.get("command", content)
                )
            else:  # 도구 출력
                logger.log_tool_output(
                    tool_name=tool_name,
                    output=content
                )
    
    def _display_message(self, message: Dict[str, Any], chat_ui):
        """메시지 UI 표시"""
        message_type = message.get("type", "")
        
        if message_type == "ai":
            chat_ui.display_agent_message(message, streaming=True)
        elif message_type == "tool":
            chat_ui.display_tool_message(message)
    
    def _update_agent_status(self, agents_container, chat_ui):
        """에이전트 상태 업데이트"""
        # 최근 이벤트에서 활성 에이전트 찾기
        active_agent = None
        for event in reversed(st.session_state.event_history):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    active_agent = agent_name.lower()
                    break
        
        # 활성 에이전트 업데이트
        if active_agent and active_agent != st.session_state.active_agent:
            if st.session_state.active_agent and st.session_state.active_agent not in st.session_state.completed_agents:
                st.session_state.completed_agents.append(st.session_state.active_agent)
            
            st.session_state.active_agent = active_agent
        
        # 초기 UI 상태 업데이트
        if st.session_state.get("keep_initial_ui", True) and (
            st.session_state.active_agent or st.session_state.completed_agents
        ):
            st.session_state.keep_initial_ui = False
        
        # 에이전트 상태 표시
        chat_ui.display_agent_status(
            agents_container,
            st.session_state.active_agent,
            None,
            st.session_state.completed_agents
        )


# 전역 워크플로우 핸들러 인스턴스
_workflow_handler = None

def get_workflow_handler() -> WorkflowHandler:
    """워크플로우 핸들러 싱글톤 인스턴스 반환"""
    global _workflow_handler
    if _workflow_handler is None:
        _workflow_handler = WorkflowHandler()
    return _workflow_handler
