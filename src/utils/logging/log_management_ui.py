"""
Streamlit 로그 관리 페이지
대화 로그 조회, 재현, 내보내기 기능
"""

import streamlit as st
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import time

# 로깅 시스템 import
from src.utils.logging.conversation_logger import get_conversation_logger
from src.utils.logging.conversation_replay import ConversationReplay, ReplayRenderer
from src.utils.logging.data_collector import get_data_collector

def display_log_management_page():
    """로그 관리 페이지 표시"""
    
    st.title("📊 Conversation Logs")
    st.markdown("대화 로그 조회, 재현, 내보내기 기능")
    
    logger = get_conversation_logger()
    replay_system = ConversationReplay()
    
    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Session List", "🔍 Session Details", "🎬 Replay", "📤 Export"])
    
    with tab1:
        display_session_list(logger)
    
    with tab2:
        display_session_details(logger)
    
    with tab3:
        display_replay_interface(logger, replay_system)
    
    with tab4:
        display_export_interface(logger)

def display_session_list(logger):
    """세션 목록 표시"""
    st.subheader("🗂️ Recent Sessions")
    
    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        days_back = st.selectbox("기간", [1, 7, 30, 90], index=2)
    
    with col2:
        user_filter = st.text_input("사용자 ID 필터 (선택사항)")
    
    with col3:
        platform_filter = st.selectbox("플랫폼", ["All", "web", "cli"], index=0)
    
    # 세션 목록 조회
    try:
        sessions = logger.list_sessions(
            user_id=user_filter if user_filter else None,
            days_back=days_back
        )
        
        # 플랫폼 필터 적용
        if platform_filter != "All":
            sessions = [s for s in sessions if s.get('platform') == platform_filter]
        
        if not sessions:
            st.info("조건에 맞는 세션이 없습니다.")
            return
        
        st.write(f"📊 총 {len(sessions)}개 세션")
        
        # 세션 테이블
        for i, session in enumerate(sessions):
            with st.expander(f"🎯 Session {i+1}: {session['session_id'][:8]}... ({session.get('platform', 'unknown')})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**사용자 ID**: {session['user_id']}")
                    st.write(f"**시작 시간**: {session['start_time']}")
                    st.write(f"**종료 시간**: {session.get('end_time', 'Not completed')}")
                    st.write(f"**플랫폼**: {session.get('platform', 'unknown')}")
                
                with col2:
                    st.write(f"**총 이벤트**: {session.get('total_events', 0)}")
                    st.write(f"**메시지 수**: {session.get('total_messages', 0)}")
                    st.write(f"**사용된 에이전트**: {', '.join(session.get('agents_used', []))}")
                    
                    model_info = session.get('model_info')
                    if model_info:
                        st.write(f"**모델**: {model_info.get('display_name', 'Unknown')}")
                
                # 액션 버튼
                button_col1, button_col2, button_col3 = st.columns(3)
                
                with button_col1:
                    if st.button(f"📋 Details", key=f"details_{session['session_id']}"):
                        st.session_state.selected_session_id = session['session_id']
                        st.rerun()
                
                with button_col2:
                    if st.button(f"🎬 Replay", key=f"replay_{session['session_id']}"):
                        st.session_state.replay_session_id = session['session_id']
                        st.rerun()
                
                with button_col3:
                    if st.button(f"📤 Export", key=f"export_{session['session_id']}"):
                        st.session_state.export_session_id = session['session_id']
                        st.rerun()
        
        # 통계 요약
        st.subheader("📈 Statistics")
        stats = logger.get_session_stats(user_id=user_filter if user_filter else None)
        
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        
        with metric_col1:
            st.metric("Total Sessions", stats['total_sessions'])
        
        with metric_col2:
            st.metric("Total Messages", stats['total_messages'])
        
        with metric_col3:
            st.metric("Total Events", stats['total_events'])
        
        with metric_col4:
            avg_messages = round(stats['avg_messages_per_session'], 1)
            st.metric("Avg Messages/Session", avg_messages)
        
        # 에이전트 및 모델 사용 통계
        if stats['unique_agents']:
            st.write("**사용된 에이전트**:", ", ".join(stats['unique_agents']))
        
        if stats['models_used']:
            st.write("**사용된 모델**:", ", ".join(stats['models_used']))
        
        if stats['platforms_used']:
            st.write("**사용된 플랫폼**:", ", ".join(stats['platforms_used']))
        
    except Exception as e:
        st.error(f"세션 목록 조회 중 오류: {str(e)}")

def display_session_details(logger):
    """세션 상세 정보 표시"""
    st.subheader("🔍 Session Details")
    
    # 세션 선택
    session_id = st.session_state.get('selected_session_id')
    
    if not session_id:
        manual_session_id = st.text_input("세션 ID 입력")
        if st.button("🔍 Load Session") and manual_session_id:
            session_id = manual_session_id
    
    if not session_id:
        st.info("세션을 선택하거나 ID를 입력하세요.")
        return
    
    # 세션 로드
    try:
        session = logger.load_session(session_id)
        
        if not session:
            st.error(f"세션을 찾을 수 없습니다: {session_id}")
            return
        
        # 세션 기본 정보
        st.write(f"**Session ID**: {session.session_id}")
        st.write(f"**User ID**: {session.user_id}")
        st.write(f"**Platform**: {session.platform}")
        st.write(f"**Start Time**: {session.start_time}")
        st.write(f"**End Time**: {session.end_time or 'Not completed'}")
        
        if session.model_info:
            st.write(f"**Model**: {session.model_info.get('display_name', 'Unknown')}")
        
        # 이벤트 타임라인
        st.subheader("📅 Event Timeline")
        
        if not session.events:
            st.info("이 세션에는 이벤트가 없습니다.")
            return
        
        # 이벤트 필터
        event_types = list(set([event.event_type.value for event in session.events]))
        selected_event_types = st.multiselect("이벤트 타입 필터", event_types, default=event_types)
        
        filtered_events = [
            event for event in session.events 
            if event.event_type.value in selected_event_types
        ]
        
        # 이벤트 표시
        for i, event in enumerate(filtered_events):
            timestamp = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
            time_str = timestamp.strftime("%H:%M:%S")
            
            event_icon = get_event_icon(event.event_type.value)
            
            with st.expander(f"{event_icon} {time_str} - {event.event_type.value} ({i+1})"):
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    if event.content:
                        st.write("**Content**:")
                        if len(event.content) > 500:
                            st.text_area("", event.content, height=100, disabled=True)
                        else:
                            st.write(event.content)
                    
                    if event.agent_name:
                        st.write(f"**Agent**: {event.agent_name}")
                    
                    if event.tool_name:
                        st.write(f"**Tool**: {event.tool_name}")
                    
                    if event.error_message:
                        st.error(f"**Error**: {event.error_message}")
                
                with col2:
                    st.write(f"**Event ID**: {event.event_id[:8]}...")
                    st.write(f"**Timestamp**: {time_str}")
                    
                    if event.execution_time:
                        st.write(f"**Execution Time**: {event.execution_time:.2f}s")
                    
                    if event.step_count:
                        st.write(f"**Step Count**: {event.step_count}")
        
        # 대화 흐름 요약
        st.subheader("💬 Conversation Flow")
        replay = ConversationReplay()
        conversation_flow = replay.extract_conversation_flow(session)
        
        if conversation_flow:
            for i, workflow in enumerate(conversation_flow, 1):
                with st.expander(f"🔄 Workflow {i}: {workflow['user_input'][:50]}..."):
                    st.write(f"**User Input**: {workflow['user_input']}")
                    
                    if workflow['responses']:
                        st.write("**Agent Responses**:")
                        for resp in workflow['responses']:
                            st.write(f"- **{resp['agent']}**: {resp['content'][:100]}...")
                    
                    if workflow['tools_used']:
                        st.write("**Tools Used**:")
                        for tool in workflow['tools_used']:
                            st.write(f"- **{tool['tool']}**: {tool['content'][:50]}...")
                    
                    status_color = "🟢" if workflow['status'] == 'completed' else "🔴"
                    st.write(f"**Status**: {status_color} {workflow['status'].title()}")
        else:
            st.info("대화 흐름을 찾을 수 없습니다.")
        
    except Exception as e:
        st.error(f"세션 상세 정보 로드 중 오류: {str(e)}")

def get_event_icon(event_type):
    """이벤트 타입별 아이콘 반환"""
    icons = {
        "user_input": "👤",
        "agent_response": "🤖",
        "tool_execution": "🛠️",
        "workflow_start": "🚀",
        "workflow_complete": "✅",
        "workflow_error": "❌",
        "model_change": "🔄",
        "session_start": "🎬",
        "session_end": "🏁"
    }
    return icons.get(event_type, "📝")

def display_replay_interface(logger, replay_system):
    """재현 인터페이스 표시"""
    st.subheader("🎬 Session Replay")
    st.info("재현 기능은 현재 개발 중입니다.")

def display_export_interface(logger):
    """내보내기 인터페이스 표시"""
    st.subheader("📤 Export Sessions")
    st.info("내보내기 기능은 현재 개발 중입니다.")

if __name__ == "__main__":
    display_log_management_page()
