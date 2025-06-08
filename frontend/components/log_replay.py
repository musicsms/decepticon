"""
로그 재현 유틸리티
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import streamlit as st

from src.utils.logging.conversation_logger import (
    ConversationSession,
    ConversationEvent,
    EventType
)


class LogReplayUtility:
    """로그 재현 유틸리티 클래스"""
    
    @staticmethod
    def load_session_from_file(file_path: str) -> Optional[ConversationSession]:
        """파일에서 세션 로드"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            return ConversationSession.from_dict(session_data)
        except Exception as e:
            print(f"Error loading session from {file_path}: {str(e)}")
            return None
    
    @staticmethod
    def export_session_to_html(session: ConversationSession, output_path: str) -> bool:
        """세션을 HTML 보고서로 내보내기"""
        try:
            html_content = LogReplayUtility._generate_html_report(session)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            print(f"Error exporting to HTML: {str(e)}")
            return False
    
    @staticmethod
    def _generate_html_report(session: ConversationSession) -> str:
        """HTML 보고서 생성"""
        # 기본 HTML 템플릿
        html_template = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Decepticon Session Report - {session_id}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #e74c3c;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .title {{
            color: #e74c3c;
            font-size: 2.5em;
            margin: 0;
            font-weight: bold;
        }}
        .subtitle {{
            color: #666;
            font-size: 1.2em;
            margin: 10px 0;
        }}
        .meta-info {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }}
        .meta-item {{
            text-align: center;
        }}
        .meta-label {{
            font-weight: bold;
            color: #333;
            display: block;
            margin-bottom: 5px;
        }}
        .meta-value {{
            color: #e74c3c;
            font-size: 1.2em;
        }}
        .timeline {{
            margin: 30px 0;
        }}
        .event {{
            margin: 20px 0;
            padding: 20px;
            border-left: 4px solid #e74c3c;
            background: #f8f9fa;
            border-radius: 0 8px 8px 0;
        }}
        .event-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .event-type {{
            font-weight: bold;
            color: #e74c3c;
            font-size: 1.1em;
        }}
        .event-timestamp {{
            color: #666;
            font-size: 0.9em;
        }}
        .event-content {{
            margin: 10px 0;
            padding: 15px;
            background: white;
            border-radius: 6px;
            border: 1px solid #ddd;
        }}
        .agent-name {{
            color: #2c3e50;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .tool-name {{
            color: #27ae60;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .code-block {{
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 6px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }}
        .error {{
            background: #ffebee;
            border-left-color: #f44336;
        }}
        .success {{
            background: #e8f5e8;
            border-left-color: #4caf50;
        }}
        .warning {{
            background: #fff3e0;
            border-left-color: #ff9800;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        .stat-card {{
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #e74c3c;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1 class="title">🛡️ Decepticon Session Report</h1>
            <p class="subtitle">Red Team Testing Session Analysis</p>
        </div>
        
        <div class="meta-info">
            <div class="meta-item">
                <span class="meta-label">Session ID</span>
                <div class="meta-value">{session_id_short}</div>
            </div>
            <div class="meta-item">
                <span class="meta-label">Platform</span>
                <div class="meta-value">{platform}</div>
            </div>
            <div class="meta-item">
                <span class="meta-label">Start Time</span>
                <div class="meta-value">{start_time}</div>
            </div>
            <div class="meta-item">
                <span class="meta-label">Duration</span>
                <div class="meta-value">{duration}</div>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_events}</div>
                <div class="stat-label">Total Events</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_messages}</div>
                <div class="stat-label">Messages</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_tools}</div>
                <div class="stat-label">Tools Used</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{unique_agents}</div>
                <div class="stat-label">Agents</div>
            </div>
        </div>
        
        {model_info}
        
        <div class="timeline">
            <h2>📋 Event Timeline</h2>
            {events_html}
        </div>
    </div>
</body>
</html>
        """
        
        # 데이터 준비
        session_id_short = session.session_id[:16] + "..."
        platform = session.platform.upper()
        start_time = session.start_time[:19].replace('T', ' ')
        
        # 지속 시간 계산
        if session.end_time:
            try:
                start_dt = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(session.end_time.replace('Z', '+00:00'))
                duration = str(end_dt - start_dt).split('.')[0]
            except:
                duration = "Unknown"
        else:
            duration = "In Progress"
        
        # 통계 계산
        unique_agents = len(set(e.agent_name for e in session.events if e.agent_name))
        
        # 모델 정보
        model_info_html = ""
        if session.model_info:
            model_info_html = f"""
        <div class="meta-info">
            <div class="meta-item">
                <span class="meta-label">AI Model</span>
                <div class="meta-value">{session.model_info.get('display_name', 'Unknown')}</div>
            </div>
            <div class="meta-item">
                <span class="meta-label">Provider</span>
                <div class="meta-value">{session.model_info.get('provider', 'Unknown')}</div>
            </div>
        </div>
            """
        
        # 이벤트 HTML 생성
        events_html = ""
        for i, event in enumerate(session.events, 1):
            timestamp = event.timestamp[:19].replace('T', ' ')
            
            # 이벤트 타입별 스타일 및 내용
            event_class = ""
            event_icon = "📝"
            
            if event.event_type == EventType.USER_INPUT:
                event_icon = "👤"
                event_class = ""
            elif event.event_type == EventType.AGENT_RESPONSE:
                event_icon = "🤖"
                event_class = ""
            elif event.event_type == EventType.TOOL_EXECUTION:
                event_icon = "🔧"
                event_class = ""
            elif event.event_type == EventType.WORKFLOW_START:
                event_icon = "🚀"
                event_class = "success"
            elif event.event_type == EventType.WORKFLOW_COMPLETE:
                event_icon = "✅"
                event_class = "success"
            elif event.event_type == EventType.WORKFLOW_ERROR:
                event_icon = "❌"
                event_class = "error"
            
            # 이벤트 내용 처리
            content_html = ""
            if event.agent_name:
                content_html += f'<div class="agent-name">🤖 Agent: {event.agent_name}</div>'
            if event.tool_name:
                content_html += f'<div class="tool-name">🔧 Tool: {event.tool_name}</div>'
            
            if event.content:
                if event.event_type == EventType.TOOL_EXECUTION:
                    content_html += f'<div class="code-block">{event.content}</div>'
                else:
                    content_html += f'<div class="event-content">{event.content.replace(chr(10), "<br>")}</div>'
            
            if event.error_message:
                content_html += f'<div class="event-content error">❌ Error: {event.error_message}</div>'
            
            events_html += f"""
            <div class="event {event_class}">
                <div class="event-header">
                    <span class="event-type">{event_icon} {event.event_type.name.replace('_', ' ').title()}</span>
                    <span class="event-timestamp">{timestamp}</span>
                </div>
                {content_html}
            </div>
            """
        
        # HTML 완성
        return html_template.format(
            session_id=session.session_id,
            session_id_short=session_id_short,
            platform=platform,
            start_time=start_time,
            duration=duration,
            total_events=session.total_events,
            total_messages=session.total_messages,
            total_tools=session.total_tools_used,
            unique_agents=unique_agents,
            model_info=model_info_html,
            events_html=events_html
        )
    
    @staticmethod
    def find_sessions_by_criteria(
        base_path: str, 
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        model_name: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """조건에 맞는 세션 검색"""
        results = []
        base_path = Path(base_path)
        
        try:
            for session_file in base_path.rglob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 필터링 조건 적용
                    if user_id and session_data.get('user_id') != user_id:
                        continue
                    
                    if agent_name and agent_name not in session_data.get('agents_used', []):
                        continue
                    
                    if model_name and session_data.get('model_info', {}).get('display_name') != model_name:
                        continue
                    
                    # 날짜 필터링 (기본 구현)
                    if date_from or date_to:
                        session_date = session_data.get('start_time', '')[:10]
                        if date_from and session_date < date_from:
                            continue
                        if date_to and session_date > date_to:
                            continue
                    
                    # 결과에 추가
                    results.append({
                        'file_path': str(session_file),
                        'session_id': session_data['session_id'],
                        'user_id': session_data['user_id'],
                        'start_time': session_data['start_time'],
                        'platform': session_data.get('platform', 'unknown'),
                        'total_events': session_data.get('total_events', 0),
                        'total_messages': session_data.get('total_messages', 0),
                        'agents_used': session_data.get('agents_used', []),
                        'model_info': session_data.get('model_info', {})
                    })
                    
                except Exception as e:
                    print(f"Error reading session file {session_file}: {str(e)}")
                    continue
            
            # 시간순 정렬
            results.sort(key=lambda x: x['start_time'], reverse=True)
            
        except Exception as e:
            print(f"Error searching sessions: {str(e)}")
        
        return results
    
    @staticmethod
    def compare_sessions(session1: ConversationSession, session2: ConversationSession) -> Dict[str, Any]:
        """두 세션 비교 분석"""
        comparison = {
            'session1_id': session1.session_id,
            'session2_id': session2.session_id,
            'differences': {},
            'similarities': {},
            'analysis': {}
        }
        
        # 기본 통계 비교
        comparison['differences']['events'] = session1.total_events - session2.total_events
        comparison['differences']['messages'] = session1.total_messages - session2.total_messages
        comparison['differences']['tools'] = session1.total_tools_used - session2.total_tools_used
        
        # 에이전트 사용 비교
        agents1 = set(session1.agents_used or [])
        agents2 = set(session2.agents_used or [])
        
        comparison['similarities']['common_agents'] = list(agents1.intersection(agents2))
        comparison['differences']['unique_agents_session1'] = list(agents1 - agents2)
        comparison['differences']['unique_agents_session2'] = list(agents2 - agents1)
        
        # 모델 비교
        model1 = session1.model_info.get('display_name', 'Unknown') if session1.model_info else 'Unknown'
        model2 = session2.model_info.get('display_name', 'Unknown') if session2.model_info else 'Unknown'
        
        comparison['analysis']['same_model'] = model1 == model2
        comparison['analysis']['model1'] = model1
        comparison['analysis']['model2'] = model2
        
        # 플랫폼 비교
        comparison['analysis']['same_platform'] = session1.platform == session2.platform
        comparison['analysis']['platform1'] = session1.platform
        comparison['analysis']['platform2'] = session2.platform
        
        return comparison
