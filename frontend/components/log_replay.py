"""
간소화된 로그 재현 유틸리티 - 기본 기능만 제공
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.utils.logging.conversation_logger import ConversationSession, ConversationEvent

class LogReplayUtility:
    """간소화된 로그 재현 유틸리티 클래스"""
    
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
    def find_sessions_by_date(
        base_path: str, 
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """날짜별 세션 검색 - 간소화"""
        results = []
        base_path = Path(base_path)
        
        try:
            for session_file in base_path.rglob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 날짜 필터링 (기본 구현)
                    if date_from or date_to:
                        session_date = session_data.get('start_time', '')[:10]
                        if date_from and session_date < date_from:
                            continue
                        if date_to and session_date > date_to:
                            continue
                    
                    # 기본 정보만 추출
                    results.append({
                        'file_path': str(session_file),
                        'session_id': session_data['session_id'],
                        'start_time': session_data['start_time'],
                        'event_count': len(session_data.get('events', []))
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
    def export_session_to_json(session: ConversationSession, output_path: str) -> bool:
        """세션을 JSON으로 내보내기"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting to JSON: {str(e)}")
            return False
