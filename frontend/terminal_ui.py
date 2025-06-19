import streamlit as st
import re
from datetime import datetime
import time
import os

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
        css_path = "static/css/terminal.css"
        
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
