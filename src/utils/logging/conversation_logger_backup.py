"""
Decepticon Conversation Logger
대화 로그 기록, 재현, 데이터 수집을 위한 시스템
"""

import json
import uuid
import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class EventType(Enum):
    """이벤트 타입 정의"""
    USER_INPUT = "user_input"
    AGENT_RESPONSE = "agent_response"
    TOOL_EXECUTION = "tool_execution"
    WORKFLOW_START = "workflow_start"
    WORKFLOW_COMPLETE = "workflow_complete"
    WORKFLOW_ERROR = "workflow_error"
    MODEL_CHANGE = "model_change"
    SESSION_START = "session_start"
    SESSION_END = "session_end"

@dataclass
class ConversationEvent:
    """대화 이벤트 데이터 구조"""
    event_id: str
    event_type: EventType
    timestamp: str
    user_id: str
    session_id: str
    thread_id: str
    
    # 메시지 관련
    content: Optional[str] = None
    agent_name: Optional[str] = None
    tool_name: Optional[str] = None
    
    # 메타데이터
    model_info: Optional[Dict[str, Any]] = None
    execution_time: Optional[float] = None
    step_count: Optional[int] = None
    error_message: Optional[str] = None
    
    # 원본 데이터 (재현용)
    raw_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['event_type'] = self.event_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationEvent':
        """딕셔너리에서 생성"""
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)

@dataclass
class ConversationSession:
    """대화 세션 데이터 구조"""
    session_id: str
    user_id: str
    thread_id: str
    start_time: str
    end_time: Optional[str] = None
    
    # 세션 메타데이터
    model_info: Optional[Dict[str, Any]] = None
    platform: str = "unknown"  # "web", "cli"
    version: str = "1.0.0"
    
    # 통계
    total_events: int = 0
    total_messages: int = 0
    total_tools_used: int = 0
    agents_used: List[str] = None
    
    # 이벤트 리스트
    events: List[ConversationEvent] = None
    
    def __post_init__(self):
        if self.agents_used is None:
            self.agents_used = []
        if self.events is None:
            self.events = []
    
    def add_event(self, event: ConversationEvent):
        """이벤트 추가"""
        self.events.append(event)
        self.total_events += 1
        
        # 통계 업데이트
        if event.event_type in [EventType.USER_INPUT, EventType.AGENT_RESPONSE]:
            self.total_messages += 1
        elif event.event_type == EventType.TOOL_EXECUTION:
            self.total_tools_used += 1
        
        if event.agent_name and event.agent_name not in self.agents_used:
            self.agents_used.append(event.agent_name)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        data = asdict(self)
        data['events'] = [event.to_dict() for event in self.events]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationSession':
        """딕셔너리에서 생성"""
        events_data = data.pop('events', [])
        session = cls(**data)
        session.events = [ConversationEvent.from_dict(event_data) for event_data in events_data]
        return session

class ConversationLogger:
    """대화 로거 메인 클래스"""
    
    def __init__(self, base_path: str = "logs"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # 현재 세션
        self.current_session: Optional[ConversationSession] = None
        self.session_start_time: Optional[datetime] = None
        
        # 설정
        self.auto_save = True
        self.compression_enabled = False
        
        logger.info(f"ConversationLogger initialized with base_path: {self.base_path}")
    
    def _get_session_file_path(self, session_id: str) -> Path:
        """세션 파일 경로 생성"""
        # 날짜별 폴더 구조: logs/2025/01/15/session_abc123.json
        date_str = datetime.now().strftime("%Y/%m/%d")
        session_dir = self.base_path / date_str
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"session_{session_id}.json"
    
    def start_session(self, user_id: str, thread_id: str, platform: str = "unknown", 
                     model_info: Optional[Dict[str, Any]] = None) -> str:
        """새 세션 시작"""
        session_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        self.current_session = ConversationSession(
            session_id=session_id,
            user_id=user_id,
            thread_id=thread_id,
            start_time=current_time,
            model_info=model_info,
            platform=platform
        )
        
        self.session_start_time = datetime.now()
        
        # 세션 시작 이벤트 로깅
        self.log_event(
            event_type=EventType.SESSION_START,
            content=f"Session started on {platform}",
            model_info=model_info
        )
        
        logger.info(f"Started new conversation session: {session_id}")
        return session_id
    
    def log_event(self, event_type: EventType, content: Optional[str] = None,
                  agent_name: Optional[str] = None, tool_name: Optional[str] = None,
                  execution_time: Optional[float] = None, step_count: Optional[int] = None,
                  error_message: Optional[str] = None, model_info: Optional[Dict[str, Any]] = None,
                  raw_data: Optional[Dict[str, Any]] = None) -> str:
        """이벤트 로깅"""
        
        if not self.current_session:
            logger.warning("No active session for logging event")
            return None
        
        event_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc).isoformat()
        
        event = ConversationEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=current_time,
            user_id=self.current_session.user_id,
            session_id=self.current_session.session_id,
            thread_id=self.current_session.thread_id,
            content=content,
            agent_name=agent_name,
            tool_name=tool_name,
            model_info=model_info,
            execution_time=execution_time,
            step_count=step_count,
            error_message=error_message,
            raw_data=raw_data
        )
        
        self.current_session.add_event(event)
        
        # 자동 저장
        if self.auto_save:
            self._save_session_async()
        
        logger.debug(f"Logged event: {event_type.value} - {event_id}")
        return event_id
    
    def log_user_input(self, content: str) -> str:
        """사용자 입력 로깅"""
        return self.log_event(
            event_type=EventType.USER_INPUT,
            content=content
        )
    
    def log_agent_response(self, agent_name: str, content: str, 
                          execution_time: Optional[float] = None) -> str:
        """에이전트 응답 로깅"""
        return self.log_event(
            event_type=EventType.AGENT_RESPONSE,
            agent_name=agent_name,
            content=content,
            execution_time=execution_time
        )
    
    def log_tool_execution(self, tool_name: str, content: str, 
                          execution_time: Optional[float] = None) -> str:
        """도구 실행 로깅"""
        return self.log_event(
            event_type=EventType.TOOL_EXECUTION,
            tool_name=tool_name,
            content=content,
            execution_time=execution_time
        )
    
    def log_workflow_start(self, user_input: str) -> str:
        """워크플로우 시작 로깅"""
        return self.log_event(
            event_type=EventType.WORKFLOW_START,
            content=user_input
        )
    
    def log_workflow_complete(self, step_count: int, execution_time: float) -> str:
        """워크플로우 완료 로깅"""
        return self.log_event(
            event_type=EventType.WORKFLOW_COMPLETE,
            content=f"Workflow completed in {step_count} steps",
            execution_time=execution_time,
            step_count=step_count
        )
    
    def log_workflow_error(self, error_message: str) -> str:
        """워크플로우 에러 로깅"""
        return self.log_event(
            event_type=EventType.WORKFLOW_ERROR,
            content="Workflow failed",
            error_message=error_message
        )
    
    def log_model_change(self, old_model: Dict[str, Any], new_model: Dict[str, Any]) -> str:
        """모델 변경 로깅"""
        return self.log_event(
            event_type=EventType.MODEL_CHANGE,
            content=f"Model changed from {old_model.get('display_name')} to {new_model.get('display_name')}",
            model_info=new_model,
            raw_data={"old_model": old_model, "new_model": new_model}
        )
    
    def end_session(self) -> Optional[str]:
        """세션 종료"""
        if not self.current_session:
            return None
        
        session_id = self.current_session.session_id
        end_time = datetime.now(timezone.utc).isoformat()
        self.current_session.end_time = end_time
        
        # 세션 종료 이벤트 로깅
        if self.session_start_time:
            session_duration = (datetime.now() - self.session_start_time).total_seconds()
        else:
            session_duration = None
            
        self.log_event(
            event_type=EventType.SESSION_END,
            content=f"Session ended",
            execution_time=session_duration
        )
        
        # 최종 저장
        self.save_session()
        
        logger.info(f"Ended conversation session: {session_id}")
        self.current_session = None
        self.session_start_time = None
        
        return session_id
    
    def save_session(self) -> bool:
        """세션을 파일로 저장"""
        if not self.current_session:
            return False
        
        try:
            file_path = self._get_session_file_path(self.current_session.session_id)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.current_session.to_dict(), f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Session saved to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            return False
    
    def _save_session_async(self):
        """비동기 세션 저장 (백그라운드)"""
        try:
            self.save_session()
        except Exception as e:
            logger.error(f"Async session save failed: {str(e)}")
    
    def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """세션 로드"""
        try:
            # 세션 파일 찾기 - 더 안전한 방식
            session_file = None
            
            # 먼저 rglob으로 직접 파일 찾기
            for potential_file in self.base_path.rglob(f"session_{session_id}.json"):
                if potential_file.exists():
                    session_file = potential_file
                    break
            
            if not session_file:
                logger.warning(f"Session file not found: {session_id}")
                print(f"[DEBUG] Session file not found for ID: {session_id}")
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            session = ConversationSession.from_dict(session_data)
            logger.info(f"Loaded session: {session_id}")
            print(f"[DEBUG] Successfully loaded session {session_id} with {len(session.events)} events")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {str(e)}")
            print(f"[DEBUG] Failed to load session {session_id}: {str(e)}")
            return None
    
    def list_sessions(self, user_id: Optional[str] = None, 
                     days_back: int = 30) -> List[Dict[str, Any]]:
        """세션 목록 조회"""
        sessions = []
        
        try:
            # 날짜 범위 내의 모든 세션 파일 찾기
            for session_file in self.base_path.rglob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 사용자 필터링
                    if user_id and session_data.get('user_id') != user_id:
                        continue
                    
                    # 세션 요약 정보 추가
                    session_summary = {
                        'session_id': session_data['session_id'],
                        'user_id': session_data['user_id'],
                        'start_time': session_data['start_time'],
                        'end_time': session_data.get('end_time'),
                        'platform': session_data.get('platform', 'unknown'),
                        'total_events': session_data.get('total_events', 0),
                        'total_messages': session_data.get('total_messages', 0),
                        'agents_used': session_data.get('agents_used', []),
                        'model_info': session_data.get('model_info'),
                        'file_path': str(session_file)
                    }
                    
                    sessions.append(session_summary)
                    
                except Exception as e:
                    logger.error(f"Error reading session file {session_file}: {str(e)}")
                    continue
            
            # 시간순 정렬 (최신 순)
            sessions.sort(key=lambda x: x['start_time'], reverse=True)
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {str(e)}")
        
        return sessions
    
    def get_session_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """세션 통계 조회"""
        sessions = self.list_sessions(user_id=user_id)
        
        if not sessions:
            return {
                'total_sessions': 0,
                'total_messages': 0,
                'total_events': 0,
                'unique_agents': [],
                'platforms_used': [],
                'models_used': []
            }
        
        total_messages = sum(s['total_messages'] for s in sessions)
        total_events = sum(s['total_events'] for s in sessions)
        
        unique_agents = set()
        platforms_used = set()
        models_used = set()
        
        for session in sessions:
            unique_agents.update(session.get('agents_used', []))
            platforms_used.add(session.get('platform', 'unknown'))
            if session.get('model_info'):
                model_name = session['model_info'].get('display_name', 'Unknown')
                models_used.add(model_name)
        
        return {
            'total_sessions': len(sessions),
            'total_messages': total_messages,
            'total_events': total_events,
            'unique_agents': list(unique_agents),
            'platforms_used': list(platforms_used),
            'models_used': list(models_used),
            'avg_messages_per_session': total_messages / len(sessions) if sessions else 0
        }

# 전역 로거 인스턴스
_global_logger: Optional[ConversationLogger] = None

def get_conversation_logger() -> ConversationLogger:
    """전역 대화 로거 인스턴스 반환"""
    global _global_logger
    if _global_logger is None:
        _global_logger = ConversationLogger()
    return _global_logger

def set_conversation_logger(logger: ConversationLogger):
    """전역 대화 로거 설정"""
    global _global_logger
    _global_logger = logger
