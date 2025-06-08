"""
로그 관리 UI 컴포넌트
"""

import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import time

from src.utils.logging.conversation_logger import (
    get_conversation_logger,
    ConversationSession,
    EventType
)


class LogManagerUI:
    """로그 관리 UI 클래스"""
    
    def __init__(self):
        self.logger = get_conversation_logger()
        
    def display_log_overview(self, container):
        """로그 개요 표시"""
        with container:
            st.subheader("📊 Log Overview")
            
            # 현재 세션 정보
            if self.logger.current_session:
                current_session = self.logger.current_session
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Session", "Active", delta="Running")
                with col2:
                    st.metric("Total Events", current_session.total_events)
                with col3:
                    st.metric("Total Messages", current_session.total_messages)
                
                # 현재 세션 상세 정보
                with st.expander("Current Session Details", expanded=False):
                    session_info = {
                        "Session ID": current_session.session_id[:16] + "...",
                        "User ID": current_session.user_id,
                        "Platform": current_session.platform,
                        "Start Time": current_session.start_time,
                        "Agents Used": ", ".join(current_session.agents_used) if current_session.agents_used else "None",
                        "Model": current_session.model_info.get('display_name', 'Unknown') if current_session.model_info else "Unknown"
                    }
                    
                    for key, value in session_info.items():
                        st.text(f"{key}: {value}")
            else:
                st.info("No active session")
    
    def display_session_history(self, container, user_id: Optional[str] = None):
        """세션 히스토리 표시"""
        with container:
            st.subheader("📅 Session History")
            
            # 필터 옵션
            col1, col2 = st.columns(2)
            with col1:
                days_back = st.selectbox("Time Range", [7, 30, 90, 365], index=0, key="log_days_back")
            with col2:
                show_platform = st.selectbox("Platform", ["All", "web", "cli"], key="log_platform_filter")
            
            # 세션 목록 가져오기
            sessions = self.logger.list_sessions(user_id=user_id, days_back=days_back)
            
            # 플랫폼 필터 적용
            if show_platform != "All":
                sessions = [s for s in sessions if s.get('platform') == show_platform]
            
            if not sessions:
                st.info("No sessions found for the selected criteria")
                return
            
            # 세션 테이블 생성
            session_data = []
            for session in sessions[:20]:  # 최대 20개만 표시
                start_time = session['start_time'][:19].replace('T', ' ')
                duration = "Unknown"
                if session.get('end_time'):
                    try:
                        start_dt = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(session['end_time'].replace('Z', '+00:00'))
                        duration = str(end_dt - start_dt).split('.')[0]  # 초 단위 제거
                    except:
                        duration = "Unknown"
                
                session_data.append({
                    "Session ID": session['session_id'][:8] + "...",
                    "Start Time": start_time,
                    "Platform": session.get('platform', 'Unknown'),
                    "Messages": session.get('total_messages', 0),
                    "Events": session.get('total_events', 0),
                    "Agents": ", ".join(session.get('agents_used', [])) if session.get('agents_used') else "None",
                    "Model": session.get('model_info', {}).get('display_name', 'Unknown') if session.get('model_info') else "Unknown",
                    "Duration": duration,
                    "Full ID": session['session_id']  # 숨겨진 전체 ID
                })
            
            # 데이터프레임으로 표시
            df = pd.DataFrame(session_data)
            
            # 선택 가능한 테이블
            event = st.dataframe(
                df.drop('Full ID', axis=1),  # Full ID는 숨김
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # 빠른 액세스 버튼 추가
            st.markdown("**💡 Tip:** Click on a row above to view session details with replay functionality")
            
            # 세션 선택 처리
            if event.selection.rows:
                selected_idx = event.selection.rows[0]
                selected_session_id = session_data[selected_idx]["Full ID"]
                
                # 세션 상세 정보 표시
                st.divider()
                st.markdown(f"### 📋 Selected Session: {session_data[selected_idx]['Session ID']}")
                self.display_session_details(selected_session_id)
    
    def display_session_details(self, session_id: str):
        """선택된 세션의 상세 정보 표시"""
        st.subheader(f"📋 Session Details: {session_id[:16]}...")
        
        # 세션 로드
        session = self.logger.load_session(session_id)
        if not session:
            st.error("Failed to load session")
            return
        
        # 기본 정보
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Events", session.total_events)
            st.metric("Total Messages", session.total_messages)
        with col2:
            st.metric("Tools Used", session.total_tools_used)
            st.metric("Agents", len(session.agents_used) if session.agents_used else 0)
        
        # 탭으로 구분
        tab1, tab2, tab3, tab4 = st.tabs(["🔄 Replay", "📝 Events", "📊 Statistics", "💾 Export"])
        
        with tab1:
            self.display_session_replay(session)
        
        with tab2:
            self.display_session_events(session)
            
        with tab3:
            self.display_session_statistics(session)
            
        with tab4:
            self.display_export_options(session)
    
    def display_session_replay(self, session: ConversationSession):
        """세션 재생 기능"""
        st.subheader("🎬 Session Replay")
        
        if not session.events:
            st.info("No events to replay")
            return
        
        # 재생 컨트롤
        col1, col2, col3 = st.columns(3)
        with col1:
            auto_play = st.checkbox("Auto Play", key=f"replay_auto_{session.session_id}")
        with col2:
            speed = st.slider("Speed", 0.1, 3.0, 1.0, key=f"replay_speed_{session.session_id}")
        with col3:
            show_timestamps = st.checkbox("Show Timestamps", True, key=f"replay_timestamps_{session.session_id}")
        
        # 이벤트 슬라이더
        if len(session.events) > 1:
            current_event_idx = st.slider(
                "Event", 0, len(session.events) - 1, 0,
                key=f"replay_slider_{session.session_id}"
            )
        else:
            current_event_idx = 0
        
        # 재생 버튼들
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("⏮️ First", key=f"replay_first_{session.session_id}"):
                st.session_state[f"replay_slider_{session.session_id}"] = 0
                st.rerun()
        with col2:
            if st.button("⏪ Previous", key=f"replay_prev_{session.session_id}"):
                if current_event_idx > 0:
                    st.session_state[f"replay_slider_{session.session_id}"] = current_event_idx - 1
                    st.rerun()
        with col3:
            if st.button("⏩ Next", key=f"replay_next_{session.session_id}"):
                if current_event_idx < len(session.events) - 1:
                    st.session_state[f"replay_slider_{session.session_id}"] = current_event_idx + 1
                    st.rerun()
        with col4:
            if st.button("⏭️ Last", key=f"replay_last_{session.session_id}"):
                st.session_state[f"replay_slider_{session.session_id}"] = len(session.events) - 1
                st.rerun()
        
        st.divider()
        
        # 현재 이벤트까지의 재생
        replay_container = st.container()
        with replay_container:
            st.markdown("### 🎥 Conversation Replay")
            
            # 현재 이벤트까지만 표시
            events_to_show = session.events[:current_event_idx + 1]
            
            for i, event in enumerate(events_to_show):
                self._display_replay_event(event, i, show_timestamps)
        
        # 자동 재생
        if auto_play and current_event_idx < len(session.events) - 1:
            time.sleep(1.0 / speed)
            st.session_state[f"replay_slider_{session.session_id}"] = current_event_idx + 1
            st.rerun()
    
    def _display_replay_event(self, event, index: int, show_timestamps: bool):
        """재생용 이벤트 표시"""
        timestamp_str = ""
        if show_timestamps:
            try:
                dt = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                timestamp_str = f" • {dt.strftime('%H:%M:%S')}"
            except:
                timestamp_str = f" • {event.timestamp[:19]}"
        
        if event.event_type == EventType.USER_INPUT:
            st.chat_message("user").write(f"**User{timestamp_str}**\n\n{event.content}")
            
        elif event.event_type == EventType.AGENT_RESPONSE:
            agent_name = event.agent_name or "Agent"
            st.chat_message("assistant").write(f"**{agent_name}{timestamp_str}**\n\n{event.content}")
            
        elif event.event_type == EventType.TOOL_EXECUTION:
            tool_name = event.tool_name or "Tool"
            with st.chat_message("assistant"):
                st.write(f"**🔧 {tool_name}{timestamp_str}**")
                st.code(event.content)
                
        elif event.event_type == EventType.WORKFLOW_START:
            st.info(f"🚀 Workflow Started{timestamp_str}: {event.content}")
            
        elif event.event_type == EventType.WORKFLOW_COMPLETE:
            st.success(f"✅ Workflow Completed{timestamp_str}")
            
        elif event.event_type == EventType.WORKFLOW_ERROR:
            st.error(f"❌ Workflow Error{timestamp_str}: {event.error_message}")
    
    def display_session_events(self, session: ConversationSession):
        """세션 이벤트 목록 표시"""
        st.subheader("📝 Event List")
        
        if not session.events:
            st.info("No events found")
            return
        
        # 이벤트 필터
        event_types = [e.name for e in EventType]
        selected_types = st.multiselect(
            "Filter by Event Type",
            event_types,
            default=event_types,
            key=f"events_filter_{session.session_id}"
        )
        
        # 필터링된 이벤트
        filtered_events = [
            e for e in session.events 
            if e.event_type.name in selected_types
        ]
        
        # 이벤트 테이블
        event_data = []
        for i, event in enumerate(filtered_events):
            timestamp = event.timestamp[:19].replace('T', ' ')
            
            event_data.append({
                "#": i + 1,
                "Time": timestamp,
                "Type": event.event_type.name,
                "Agent": event.agent_name or "-",
                "Tool": event.tool_name or "-",
                "Content": (event.content[:50] + "...") if event.content and len(event.content) > 50 else (event.content or "-")
            })
        
        if event_data:
            df = pd.DataFrame(event_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No events match the selected filters")
    
    def display_session_statistics(self, session: ConversationSession):
        """세션 통계 표시"""
        st.subheader("📊 Session Statistics")
        
        # 기본 통계
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Duration", self._calculate_session_duration(session))
            st.metric("Events per Minute", self._calculate_events_per_minute(session))
            
        with col2:
            st.metric("Unique Agents", len(set(e.agent_name for e in session.events if e.agent_name)))
            st.metric("Tool Executions", len([e for e in session.events if e.event_type == EventType.TOOL_EXECUTION]))
        
        # 이벤트 타입별 분포
        event_counts = {}
        for event in session.events:
            event_type = event.event_type.name
            event_counts[event_type] = event_counts.get(event_type, 0) + 1
        
        if event_counts:
            st.subheader("Event Type Distribution")
            chart_data = pd.DataFrame(
                list(event_counts.items()),
                columns=['Event Type', 'Count']
            )
            st.bar_chart(chart_data.set_index('Event Type'))
        
        # 에이전트별 활동
        agent_activity = {}
        for event in session.events:
            if event.agent_name:
                agent_activity[event.agent_name] = agent_activity.get(event.agent_name, 0) + 1
        
        if agent_activity:
            st.subheader("Agent Activity")
            activity_data = pd.DataFrame(
                list(agent_activity.items()),
                columns=['Agent', 'Activities']
            )
            st.bar_chart(activity_data.set_index('Agent'))
    
    def display_export_options(self, session: ConversationSession):
        """내보내기 옵션 표시"""
        st.subheader("💾 Export Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as JSON", key=f"export_json_{session.session_id}"):
                json_data = session.to_dict()
                st.download_button(
                    "Download JSON",
                    json.dumps(json_data, indent=2, ensure_ascii=False),
                    file_name=f"session_{session.session_id[:8]}.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("📊 Export as CSV", key=f"export_csv_{session.session_id}"):
                # 이벤트를 CSV 형태로 변환
                csv_data = []
                for event in session.events:
                    csv_data.append({
                        "timestamp": event.timestamp,
                        "event_type": event.event_type.name,
                        "agent_name": event.agent_name or "",
                        "tool_name": event.tool_name or "",
                        "content": event.content or "",
                        "error_message": event.error_message or ""
                    })
                
                df = pd.DataFrame(csv_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    "Download CSV",
                    csv,
                    file_name=f"session_{session.session_id[:8]}.csv",
                    mime="text/csv"
                )
        
        # 보고서 생성
        st.divider()
        if st.button("📋 Generate Report", key=f"export_report_{session.session_id}"):
            report = self._generate_session_report(session)
            st.download_button(
                "Download Report",
                report,
                file_name=f"session_report_{session.session_id[:8]}.md",
                mime="text/markdown"
            )
    
    def _calculate_session_duration(self, session: ConversationSession) -> str:
        """세션 지속 시간 계산"""
        try:
            if session.end_time:
                start_dt = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(session.end_time.replace('Z', '+00:00'))
                duration = end_dt - start_dt
                return str(duration).split('.')[0]  # 초 단위 제거
            else:
                return "In Progress"
        except:
            return "Unknown"
    
    def _calculate_events_per_minute(self, session: ConversationSession) -> str:
        """분당 이벤트 수 계산"""
        try:
            if len(session.events) < 2:
                return "N/A"
                
            first_event = min(session.events, key=lambda x: x.timestamp)
            last_event = max(session.events, key=lambda x: x.timestamp)
            
            start_dt = datetime.fromisoformat(first_event.timestamp.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(last_event.timestamp.replace('Z', '+00:00'))
            
            duration_minutes = (end_dt - start_dt).total_seconds() / 60
            if duration_minutes > 0:
                events_per_minute = len(session.events) / duration_minutes
                return f"{events_per_minute:.1f}"
            else:
                return "N/A"
        except:
            return "Unknown"
    
    def _generate_session_report(self, session: ConversationSession) -> str:
        """세션 보고서 생성"""
        report = f"""# Session Report

## Basic Information
- **Session ID**: {session.session_id}
- **User ID**: {session.user_id}
- **Platform**: {session.platform}
- **Start Time**: {session.start_time}
- **End Time**: {session.end_time or 'In Progress'}
- **Duration**: {self._calculate_session_duration(session)}

## Statistics
- **Total Events**: {session.total_events}
- **Total Messages**: {session.total_messages}
- **Tools Used**: {session.total_tools_used}
- **Agents Used**: {', '.join(session.agents_used) if session.agents_used else 'None'}

## Model Information
"""
        
        if session.model_info:
            report += f"- **Model**: {session.model_info.get('display_name', 'Unknown')}\n"
            report += f"- **Provider**: {session.model_info.get('provider', 'Unknown')}\n"
        else:
            report += "- **Model**: Unknown\n"
        
        report += "\n## Event Timeline\n\n"
        
        for i, event in enumerate(session.events, 1):
            timestamp = event.timestamp[:19].replace('T', ' ')
            report += f"### {i}. {event.event_type.name} ({timestamp})\n\n"
            
            if event.agent_name:
                report += f"**Agent**: {event.agent_name}\n\n"
            if event.tool_name:
                report += f"**Tool**: {event.tool_name}\n\n"
            if event.content:
                report += f"**Content**:\n```\n{event.content}\n```\n\n"
            if event.error_message:
                report += f"**Error**: {event.error_message}\n\n"
            
            report += "---\n\n"
        
        return report
