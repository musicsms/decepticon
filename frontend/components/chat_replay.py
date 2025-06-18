"""
채팅 화면에서 세션 자동 재생 기능
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from src.utils.logging.replay import get_replay_system

class ReplayManager:
    """자동 재생 관리자 - UI 컨트롤 없음"""
    
    def __init__(self):
        self.replay_system = get_replay_system()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def handle_replay_in_main_app(self, chat_area, agents_container, chat_ui) -> bool:
        """메인 앱에서 재현 처리 - 기존 워크플로우와 동일"""
        if not self.is_replay_mode():
            return False
        
        replay_session_id = st.session_state.get("replay_session_id")
        if not replay_session_id:
            return False
        
        try:
            # 재현 시작
            if self.replay_system.start_replay(replay_session_id):
                # 비동기 재현 실행 (기존 워크플로우와 동일)
                asyncio.run(self.replay_system.execute_replay(chat_area, agents_container, chat_ui))
                
                # 재현 완료 후 정리
                self.replay_system.stop_replay()
                
                return True
            
        except Exception as e:
            st.error(f"Replay error: {e}")
            # 에러 발생 시 재현 모드 해제
            self.replay_system.stop_replay()
        
        return False
