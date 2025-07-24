import streamlit as st
import streamlit.components.v1 as components
import re
from datetime import datetime
import time
import os
from .utils.float import float_css_helper

class TerminalUI:
    """가상 터미널 UI를 관리하는 클래스 - CLI 방식에 맞게 단순화"""
    
    def __init__(self):
        """UI 초기화"""
        # 터미널 히스토리 관리 및 세션 상태 초기화
        if "terminal_history" not in st.session_state:
            st.session_state.terminal_history = []
        
        self.terminal_history = st.session_state.terminal_history
        self.placeholder = None
        self.processed_messages = set()  # 이미 처리된 메시지 추적
    
    def apply_terminal_css(self):
        """터미널 CSS 스타일 적용 - static/css에서 로드"""
        css_path = "frontend/static/css/terminal.css"
        
        try:
            # CSS 파일에서 스타일 로드
            with open(css_path, "r", encoding="utf-8") as f:
                css = f.read()
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except Exception as e:
            print(f"Error loading terminal CSS: {e}")
    
    def create_terminal(self, container):
        """터미널 컨테이너 생성"""
        # 맥 스타일 헤더와 버튼
        container.markdown('''
        <div class="mac-terminal-header">
            <div class="mac-buttons">
                <div class="terminal-header-button red"></div>
                <div class="terminal-header-button yellow"></div>
                <div class="terminal-header-button green"></div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # 터미널 컨테이너 생성
        self.placeholder = container.empty()
        
        self._update_terminal_display()
        
        return self.placeholder
    
    def _update_terminal_display(self):
        """터미널 디스플레이 업데이트"""
        if self.placeholder:
            terminal_content = ""
            for entry in self.terminal_history:
                entry_type = entry.get("type", "output")
                content = entry.get("content", "")
                
                if entry_type == "command":
                    # 명령어 표시 형식
                    terminal_content += f'<div class="terminal-prompt"><span class="terminal-user">root@kali</span><span class="terminal-prompt-text">:~$ </span><span class="terminal-command-text">{content}</span></div>'
                elif entry_type == "output":
                    terminal_content += f'<div class="terminal-output">{content}</div>'
            
            # 커서 추가
            terminal_content += '<div class="terminal-prompt"><span class="terminal-user">root@kali</span><span class="terminal-prompt-text">:~$ </span><span class="terminal-cursor"></span></div>'
            
            # 터미널 컨테이너 HTML 생성
            terminal_html = f'''
            <div class="terminal-container" id="terminal-container">
                {terminal_content}
            </div>
            <script type="text/javascript">
            (function() {{
                const terminal = document.getElementById('terminal-container');
                if (terminal) {{
                    terminal.scrollTop = terminal.scrollHeight;
                }}
            }})();
            </script>
            '''
            
            # HTML을 플레이스홀더에 적용
            self.placeholder.markdown(terminal_html, unsafe_allow_html=True)
            
            # 세션 상태에 터미널 히스토리 저장
            st.session_state.terminal_history = self.terminal_history
    
    def add_command(self, command):
        """터미널에 명령어 추가 - CLI 방식으로 단순화"""
        # 명령어 정리
        command = self._clean_command(command)
        
        # 새 명령어 추가
        self.terminal_history.append({
            "type": "command",
            "content": command,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # 세션 상태 업데이트
        st.session_state.terminal_history = self.terminal_history
        self._update_terminal_display()
        
    def add_output(self, output):
        """터미널에 출력 추가 - CLI 방식으로 단순화"""
        # 출력 내용 정리
        output = self._sanitize_output(output)
        
        # 새 출력 추가
        self.terminal_history.append({
            "type": "output",
            "content": output,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        # 세션 상태 업데이트
        st.session_state.terminal_history = self.terminal_history
        self._update_terminal_display()
    
    def _clean_command(self, command):
        """명령어 정리 - CLI 방식"""
        if not isinstance(command, str):
            command = str(command)
        
        # 앞뒤 공백 제거
        command = command.strip()
        
        # 여러 줄인 경우 첫 번째 줄만 사용
        if '\n' in command:
            command = command.split('\n')[0].strip()
        
        # 불필요한 프리픽스 제거
        prefixes_to_remove = [
            'Running command:',
            'Executing:',
            'Command:',
            'Execute:',
            '$',
            '# '
        ]
        
        for prefix in prefixes_to_remove:
            if command.startswith(prefix):
                command = command[len(prefix):].strip()
        
        return command
    
    def _sanitize_output(self, output):
        """출력 내용 정리"""
        if not isinstance(output, str):
            output = str(output)
        
        # HTML 이스케이프 (& < >)
        output = output.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        
        # 줄바꿈 처리
        output = output.replace("\n", "<br>")
        
        return output
    
    def clear_terminal(self):
        """터미널 히스토리 초기화 - 완전 청소"""
        # 인스턴스 상태 초기화
        self.terminal_history = []
        self.processed_messages = set()
        
        # 세션 상태에 터미널 히스토리 저장
        st.session_state.terminal_history = self.terminal_history
        
        # 플레이스홀더 초기화 (있는 경우)
        if self.placeholder:
            self.placeholder.empty()
        
        # 디스플레이 업데이트
        self._update_terminal_display()
    
    def process_frontend_messages(self, frontend_messages):
        """프론트엔드 메시지 처리 - app.py에서 호출하는 메서드"""
        if not frontend_messages:
            return
        
        # frontend_messages는 리스트 형태
        for message in frontend_messages:
            message_id = message.get("id")
            
            # 이미 처리한 메시지는 건너뛰
            if message_id in self.processed_messages:
                continue
                
            message_type = message.get("type")
            
            # 도구 메시지 처리
            if message_type == "tool":
                tool_display_name = message.get("tool_display_name", "Tool")
                content = message.get("content", "")
                
                # terminal 관련 도구를 식별하여 명령어와 출력 처리 개선
                is_terminal_tool = (
                    "terminal" in tool_display_name.lower() or 
                    "command" in tool_display_name.lower() or
                    "exec" in tool_display_name.lower() or
                    "shell" in tool_display_name.lower()
                )
                
                if is_terminal_tool:
                    # 내용에서 명령어와 출력 분리 시도
                    lines = content.split('\n') if content else []
                    
                    # 명령어 찾기 시도
                    command_found = False
                    for i, line in enumerate(lines):
                        line = line.strip()
                        # 사용자 입력 명령어를 생각하는 패턴
                        if any(indicator in line.lower() for indicator in ['$', '#', 'command:', 'executing:', 'running:']):
                            # 이 라인을 명령어로 처리
                            cleaned_command = self._extract_command_from_line(line)
                            if cleaned_command:
                                self.add_command(cleaned_command)
                                command_found = True
                                # 나머지 라인들을 출력으로 처리
                                remaining_output = '\n'.join(lines[i+1:])
                                if remaining_output.strip():
                                    self.add_output(remaining_output.strip())
                                break
                    
                    # 명령어를 찾지 못한 경우 전체를 출력으로 처리
                    if not command_found and content.strip():
                        # 도구 이름을 명령어로 추가
                        self.add_command(f"{tool_display_name.lower()}")
                        self.add_output(content)
                else:
                    # 비-터미널 도구인 경우 도구 이름과 출력만 표시
                    if content and content.strip():
                        self.add_command(f"{tool_display_name}")
                        self.add_output(content)
                
                # 처리된 메시지로 표시
                self.processed_messages.add(message_id)
    
    def _extract_command_from_line(self, line):
        """라인에서 실제 명령어 추출"""
        line = line.strip()
        
        # 여러 패턴으로 명령어 추출 시도
        patterns = [
            r'(?:command|executing|running):\s*(.+)',
            r'\$\s*(.+)',
            r'#\s*(.+)',
            r'^(.+?)\s*$'  # 마지막으로 전체 라인 사용
        ]
        
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                command = match.group(1).strip()
                if command:
                    return command
        
        return line
    
    def process_structured_messages(self, structured_messages):
        """구조화된 메시지 데이터에서 명령어와 출력 처리 - 도구 메시지 반복 출력 방지"""
        if not structured_messages:
            return
        
        # 메시지 순회 및 처리
        for message in structured_messages:
            message_id = message.get("id")
            
            # 이미 처리한 메시지는 건너뜀
            if message_id in self.processed_messages:
                continue
                
            message_type = message.get("type")
            
            # 도구 메시지 처리 - CLI와 동일하게 tool 타입으로 통일
            if message_type == "tool":
                tool_display_name = message.get("tool_display_name", "Tool")
                content = message.get("content", "")
                
                if tool_display_name and content:
                    # 도구 이름을 명령어로 표시
                    self.add_command(tool_display_name)
                    # 출력 추가
                    self.add_output(content)
                    self.processed_messages.add(message_id)


# ================================
# 터미널 관련 Helper 함수들
# ================================

def load_terminal_css():
    """terminal.css 로드"""
    css_path = "frontend/static/css/terminal.css"
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        st.markdown(f"<style>{css_content}</style>", unsafe_allow_html=True)
    except Exception as e:
        print(f"Warning: Could not load terminal.css: {e}")


def create_floating_terminal(terminal_ui):
    """플로팅 터미널 생성 - 터미널 UI 초기화 강화"""
    
    terminal_container = st.container()
    
    with terminal_container:
        # 터미널 CSS 재적용 (플로팅 전에 적용)
        terminal_ui.apply_terminal_css()
        
        # 터미널 생성 (MAC 헤더는 terminal_ui.create_terminal()에서 처리)
        terminal_ui.create_terminal(st.container())
        
        # 디버깅: 터미널 메시지 상태 확인
        terminal_messages = st.session_state.get("terminal_messages")
        structured_messages = st.session_state.get("structured_messages", [])
        terminal_history = st.session_state.get("terminal_history", [])
        
        # 디버깅 정보 표시 (디버그 모드에서만)
        if st.session_state.get("debug_mode", False):
            st.write(f"Debug - terminal_messages: {len(terminal_messages) if terminal_messages else 0}")
            st.write(f"Debug - structured_messages: {len(structured_messages)}")
            st.write(f"Debug - terminal_history: {len(terminal_history)}")
            st.write(f"Debug - replay_mode: {st.session_state.get('replay_mode', False)}")
            if terminal_messages:
                st.write("Debug - terminal_messages sample:", terminal_messages[:2] if len(terminal_messages) > 0 else "Empty")
        
        # 터미널 메시지 복원 - 다양한 소스에서 메시지 처리
        try:
            # 1. terminal_messages에서 처리
            if terminal_messages:
                terminal_ui.process_structured_messages(terminal_messages)
            
            # 2. structured_messages에서 tool 메시지 처리
            elif structured_messages:  # terminal_messages가 없을 때만
                tool_messages = [msg for msg in structured_messages if msg.get("type") == "tool"]
                if tool_messages:
                    terminal_ui.process_structured_messages(tool_messages)
                
        except Exception as e:
            if st.session_state.get("debug_mode", False):
                st.error(f"Debug - Terminal message processing error: {e}")
    
    # Floating CSS 적용 (높이 제한 추가)
    terminal_css = float_css_helper(
        width="350px",
        height="500px",
        right="40px",
        top="50%",
        transform="translateY(-50%)",
        z_index="1000",
        border_radius="12px",
        box_shadow="0 25px 50px -12px rgba(0, 0, 0, 0.25)",
        backdrop_filter="blur(16px)",
        background="linear-gradient(145deg, #1f2937 0%, #111827 100%)",
        border="1px solid #374151",
        max_height="500px",
        overflow_y="auto"
    )
    
    terminal_container.float(terminal_css)
    
    return terminal_container


def create_floating_toggle_button():
    """플로팅 토글 버튼 생성"""
    
    toggle_container = st.container()
    
    with toggle_container:
        # 터미널 상태에 따른 버튼
        if st.session_state.get("terminal_visible", True):
            button_text = "💻 Hide Terminal"
            button_type = "secondary"
        else:
            button_text = "💻 Show Terminal"
            button_type = "primary"
        
        # 토글 버튼
        if st.button(button_text, type=button_type, use_container_width=True):
            st.session_state.terminal_visible = not st.session_state.get("terminal_visible", True)
            st.rerun()
    
    # Floating CSS 적용
    toggle_css = float_css_helper(
        width="140px",
        right="40px",
        bottom="20px",
        z_index="1001",
        border_radius="12px",
        box_shadow="0 8px 32px rgba(0,0,0,0.12)",
        backdrop_filter="blur(16px)",
        background="rgba(255, 255, 255, 0.9)"
    )
    
    toggle_container.float(toggle_css)
    
    return toggle_container
