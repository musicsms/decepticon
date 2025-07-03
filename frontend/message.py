"""
CLI Message Processor - CLI의 메시지 처리 로직을 프론트엔드용으로 래핑
CLI와 완전히 동일한 방식으로 단순화
"""

from datetime import datetime
from typing import Dict, Any, List

# CLI 메시지 유틸리티 직접 import
from src.utils.message import parse_tool_name, extract_tool_calls
# 리팩토링된 에이전트 관리자
from src.utils.agents import AgentManager


class CLIMessageProcessor:
    """CLI 메시지 처리 로직을 프론트엔드용으로 래핑하는 클래스 - CLI와 완전히 동일"""
    
    def __init__(self):
        # 기본 아바타 (리팩토링된 모듈에서 관리)
        self.default_avatar = "🤖"
    
    def process_cli_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        CLI에서 온 이벤트 데이터를 프론트엔드 메시지 형식으로 변환
        CLI와 완전히 동일한 방식
        """
        message_type = event_data.get("message_type", "")
        agent_name = event_data.get("agent_name", "Unknown")
        content = event_data.get("content", "")
        raw_message = event_data.get("raw_message")
        
        # 에이전트 표시 정보 생성
        display_name = AgentManager.get_display_name(agent_name)
        avatar = AgentManager.get_avatar(agent_name)
        
        if message_type == "ai":
            # AI 메시지를 프론트엔드 에이전트 메시지로 변환
            frontend_message = {
                "type": "ai",
                "agent_id": agent_name.lower(),
                "display_name": display_name,
                "avatar": avatar,
                "content": content,
                "id": f"ai_{agent_name.lower()}_{hash(content[:100])}_{datetime.now().timestamp()}"
            }
            
            # Tool calls 정보 추출 - 새로 만든 유틸리티 함수 사용
            tool_calls = extract_tool_calls(raw_message, event_data)
            if tool_calls:
                frontend_message["tool_calls"] = tool_calls
            
            return frontend_message
        
        elif message_type == "tool":
            # 도구 메시지 - CLI와 동일하게 단순 처리
            tool_name = event_data.get("tool_name", "Unknown Tool")
            tool_display_name = event_data.get("tool_display_name", parse_tool_name(tool_name))
            
            return {
                "type": "tool",
                "tool_name": tool_name,
                "tool_display_name": tool_display_name,
                "content": content,
                "id": f"tool_{tool_name}_{hash(content[:100])}_{datetime.now().timestamp()}"
            }
        
        elif message_type == "user":
            # 사용자 메시지
            return {
                "type": "user",
                "content": content,
                "id": f"user_{hash(content)}_{datetime.now().timestamp()}"
            }
        
        # 기본 메시지 - AI로 처리
        return {
            "type": "ai",
            "agent_id": agent_name.lower(),
            "display_name": display_name,
            "avatar": avatar,
            "content": content,
            "id": f"ai_{agent_name.lower()}_{hash(content[:100])}_{datetime.now().timestamp()}"
        }
    
    def _create_user_message(self, content: str) -> Dict[str, Any]:
        """사용자 메시지 생성 - CLI와 동일"""
        return {
            "type": "user",
            "content": content,
            "id": f"user_{hash(content)}_{datetime.now().timestamp()}"
        }
    


    def extract_agent_status(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """이벤트들에서 에이전트 상태 정보 추출 - CLI와 동일"""
        status = {
            "active_agent": None,
            "completed_agents": [],
            "current_step": 0
        }
        
        # 최근 이벤트에서 활성 에이전트 찾기
        for event in reversed(events):
            if event.get("type") == "message" and event.get("message_type") == "ai":
                agent_name = event.get("agent_name")
                if agent_name and agent_name != "Unknown":
                    status["active_agent"] = agent_name.lower()
                    break
        
        # 총 스텝 수 계산
        status["current_step"] = len([e for e in events if e.get("type") == "message"])
        
        return status
    
    def is_duplicate_message(self, new_message: Dict[str, Any], existing_messages: List[Dict[str, Any]]) -> bool:
        """메시지 중복 검사 - CLI와 동일"""
        new_id = new_message.get("id")
        if not new_id:
            return False
        
        # ID 기반 중복 검사
        for msg in existing_messages:
            if msg.get("id") == new_id:
                return True
        
        # 내용 기반 중복 검사 (같은 에이전트의 같은 내용)
        new_agent = new_message.get("agent_id")
        new_content = new_message.get("content", "")
        
        for msg in existing_messages:
            if (msg.get("agent_id") == new_agent and 
                msg.get("type") == new_message.get("type") and
                msg.get("content") == new_content):
                return True
        
        return False