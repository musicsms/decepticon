"""
Conversation Replay System
저장된 대화 로그를 재현하는 시스템
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime
import logging

from .conversation_logger import ConversationSession, ConversationEvent, EventType

logger = logging.getLogger(__name__)

class ConversationReplay:
    """대화 재현 시스템"""
    
    def __init__(self):
        self.current_replay_session: Optional[ConversationSession] = None
        self.replay_speed = 1.0  # 재생 속도 (1.0 = 원본 속도)
        self.pause_between_events = True
        
    def load_session_for_replay(self, session: ConversationSession) -> bool:
        """재현용 세션 로드"""
        try:
            self.current_replay_session = session
            logger.info(f"Loaded session for replay: {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to load session for replay: {str(e)}")
            return False
    
    async def replay_session(self, session: ConversationSession, 
                           speed: float = 1.0,
                           event_callback: Optional[callable] = None,
                           pause_callback: Optional[callable] = None) -> AsyncGenerator[ConversationEvent, None]:
        """
        세션 전체 재현
        
        Args:
            session: 재현할 세션
            speed: 재생 속도 (1.0 = 원본, 2.0 = 2배속)
            event_callback: 각 이벤트 처리 콜백
            pause_callback: 일시정지 처리 콜백
        """
        if not session.events:
            logger.warning("No events to replay in session")
            return
        
        logger.info(f"Starting replay of session {session.session_id} with {len(session.events)} events")
        
        previous_timestamp = None
        
        for i, event in enumerate(session.events):
            try:
                # 이벤트 간 시간 지연 계산
                if previous_timestamp and self.pause_between_events:
                    current_time = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                    previous_time = datetime.fromisoformat(previous_timestamp.replace('Z', '+00:00'))
                    time_diff = (current_time - previous_time).total_seconds()
                    
                    # 속도 조정된 지연 시간 (최대 5초로 제한)
                    adjusted_delay = min(time_diff / speed, 5.0)
                    if adjusted_delay > 0.1:  # 0.1초 이상인 경우만 지연
                        await asyncio.sleep(adjusted_delay)
                
                # 콜백 호출
                if event_callback:
                    try:
                        await event_callback(event, i, len(session.events))
                    except Exception as e:
                        logger.error(f"Error in event callback: {str(e)}")
                
                # 이벤트 반환
                yield event
                
                # 일시정지 콜백
                if pause_callback:
                    should_pause = await pause_callback(event)
                    if should_pause:
                        logger.info("Replay paused by callback")
                        # 사용자가 계속 진행할 때까지 대기하는 로직을 여기에 구현
                
                previous_timestamp = event.timestamp
                
            except Exception as e:
                logger.error(f"Error replaying event {i}: {str(e)}")
                continue
        
        logger.info(f"Completed replay of session {session.session_id}")
    
    def extract_conversation_flow(self, session: ConversationSession) -> List[Dict[str, Any]]:
        """
        대화 흐름만 추출 (사용자 입력 -> 에이전트 응답 -> 도구 실행)
        """
        conversation_flow = []
        
        current_workflow = None
        
        for event in session.events:
            if event.event_type == EventType.WORKFLOW_START:
                current_workflow = {
                    'user_input': event.content,
                    'timestamp': event.timestamp,
                    'responses': [],
                    'tools_used': []
                }
                
            elif event.event_type == EventType.AGENT_RESPONSE and current_workflow:
                current_workflow['responses'].append({
                    'agent': event.agent_name,
                    'content': event.content,
                    'timestamp': event.timestamp,
                    'execution_time': event.execution_time
                })
                
            elif event.event_type == EventType.TOOL_EXECUTION and current_workflow:
                current_workflow['tools_used'].append({
                    'tool': event.tool_name,
                    'content': event.content,
                    'timestamp': event.timestamp,
                    'execution_time': event.execution_time
                })
                
            elif event.event_type in [EventType.WORKFLOW_COMPLETE, EventType.WORKFLOW_ERROR] and current_workflow:
                current_workflow['status'] = 'completed' if event.event_type == EventType.WORKFLOW_COMPLETE else 'error'
                current_workflow['end_timestamp'] = event.timestamp
                if event.error_message:
                    current_workflow['error'] = event.error_message
                
                conversation_flow.append(current_workflow)
                current_workflow = None
        
        return conversation_flow

class ReplayRenderer:
    """재현 결과를 다양한 형태로 렌더링"""
    
    @staticmethod
    def render_to_markdown(session: ConversationSession) -> str:
        """마크다운 형태로 렌더링"""
        replay = ConversationReplay()
        conversation_flow = replay.extract_conversation_flow(session)
        
        md_content = f"""# Conversation Replay Report
        
## Session Information
- **Session ID**: {session.session_id}
- **User ID**: {session.user_id}  
- **Platform**: {session.platform}
- **Start Time**: {session.start_time}
- **End Time**: {session.end_time or 'Not completed'}
- **Model**: {session.model_info.get('display_name', 'Unknown') if session.model_info else 'Unknown'}
- **Total Messages**: {session.total_messages}
- **Agents Used**: {', '.join(session.agents_used) if session.agents_used else 'None'}

## Conversation Flow

"""
        
        for i, workflow in enumerate(conversation_flow, 1):
            md_content += f"""### Workflow {i}

**User Input**: {workflow['user_input']}

**Agent Responses**:
"""
            
            for resp in workflow['responses']:
                md_content += f"- **{resp['agent']}**: {resp['content'][:200]}{'...' if len(resp['content']) > 200 else ''}\n"
            
            if workflow['tools_used']:
                md_content += f"\n**Tools Used**:\n"
                for tool in workflow['tools_used']:
                    md_content += f"- **{tool['tool']}**: {tool['content'][:100]}{'...' if len(tool['content']) > 100 else ''}\n"
            
            md_content += f"\n**Status**: {workflow['status'].title()}\n\n---\n\n"
        
        return md_content
    
    @staticmethod
    def render_to_json(session: ConversationSession, pretty: bool = True) -> str:
        """JSON 형태로 렌더링"""
        replay = ConversationReplay()
        conversation_flow = replay.extract_conversation_flow(session)
        
        report = {
            'session_info': {
                'session_id': session.session_id,
                'user_id': session.user_id,
                'platform': session.platform,
                'start_time': session.start_time,
                'end_time': session.end_time,
                'model_info': session.model_info,
                'total_messages': session.total_messages,
                'agents_used': session.agents_used
            },
            'conversation_flow': conversation_flow,
            'statistics': {
                'total_workflows': len(conversation_flow),
                'successful_workflows': len([wf for wf in conversation_flow if wf['status'] == 'completed']),
                'failed_workflows': len([wf for wf in conversation_flow if wf['status'] == 'error'])
            }
        }
        
        if pretty:
            return json.dumps(report, indent=2, ensure_ascii=False)
        else:
            return json.dumps(report, ensure_ascii=False)
