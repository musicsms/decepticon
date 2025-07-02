import streamlit as st
import re
import time
from datetime import datetime
from src.utils.message import get_agent_name

class ChatUI:
    """채팅 인터페이스를 관리하는 클래스"""
    
    def __init__(self):
        """UI 초기화"""
        self._setup_styles()
        # 메시지 고유 ID 카운터 (영구적 색상 적용용)
        if "message_counter" not in st.session_state:
            st.session_state.message_counter = 0
    
    def _setup_styles(self):
        """스타일 설정"""
        try:
            # 외부 CSS 파일 로드
            css_path = "static/css/chat_ui.css"
            with open(css_path, "r", encoding="utf-8") as f:
                chat_css = f.read()
            
            # CSS 스타일 적용
            st.html(f"<style>{chat_css}</style>")
            
            # 에이전트 상태 CSS 로드
            agent_status_css_path = "static/css/agent_status.css"
            with open(agent_status_css_path, "r", encoding="utf-8") as f:
                agent_status_css = f.read()
            
            # 에이전트 상태 CSS 적용
            st.html(f"<style>{agent_status_css}</style>")
        except Exception as e:
            print(f"Error loading CSS: {e}")
    
    def format_timestamp(self, timestamp=None):
        """현재 시간 또는 주어진 타임스탬프를 포맷팅"""
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp)
                return dt.strftime("%H:%M:%S")
            except (ValueError, TypeError):
                pass
        return datetime.now().strftime("%H:%M:%S")
    
    def get_agent_class_name(self, agent_name):
        """에이전트 이름에 따른 CSS 클래스 이름 반환 (예전 코드 방식)"""
        if isinstance(agent_name, str):
            if "Supervisor" in agent_name or "supervisor" in agent_name.lower():
                return "supervisor-message"
            elif "Planner" in agent_name or "planner" in agent_name.lower():
                return "planner-message"
            elif "Reconnaissance" in agent_name or "reconnaissance" in agent_name.lower():
                return "recon-message"
            elif "Initial_Access" in agent_name or "initial" in agent_name.lower():
                return "initaccess-message"
            elif "Execution" in agent_name or "execution" in agent_name.lower():
                return "execution-message"
            elif "Persistence" in agent_name or "persistence" in agent_name.lower():
                return "persistence-message"
            elif "Privilege_Escalation" in agent_name or "privilege" in agent_name.lower():
                return "privilege-escalation-message"
            elif "Defense_Evasion" in agent_name or "defense" in agent_name.lower() or "evasion" in agent_name.lower():
                return "defense-evasion-message"
            elif "tool" in agent_name.lower():
                return "tool-message"
        return "agent-message"  # 기본 클래스
    
    def get_agent_color(self, agent_name):
        """에이전트 이름에 따른 색상 반환"""
        if isinstance(agent_name, str):
            agent_name = agent_name.lower()
            if "planner" in agent_name:
                return "#4dabf7"
            elif "reconnaissance" in agent_name:
                return "#7950f2"
            elif "initial_access" in agent_name:
                return "#fab005"
            elif "execution" in agent_name:
                return "#f76707"
            elif "persistence" in agent_name:
                return "#ae3ec9"
            elif "privilege_escalation" in agent_name:
                return "#d6336c"
            elif "defense_evasion" in agent_name:
                return "#1098ad"
            elif "summary" in agent_name:
                return "#fd7e14"
            elif "tool" in agent_name:
                return "#82c91e"
        return "#adb5bd"  # 기본 색상
    
    def simulate_typing(self, text, placeholder, speed=0.005):
        """타이핑 애니메이션 시뮬레이션"""
        # 코드 블록 위치 찾기
        code_blocks = []
        code_block_pattern = r'```.*?```'
        for match in re.finditer(code_block_pattern, text, re.DOTALL):
            code_blocks.append((match.start(), match.end()))
        
        result = ""
        i = 0
        chars_per_update = 5  # 성능 최적화
        
        while i < len(text):
            # 현재 위치가 코드 블록 안에 있는지 확인
            in_code_block = False
            code_block_to_add = None
            
            for start, end in code_blocks:
                if i == start:
                    code_block_to_add = text[start:end]
                    in_code_block = True
                    break
                elif start < i < end:
                    in_code_block = True
                    break
            
            if code_block_to_add:
                result += code_block_to_add
                i = end
                placeholder.markdown(result)
                time.sleep(speed * 2)
            elif in_code_block:
                i += 1
            else:
                end_pos = min(i + chars_per_update, len(text))
                
                # 다음 코드 블록 전까지만 추가
                for block_start, _ in code_blocks:
                    if block_start > i:
                        end_pos = min(end_pos, block_start)
                        break
                
                result += text[i:end_pos]
                i = end_pos
                
                placeholder.markdown(result)
                time.sleep(speed)
    
    def display_messages(self, structured_messages, container=None):
        """구조화된 메시지를 UI에 표시"""
        if container is None:
            container = st
            
        for message in structured_messages:
            message_type = message.get("type", "")
            
            if message_type == "user":
                # 사용자 메시지
                with container.chat_message("user"):
                    st.write(message.get("content", ""))
                    
            elif message_type == "ai":
                # AI 에이전트 메시지 - 일반 워크플로우와 동일
                self.display_agent_message(message, container, streaming=False)
                
            elif message_type == "tool":
                # 도구 메시지 - 일반 워크플로우와 동일
                self.display_tool_message(message, container)
    
    def display_agent_message(self, message, container=None, streaming=True):
        """에이전트 메시지 표시 - 재현 시스템 호환성 개선"""
        if container is None:
            container = st
            
        display_name = message.get("display_name", "Agent")
        avatar = message.get("avatar", "🤖")
        
        # 재현 시스템과 일반 시스템 모두 호환
        if "data" in message and isinstance(message["data"], dict):
            # 재현 시스템 형식
            content = message["data"].get("content", "")
            # 재현 시스템에서도 tool_calls 확인
            tool_calls = message.get("tool_calls", [])
        else:
            # 일반 시스템 형식
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
        
        # namespace 정보에서 에이전트 이름 추출 (기존 get_agent_name 함수 사용)
        namespace = message.get("namespace", "")
        if namespace:
            # namespace가 문자열인 경우 리스트로 변환
            if isinstance(namespace, str):
                namespace_list = [namespace]
            else:
                namespace_list = namespace
            agent_name_for_color = get_agent_name(namespace_list)
            # "Unknown"이 반환되면 display_name 사용
            if agent_name_for_color == "Unknown":
                agent_name_for_color = display_name
        else:
            # namespace가 없으면 display_name 사용
            agent_name_for_color = display_name
        
        # 에이전트 색상 및 클래스 생성
        agent_color = self.get_agent_color(agent_name_for_color)
        agent_class = self.get_agent_class_name(agent_name_for_color)
        
        # 고유한 메시지 ID 생성
        st.session_state.message_counter += 1
        
        # 메시지 먼저 출력 (DOM 요소 생성)
        with container.chat_message("assistant", avatar=avatar):
            # 예전 코드와 동일하게 클래스 추가
            st.markdown(f'<div class="agent-header {agent_class}"><strong style="color: {agent_color}">{display_name}</strong></div>', unsafe_allow_html=True)
            
            # 컨텐츠 표시
            if content:
                text_placeholder = st.empty()
                
                # 재현 모드에서는 타이핑 애니메이션 비활성화
                is_replay_mode = st.session_state.get("replay_mode", False)
                if streaming and len(content) > 50 and not is_replay_mode:
                    self.simulate_typing(content, text_placeholder, speed=0.005)
                else:
                    text_placeholder.write(content)
            elif not tool_calls:  # content가 없고 tool_calls도 없을 때만 오류 메시지 표시
                st.write("No content available")
            
            # Tool calls 정보 표시 (클로드 데스크탑 스타일)
            tool_calls = message.get("tool_calls", [])
            if tool_calls:
                for i, tool_call in enumerate(tool_calls):
                    tool_name = tool_call.get("name", "Unknown Tool")
                    tool_args = tool_call.get("args", {})
                    
                    # tool call 메시지 생성
                    try:
                        from src.utils.message import parse_tool_call
                        tool_call_message = parse_tool_call(tool_call)
                    except Exception as e:
                        tool_call_message = f"Tool call error: {str(e)}"
                    
                    # 클로드 데스크탑 스타일의 확장 가능한 UI
                    with st.expander(f"**{tool_call_message}**", expanded=False):
                        # 도구 세부 정보 표시
                        col1, col2 = st.columns([1, 3])
                        
                        with col1:
                            st.markdown("**Tool:**")
                            st.markdown("**ID:**")
                            if tool_args:
                                st.markdown("**Arguments:**")
                        
                        with col2:
                            st.markdown(f"`{tool_name}`")
                            st.markdown(f"`{tool_call.get('id', 'N/A')}`")
                            if tool_args:
                                # 매개변수들을 JSON 형태로 깔끔하게 표시
                                import json
                                st.code(json.dumps(tool_args, indent=2), language="json")
                            else:
                                st.markdown("`No arguments`")
    
    def display_tool_message(self, message, container=None):
        """도구 메시지 표시 - 메시지 출력 후 CSS 적용"""
        if container is None:
            container = st
            
        tool_display_name = message.get("tool_display_name", "Tool")
        content = message.get("content", "")
        
        # tool 메시지는 항상 tool 색상 사용
        tool_color = self.get_agent_color("tool")
        tool_class = "tool-message"
        
        # 고유한 메시지 ID 생성
        st.session_state.message_counter += 1
        
        # 메시지 먼저 출력 (DOM 요소 생성)
        with container.chat_message("tool", avatar="🔧"):
            # tool 클래스 추가
            st.markdown(f'<div class="agent-header {tool_class}"><strong style="color: {tool_color}">{tool_display_name}</strong></div>', unsafe_allow_html=True)
            
            # 컨텐츠 표시
            if content:
                # 너무 긴 출력은 제한
                if len(content) > 5000:
                    st.code(content[:5000] + "\n[Output truncated...]")
                    with st.expander("More.."):
                        st.text(content)
                else:
                    st.code(content)
    
    def display_tool_command(self, message, container=None):
        """도구 명령 메시지 표시 - 재현 시스템 호환성"""
        if container is None:
            container = st
            
        display_name = message.get("display_name", "Tool")
        command = message.get("data", {}).get("command", "")
        
        # 도구 색상 가져오기
        tool_color = self.get_agent_color("tool")
        
        with container.chat_message("tool", avatar="🔧"):
            st.markdown(f'<div class="agent-header tool-message"><strong style="color: {tool_color}">Command: {display_name}</strong></div>', unsafe_allow_html=True)
            st.code(command, language="bash")
    
    def display_tool_output(self, message, container=None):
        """도구 출력 메시지 표시 - 재현 시스템 호환성"""
        if container is None:
            container = st
            
        display_name = message.get("display_name", "Tool Output")
        output = message.get("data", {}).get("content", "")
        
        # 도구 출력 색상 가져오기
        tool_color = self.get_agent_color("tool")
        
        with container.chat_message("tool", avatar="🔧"):
            st.markdown(f'<div class="agent-header tool-output-message"><strong style="color: {tool_color}">Output: {display_name}</strong></div>', unsafe_allow_html=True)
            
            # 너무 긴 출력은 제한
            if len(output) > 5000:
                st.code(output[:5000] + "\n[Output truncated...]")
                with st.expander("더 보기.."):
                    st.text(output)
            else:
                st.code(output)
 
    def display_user_message(self, content, container=None):
        """사용자 메시지 표시"""
        if container is None:
            container = st
            
        with container.chat_message("user"):
            # HTML로 오른쪽 정렬된 사용자 메시지 생성
            st.markdown(f'<div style="text-align: left;">{content}</div>', unsafe_allow_html=True)    
    
    def display_agent_status(self, container, active_agent=None, active_stage=None, completed_agents=None):
        """에이전트 상태를 표시 - namespace 기반으로 단순화"""
        if completed_agents is None:
            completed_agents = []
        
        # CLI에서 실제 사용되는 에이전트만 표시 (하드코딩 제거)
        agents = [
            {"id": "planner", "name": "Planner", "icon": "🧠"},
            {"id": "reconnaissance", "name": "Reconnaissance", "icon": "🔍"},
            {"id": "initial_access", "name": "Initial Access", "icon": "🔑"},
            {"id": "execution", "name": "Execution", "icon": "💻"},
            {"id": "persistence", "name": "Persistence", "icon": "🔐"},
            {"id": "privilege_escalation", "name": "Privilege Escalation", "icon": "🔒"},
            {"id": "defense_evasion", "name": "Defense Evasion", "icon": "🕵️"},
            {"id": "summary", "name": "Summary", "icon": "📋"},
        ]
        
        # 플레이스홀더 관리
        if "agent_status_placeholders" not in st.session_state:
            st.session_state.agent_status_placeholders = {}
        
        # 초기 UI 상태 유지 체크
        is_initial_ui = st.session_state.get("keep_initial_ui", True)
        
        # 각 에이전트의 상태 표시
        for agent in agents:
            agent_id = agent["id"]
            agent_name = agent["name"]
            agent_icon = agent["icon"]
            
            # 플레이스홀더 생성
            if agent_id not in st.session_state.agent_status_placeholders:
                st.session_state.agent_status_placeholders[agent_id] = container.empty()
            
            # 상태 클래스 결정 - namespace 기반
            status_class = ""
            
            if not is_initial_ui:
                # 활성 에이전트 (현재 실행중)
                if agent_id == active_agent:
                    status_class = "status-active"
                # 완료된 에이전트
                elif agent_id in completed_agents:
                    status_class = "status-completed"
            
            # 상태 업데이트
            st.session_state.agent_status_placeholders[agent_id].html(
                f"<div class='agent-status {status_class}'>" +
                f"<div>{agent_icon} {agent_name}</div>" +
                f"</div>"
            )
        
        # 사용자 입력이 있었을 때 초기 UI 유지 플래그 해제
        if is_initial_ui and active_agent is not None and len(completed_agents) > 0:
            st.session_state.keep_initial_ui = False

    def show_processing_status(self, label="Processing...", expanded=True):
        """처리 중 상태 표시"""
        return st.status(label, expanded=expanded)
