"""
간소화된 채팅 재현 관리자 - 복잡한 컨트롤 제거
"""

import streamlit as st
import asyncio
from typing import Optional

from src.utils.logging.simple_replay import get_replay_system

class ChatReplayManager:
    """간소화된 채팅 재현 관리자 - 기존 워크플로우와 동일한 방식"""
    
    def __init__(self):
        self.replay_system = get_replay_system()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def handle_replay_in_main_app(self, chat_area, agents_container, chat_ui) -> bool:
        """메인 앱에서 재현 처리"""
        if not self.is_replay_mode():
            return False
        
        replay_session_id = st.session_state.get("replay_session_id")
        if not replay_session_id:
            return False
        
        try:
            # 재현 시작
            if self.replay_system.start_replay(replay_session_id):
                # 비동기 재현 실행
                asyncio.run(self.replay_system.execute_replay(chat_area, agents_container, chat_ui))
                
                # 재현 완료 후 정리
                self.replay_system.stop_replay()
                self._cleanup_replay_state()
                
                return True
            
        except Exception as e:
            st.error(f"Replay error: {e}")
            self._cleanup_replay_state()
        
        return False
    
    def _cleanup_replay_state(self):
        """재현 상태 정리"""
        for key in ["replay_mode", "replay_session_id"]:
            if key in st.session_state:
                del st.session_state[key]

# 하위 호환성을 위한 별칭
SimpleReplayManager = ChatReplayManager
