"""
CLI Message Processor - CLI의 메시지 처리 로직을 프론트엔드용으로 래핑
CLI와 완전히 동일한 방식으로 단순화
"""

from datetime import datetime
from typing import Dict, Any, List

# CLI 메시지 유틸리티 직접 import
from src.utils.message import (
    extract_message_content,
    get_message_type,
    get_agent_name,
    parse_tool_name
)


class CLIMessageProcessor:
    """CLI 메시지 처리 로직을 프론트엔드용으로 래핑하는 클래스 - CLI와 완전히 동일"""
    
    def __init__(self):
        # 에이전트 아바타 - 동적으로 관리
        self.agent_avatars = {
            "planner": "🧠",
            "reconnaissance": "🔍", 
            "initial_access": "🔑",
            "execution": "💻",
            "persistence": "🔐",
            "privilege_escalation": "🔒",
            "defense_evasion": "🕵️",
            "summary": "📋",
        }
        
        # 기본 아바타
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
        display_name = self._get_agent_display_name(agent_name)
        avatar = self._get_agent_avatar(agent_name)
        
        if message_type == "ai":
            # AI 메시지를 프론트엔드 에이전트 메시지로 변환
            return {
                "type": "ai",
                "agent_id": agent_name.lower(),
                "display_name": display_name,
                "avatar": avatar,
                "content": content,
                "id": f"ai_{agent_name.lower()}_{hash(content[:100])}_{datetime.now().timestamp()}"
            }
        
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
    
    def _get_agent_display_name(self, agent_name: str) -> str:
        """에이전트 표시 이름 생성 - CLI와 동일"""
        if not agent_name or agent_name == "Unknown":
            return "Unknown Agent"
        
        # CLI에서 오는 이름을 그대로 사용하되, 포맷팅만 적용
        # snake_case를 Title Case로 변환
        if "_" in agent_name:
            return agent_name.replace("_", " ").title()
        
        # 첫 글자만 대문자로
        return agent_name.capitalize()
    
    def _get_agent_avatar(self, agent_name: str) -> str:
        """에이전트 아바타 반환 - 동적 매칭"""
        if not agent_name:
            return self.default_avatar
        
        # 소문자로 변환해서 매칭
        agent_key = agent_name.lower()
        
        # 부분 매칭으로 아바타 찾기
        for key, avatar in self.agent_avatars.items():
            if key in agent_key or agent_key in key:
                return avatar
        
        return self.default_avatar
    
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