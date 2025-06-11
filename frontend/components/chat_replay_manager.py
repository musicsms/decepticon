"""
간소화된 채팅 재현 관리자 - 복잡한 컨트롤 제거
"""

import streamlit as st
import asyncio
from typing import Optional

from src.utils.logging.replay import get_replay_system

class ChatReplayManager:
    """간소화된 채팅 재현 관리자 - 기존 워크플로우와 동일한 방식"""
    
    def __init__(self):
        self.replay_system = get_replay_system()
    
    def is_replay_mode(self) -> bool:
        """재생 모드인지 확인"""
        return st.session_state.get("replay_mode", False)
    
    def handle_replay_in_main_app(self, chat_area, agents_container, chat_ui) -> bool:
        """메인 앱에서 재현 처리 - 메시지 유지"""
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
                
                # 재현 완료 후 상태 정리
                self.replay_system.stop_replay()
                
                # 재현 모드 플래그는 유지 (사용자가 버튼을 클릭할 때까지)
                # st.session_state.pop("replay_mode", None) - 제거
                # st.session_state.pop("replay_session_id", None) - 제거
                
                # 재현 완료 플래그 설정
                st.session_state.replay_completed = True
                
                # 메시지가 유지된 상태로 정상 모드로 복귀
                return True
            
        except Exception as e:
            st.error(f"Replay error: {e}")
            # 에러 발생 시 정리
            self.replay_system.stop_replay()
            st.session_state.pop("replay_mode", None)
            st.session_state.pop("replay_session_id", None)
        
        return False
    
    def _cleanup_replay_state(self):
        """재현 상태 정리 - 에러 시에만 사용"""
        # 에러 발생 시에만 사용되는 메소드
        # 정상 재현 완료 시에는 stop_replay만 호출
        self.replay_system.stop_replay()

# 하위 호환성을 위한 별칭
SimpleReplayManager = ChatReplayManager
