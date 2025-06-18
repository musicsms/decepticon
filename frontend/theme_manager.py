import streamlit as st
import toml
from pathlib import Path

class ThemeManager:
    """테마 관리 클래스"""
    
    def __init__(self):
        """테마 매니저 초기화"""
        self.static_dir = Path(__file__).parent.parent / "static"
        self.config_dir = Path(__file__).parent.parent / ".streamlit"
        self.dark_theme_css = self.static_dir / "dark_theme.css"
        self.light_theme_css = self.static_dir / "light_theme.css"
        self.dark_theme_toml = self.static_dir / "dark_theme.toml"
        self.light_theme_toml = self.static_dir / "light_theme.toml"
        self.config_toml = self.config_dir / "config.toml"
        
        # 세션 상태 초기화
        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = True
            
        # 파일 존재 확인
        self._check_files()
    
    def _check_files(self):
        """필요한 파일이 존재하는지 확인"""
        required_files = [
            self.dark_theme_css,
            self.light_theme_css,
            self.dark_theme_toml,
            self.light_theme_toml
        ]
        
        # CSS 디렉토리 확인
        css_dir = self.static_dir / "css"
        if not css_dir.exists():
            css_dir.mkdir(parents=True, exist_ok=True)
            print(f"Created CSS directory: {css_dir}")
        
        # 필수 CSS 파일 확인
        required_css_files = [
            css_dir / "terminal.css",
            css_dir / "chat_ui.css",
            css_dir / "agent_status.css",
            css_dir / "layout.css",
            css_dir / "input_fix.css"
        ]
        
        for file in required_files + required_css_files:
            if not file.exists():
                st.error(f"테마 파일을 찾을 수 없습니다: {file}")
                
        # 설정 디렉토리가 없는 경우 생성
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def get_current_theme(self):
        """현재 테마 반환"""
        # dark_mode가 없는 경우 초기화 (기본값: dark mode)
        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = True
            print("Initialized dark_mode to True")
            
        return "dark" if st.session_state.dark_mode else "light"
    
    def load_theme_css(self):
        """현재 테마에 맞는 CSS 파일 로드"""
        theme = self.get_current_theme()
        css_file = self.dark_theme_css if theme == "dark" else self.light_theme_css
        
        try:
            with open(css_file, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.error(f"테마 CSS 파일을 로드하는 중 오류 발생: {str(e)}")
            return ""
    
    def _update_streamlit_theme_config(self):
        """현재 테마에 따라 Streamlit 설정 파일 업데이트"""
        theme = self.get_current_theme()
        theme_toml = self.dark_theme_toml if theme == "dark" else self.light_theme_toml
        
        try:
            # 기존 config.toml 파일 읽기 (일반 설정 유지 위해)
            if self.config_toml.exists():
                with open(self.config_toml, "r", encoding="utf-8") as f:
                    config = toml.load(f)
            else:
                config = {}
            
            # 테마 관련 설정 읽기
            with open(theme_toml, "r", encoding="utf-8") as f:
                theme_config = toml.load(f)
            
            print(f"Updating config.toml for theme: {theme}")
            print(f"Current config: {config}")
            print(f"Theme config to apply: {theme_config}")
            
            # 기존 테마 설정 제거 (있는 경우)
            if "theme" in config:
                del config["theme"]
            
            # 새 테마 설정 추가
            config.update(theme_config)
            
            # 설정 저장
            with open(self.config_toml, "w", encoding="utf-8") as f:
                toml.dump(config, f)
            
            print(f"Updated config.toml successfully. New config: {config}")
            
            # 현재 테마 CSS 즉시 적용
            css = self.load_theme_css()
            if css:
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
                print(f"CSS applied by _update_streamlit_theme_config - Theme: {theme}, Length: {len(css)}")
                
            return True
        except Exception as e:
            print(f"Error updating config.toml: {str(e)}")
            st.error(f"테마 구성 파일 업데이트 중 오류 발생: {str(e)}")
            return False
    
    def apply_theme(self):
        """현재 테마 적용"""
        # CSS 적용
        css = self.load_theme_css()
        theme = self.get_current_theme()
        
        if css:
            # 테마에 따라 값 미리 계산
            sidebar_bg = "#0B0B12" if theme == "dark" else "#F0F2F6"  # 사이드바 배경색
            sidebar_text = "#FAFAFA" if theme == "dark" else "#31333F"  # 사이드바 텍스트
            toggle_bg = "#1E1E1E" if theme == "dark" else "#F0F2F6"  # 토글 버튼 배경색
            toggle_text = "#FFFFFF" if theme == "dark" else "#31333F"  # 토글 버튼 텍스트
            toggle_border = "rgba(255, 255, 255, 0.2)" if theme == "dark" else "rgba(49, 51, 63, 0.2)"  # 테두리 색
            
            # 에이전트 상태 컨테이너 스타일
            agent_bg = "linear-gradient(to right, #222222, #2d2d2d, #222222)" if theme == "dark" else "linear-gradient(to right, #F0F2F6, #FFFFFF, #F0F2F6)"  # 배경
            agent_border = "transparent" if theme == "dark" else "#DFE2E6"  # 테두리 색
            agent_text = "#FAFAFA" if theme == "dark" else "#31333F"  # 텍스트 색
            agent_hover_bg = "linear-gradient(to right, #262626, #323232, #262626)" if theme == "dark" else "linear-gradient(to right, #E8EAF0, #F5F7F9, #E8EAF0)"  # 호버 배경
            
            # 에이전트 활성 상태 스타일 - 강화된 버전
            active_bg = "linear-gradient(to right, #3a1515, #4a1f1f, #3a1515)" if theme == "dark" else "linear-gradient(to right, #FFF0F0, #FFF5F5, #FFF0F0)"  # 활성 배경
            active_border = "#ff4b4b" if theme == "dark" else "#FF4B4B"  # 활성 테두리
            active_shadow = "rgba(255, 75, 75, 0.9)" if theme == "dark" else "rgba(255, 75, 75, 0.6)"  # 활성 그림자
            active_text_shadow = "rgba(255, 75, 75, 0.8)" if theme == "dark" else "rgba(255, 75, 75, 0.4)"  # 텍스트 그림자
            animation_name = "pulse-button-dark" if theme == "dark" else "pulse-button-light"  # 애니메이션 이름
            
            # 다음 예정 에이전트 스타일
            next_bg = "linear-gradient(to right, #332b15, #403621, #332b15)" if theme == "dark" else "linear-gradient(to right, #FFFAF0, #FFFCF5, #FFFAF0)"  # 다음 예정 배경
            next_border = "#FFC107" if theme == "dark" else "#FFC107"  # 다음 예정 테두리
            
            # 완료 상태 스타일
            completed_bg = "linear-gradient(to right, #152315, #1e3a1e, #152315)" if theme == "dark" else "linear-gradient(to right, #F0FFF0, #F5FFF5, #F0FFF0)"  # 완료 배경
            completed_border = "#4CAF50" if theme == "dark" else "#4CAF50"  # 완료 테두리
            
            # 메시지 헤더 스타일
            header_text = "#F0F0F0" if theme == "dark" else "#31333F"  # 헤더 텍스트 색
            header_border = "rgba(255, 255, 255, 0.1)" if theme == "dark" else "rgba(0, 0, 0, 0.1)"  # 구분선 색
            
            # 메시지 컨텐트 배경
            message_bg = "rgba(45, 45, 45, 0.5)" if theme == "dark" else "rgba(240, 242, 246, 0.5)"  # 메시지 배경
            
            additional_css = f'''
            <style id="custom-theme-overrides">
            /* Streamlit 테마 오버라이드 - 강력한 선택자 사용 */
            
            /* 사이드바 메인 배경 */
            section[data-testid="stSidebar"] > div,
            section[data-testid="stSidebar"] > div > div,
            section[data-testid="stSidebar"] > div > div > div,
            section[data-testid="stSidebar"] div.st-emotion-cache-*,
            .st-emotion-cache-*[data-testid="stSidebar"] {{
                background-color: {sidebar_bg} !important;
                color: {sidebar_text} !important;
            }}
            
            /* 사이드바 내부 요소 */
            section[data-testid="stSidebar"] h1, 
            section[data-testid="stSidebar"] h2, 
            section[data-testid="stSidebar"] h3, 
            section[data-testid="stSidebar"] h4, 
            section[data-testid="stSidebar"] h5, 
            section[data-testid="stSidebar"] h6,
            section[data-testid="stSidebar"] p,
            section[data-testid="stSidebar"] span,
            section[data-testid="stSidebar"] div,
            section[data-testid="stSidebar"] label {{
                color: {sidebar_text} !important;
            }}
            
            /* 토글 버튼 스타일 */
            .stToggleButton label,
            [data-testid="stToggleButton"] label {{
                background-color: {toggle_bg} !important;
                color: {toggle_text} !important;
                border-color: {toggle_border} !important;
            }}
            
            /* 에이전트 상태 컨테이너 스타일 수정 */
            .agent-status {{
                display: flex;
                align-items: center;
                margin-bottom: 10px;
                padding: 8px 12px;
                border-radius: 5px;
                background: {agent_bg} !important;
                transition: all 0.3s ease;
                border: 1px solid {agent_border} !important;
                font-size: 18px;
                color: {agent_text} !important;
                box-shadow: none !important;
            }}
            
            .agent-status div {{
                color: {agent_text} !important;
                font-size: 18px !important;
            }}
            
            .agent-status:hover {{
                background: {agent_hover_bg} !important;
            }}
            
            .agent-status.status-active {{
                background: {active_bg} !important;
                border: 2px solid {active_border} !important;
                box-shadow: 0 0 15px {active_shadow} !important;
                animation: {animation_name} 1.5s infinite alternate;
                font-weight: bold;
                text-shadow: 0 0 10px {active_text_shadow};
            }}
            
            .agent-status.status-completed {{
                background: {completed_bg} !important;
                border: 2px solid {completed_border} !important;
            }}
            
            /* 채팅 메시지 헤더 스타일 */
            .agent-header {{
                font-size: 24px !important;
                font-weight: 600;
                color: {header_text} !important;
                margin-bottom: 10px;
                padding-bottom: 8px;
                border-bottom: 1px solid {header_border} !important;
                position: relative;
            }}
            
            /* 채팅 메시지 컨텐트 스타일 */
            div.stChatMessage[data-testid="stChatMessage"] .stChatMessageContent {{
                padding: 10px 15px;
                border-radius: 6px;
                background-color: {message_bg} !important;
            }}
            
            /* 애니메이션 정의 */
            @keyframes pulse-button-dark {{
                0% {{
                    background-color: rgba(255, 75, 75, 0.2);
                    box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.7);
                }}
                50% {{
                    background-color: rgba(255, 75, 75, 0.4);
                    box-shadow: 0 0 20px 5px rgba(255, 75, 75, 0.9);
                }}
                100% {{
                    background-color: rgba(255, 75, 75, 0.2);
                    box-shadow: 0 0 0 0 rgba(255, 75, 75, 0);
                }}
            }}
            
            @keyframes pulse-button-light {{
                0% {{
                    background-color: rgba(255, 75, 75, 0.15);
                    box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.5);
                    border-color: rgba(255, 75, 75, 0.7);
                }}
                50% {{
                    background-color: rgba(255, 75, 75, 0.3);
                    box-shadow: 0 0 20px 5px rgba(255, 75, 75, 0.8);
                    border-color: rgba(255, 75, 75, 1);
                }}
                100% {{
                    background-color: rgba(255, 75, 75, 0.15);
                    box-shadow: 0 0 0 0 rgba(255, 75, 75, 0);
                    border-color: rgba(255, 75, 75, 0.7);
                }}
            }}
            </style>
            '''
            
            # 터미널 UI 테마 스타일 추가
            terminal_theme_css = f'''
            <style id="terminal-theme-overrides">
                /* 터미널 테마 스타일 - {theme} 모드 */
                .terminal-container {{                
                    background-color: {"#1E1E1E" if theme == "dark" else "#F5F5F5"} !important;
                    color: {"#FFFFFF" if theme == "dark" else "#333333"} !important;
                    box-shadow: {"rgba(0, 0, 0, 0.5)" if theme == "dark" else "rgba(0, 0, 0, 0.1)"} -2px 0 10px !important;
                }}
                
                .terminal-header {{                
                    background-color: {"#333333" if theme == "dark" else "#E0E0E0"} !important;
                    color: {"#FFFFFF" if theme == "dark" else "#333333"} !important;
                }}
                
                .terminal-prompt {{                
                    color: {"#4EC9B0" if theme == "dark" else "#0B7285"} !important;
                }}
                
                .terminal-command {{                
                    color: {"#DCDCAA" if theme == "dark" else "#AD8400"} !important;
                }}
                
                .terminal-output {{                
                    color: {"#CCCCCC" if theme == "dark" else "#555555"} !important;
                }}
                
                .terminal-success {{                
                    color: {"#6A9955" if theme == "dark" else "#2E7D32"} !important;
                }}
                
                .terminal-error {{                
                    color: {"#F14C4C" if theme == "dark" else "#C62828"} !important;
                }}
                
                .terminal-warning {{                
                    color: {"#DCDCAA" if theme == "dark" else "#F57F17"} !important;
                }}
                
                .terminal-cursor {{                
                    background-color: {"#FFFFFF" if theme == "dark" else "#333333"} !important;
                }}
            </style>
            '''
            
            # 레이아웃 CSS 로드
            layout_css_path = self.static_dir / "css" / "layout.css"
            layout_css = ""
            if layout_css_path.exists():
                with open(layout_css_path, "r", encoding="utf-8") as f:
                    layout_css = f.read()
            
            # 입력창 고정 CSS 로드 (최종 적용을 위해 마지막에 로드)
            input_fix_css_path = self.static_dir / "css" / "input_fix.css"
            input_fix_css = ""
            if input_fix_css_path.exists():
                with open(input_fix_css_path, "r", encoding="utf-8") as f:
                    input_fix_css = f.read()
                    
            # 기본 CSS와 추가 CSS 합치기
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
            st.markdown(additional_css, unsafe_allow_html=True)
            st.markdown(terminal_theme_css, unsafe_allow_html=True)
            st.markdown(f"<style>{layout_css}</style>", unsafe_allow_html=True)
            st.markdown(f"<style>{input_fix_css}</style>", unsafe_allow_html=True)
            
            print(f"Applied {theme} theme CSS with overrides")
        
        # Streamlit 설정 업데이트 (앱 재시작 시 적용)
        self._update_streamlit_theme_config()
    
    def toggle_theme_callback(self):
        """토글 상태가 변경되었을 때 호출되는 콜백 함수"""
        # theme_toggle의 현재 값을 확인
        if "theme_toggle" in st.session_state:
            # 토글 값을 상태로 저장
            st.session_state.dark_mode = st.session_state.theme_toggle
            print(f"Theme callback - Setting dark_mode to: {st.session_state.dark_mode}")
            
            # Streamlit 설정 파일 업데이트
            self._update_streamlit_theme_config()
            
            # 테마 CSS 즉시 적용
            css = self.load_theme_css()
            if css:
                st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    
    def toggle_theme(self):
        """테마 전환 (직접 호출용)"""
        # 이전 테마 상태 저장
        previous_mode = st.session_state.dark_mode
        
        # 세션 상태 변경
        st.session_state.dark_mode = not previous_mode
        
        # 로그 추가
        new_mode = "dark" if st.session_state.dark_mode else "light"
        print(f"Theme toggled DIRECTLY from {'dark' if previous_mode else 'light'} to {new_mode}")
        
        # 테마 파일 (.toml) 업데이트
        updated = self._update_streamlit_theme_config()
        if not updated:
            print("Warning: Could not update config.toml - applying CSS only")
        
        # 테마 CSS 즉시 적용 - 하지만 페이지 재로드가 아직 필요함
        self.apply_theme()
        
        # 테마 전환 후 즉시 적용을 위해 페이지 새로고침
        st.rerun()
    
    def create_theme_toggle(self, container=None):
        """테마 전환 토글 버튼 생성"""
        if container is None:
            container = st
            
        dark_mode = st.session_state.dark_mode
        theme_label = "🌙 Dark" if dark_mode else "☀️ Light"
        
        # 토글 상태가 변경되었는지 확인하기 위한 함수
        def on_toggle_change():
            # 토글 상태가 변경되면 dark_mode 상태 업데이트
            if "theme_toggle" in st.session_state:
                new_mode = st.session_state.theme_toggle
                if new_mode != dark_mode:  # 상태가 변경되었을 때만 처리
                    print(f"Theme toggle callback: changing to {new_mode}")
                    # 직접 toggle_theme를 호출하여 동일한 경로 유지
                    self.toggle_theme()
        
        # 토글 버튼 생성 - 토글 변경 자체는 dark_mode를 자동 변경하지 않음
        # 대신 on_change 콜백에서 toggle_theme를 호출하여 일관성 유지
        container.toggle(
            theme_label, 
            value=dark_mode, 
            key="theme_toggle", 
            on_change=on_toggle_change
        )
