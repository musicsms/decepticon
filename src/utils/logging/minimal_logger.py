"""
최소한의 로거 - 재현에 필요한 정보만 기록
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    """재현에 필요한 최소한의 이벤트 타입"""
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    TOOL_COMMAND = "tool_command"
    TOOL_OUTPUT = "tool_output"

@dataclass
class MinimalEvent:
    """재현에 필요한 최소한의 이벤트 정보"""
    event_type: EventType
    timestamp: str
    content: str
    agent_name: Optional[str] = None  # agent_response에만 사용
    tool_name: Optional[str] = None   # tool_command, tool_output에만 사용
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "content": self.content
        }
        if self.agent_name:
            result["agent_name"] = self.agent_name
        if self.tool_name:
            result["tool_name"] = self.tool_name
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MinimalEvent':
        return cls(
            event_type=EventType(data["event_type"]),
            timestamp=data["timestamp"],
            content=data["content"],
            agent_name=data.get("agent_name"),
            tool_name=data.get("tool_name")
        )

@dataclass
class MinimalSession:
    """재현에 필요한 최소한의 세션 정보"""
    session_id: str
    start_time: str
    events: List[MinimalEvent]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "start_time": self.start_time,
            "events": [event.to_dict() for event in self.events]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MinimalSession':
        return cls(
            session_id=data["session_id"],
            start_time=data["start_time"],
            events=[MinimalEvent.from_dict(e) for e in data["events"]]
        )

class MinimalLogger:
    """최소한의 로거 - 재현에 필요한 정보만 기록"""
    
    def __init__(self, base_path: str = "logs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        self.current_session: Optional[MinimalSession] = None
    
    def _get_session_file_path(self, session_id: str) -> Path:
        """세션 파일 경로 생성"""
        date_str = datetime.now().strftime("%Y/%m/%d")
        session_dir = self.base_path / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"session_{session_id}.json"
    
    def start_session(self) -> str:
        """새 세션 시작"""
        session_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()
        
        self.current_session = MinimalSession(
            session_id=session_id,
            start_time=start_time,
            events=[]
        )
        return session_id
    
    def log_user_input(self, content: str):
        """사용자 입력 로깅"""
        if self.current_session:
            event = MinimalEvent(
                event_type=EventType.USER_INPUT,
                timestamp=datetime.now().isoformat(),
                content=content
            )
            self.current_session.events.append(event)
    
    def log_agent_response(self, agent_name: str, content: str):
        """에이전트 응답 로깅"""
        if self.current_session:
            event = MinimalEvent(
                event_type=EventType.AGENT_RESPONSE,
                timestamp=datetime.now().isoformat(),
                content=content,
                agent_name=agent_name
            )
            self.current_session.events.append(event)
    
    def log_tool_command(self, tool_name: str, command: str):
        """도구 명령 로깅"""
        if self.current_session:
            event = MinimalEvent(
                event_type=EventType.TOOL_COMMAND,
                timestamp=datetime.now().isoformat(),
                content=command,
                tool_name=tool_name
            )
            self.current_session.events.append(event)
    
    def log_tool_output(self, tool_name: str, output: str):
        """도구 출력 로깅"""
        if self.current_session:
            event = MinimalEvent(
                event_type=EventType.TOOL_OUTPUT,
                timestamp=datetime.now().isoformat(),
                content=output,
                tool_name=tool_name
            )
            self.current_session.events.append(event)
    
    def save_session(self) -> bool:
        """세션 저장"""
        if not self.current_session:
            return False
        
        try:
            file_path = self._get_session_file_path(self.current_session.session_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
    
    def end_session(self) -> Optional[str]:
        """세션 종료"""
        if not self.current_session:
            return None
        
        session_id = self.current_session.session_id
        self.save_session()
        self.current_session = None
        return session_id
    
    def load_session(self, session_id: str) -> Optional[MinimalSession]:
        """세션 로드"""
        try:
            for session_file in self.base_path.rglob(f"session_{session_id}.json"):
                if session_file.exists():
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    return MinimalSession.from_dict(session_data)
            return None
        except Exception as e:
            print(f"Failed to load session {session_id}: {e}")
            return None
    
    def list_sessions(self, limit: int = 20) -> List[Dict[str, Any]]:
        """세션 목록 조회"""
        sessions = []
        
        try:
            for session_file in self.base_path.rglob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 기본 정보만 추출
                    session_info = {
                        'session_id': session_data['session_id'],
                        'start_time': session_data['start_time'],
                        'event_count': len(session_data.get('events', [])),
                        'file_path': str(session_file)
                    }
                    
                    # 첫 번째 사용자 입력으로 미리보기 생성
                    events = session_data.get('events', [])
                    preview = "No user input found"
                    for event in events:
                        if event.get('event_type') == 'user_input':
                            preview = event.get('content', '')[:100]
                            if len(preview) < len(event.get('content', '')):
                                preview += "..."
                            break
                    
                    session_info['preview'] = preview
                    sessions.append(session_info)
                    
                except Exception as e:
                    continue
            
            # 시간순 정렬 (최신 순)
            sessions.sort(key=lambda x: x['start_time'], reverse=True)
            
        except Exception as e:
            print(f"Error listing sessions: {e}")
        
        return sessions[:limit]

# 전역 인스턴스
_minimal_logger: Optional[MinimalLogger] = None

def get_minimal_logger() -> MinimalLogger:
    """전역 최소 로거 인스턴스 반환"""
    global _minimal_logger
    if _minimal_logger is None:
        _minimal_logger = MinimalLogger()
    return _minimal_logger
