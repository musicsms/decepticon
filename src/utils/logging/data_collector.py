"""
Data Collection & Remote Logging
향후 데이터 수집을 위한 서버 전송 시스템
"""

import asyncio
import aiohttp
import json
import hashlib
import gzip
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

from .conversation_logger import ConversationSession, ConversationEvent

logger = logging.getLogger(__name__)

class DataCollector:
    """데이터 수집 및 원격 전송 시스템"""
    
    def __init__(self, collection_endpoint: Optional[str] = None, 
                 api_key: Optional[str] = None,
                 enable_collection: bool = False):
        self.collection_endpoint = collection_endpoint or "https://api.decepticon.ai/v1/collect"
        self.api_key = api_key
        self.enable_collection = enable_collection
        
        # 로컬 큐 (오프라인 시 저장)
        self.pending_queue: List[Dict[str, Any]] = []
        self.max_queue_size = 1000
        
        # 개인정보 보호 설정
        self.anonymize_data = True
        self.include_content = True  # False로 설정하면 메타데이터만 전송
        self.hash_user_ids = True
        
        logger.info(f"DataCollector initialized (collection_enabled: {enable_collection})")
    
    def _anonymize_user_id(self, user_id: str) -> str:
        """사용자 ID 익명화"""
        if not self.hash_user_ids:
            return user_id
        
        # SHA-256 해시 + salt로 사용자 ID 익명화
        salt = "decepticon_user_salt_2025"
        hash_input = f"{user_id}:{salt}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _sanitize_content(self, content: str) -> str:
        """민감한 정보 제거"""
        if not content:
            return content
        
        # IP 주소, 이메일, 전화번호 등 마스킹
        import re
        
        # IP 주소 마스킹
        content = re.sub(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP_ADDRESS]', content)
        
        # 이메일 마스킹
        content = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', content)
        
        # 전화번호 마스킹 (간단한 패턴)
        content = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', content)
        
        # URL에서 민감한 파라미터 제거
        content = re.sub(r'([?&](?:token|key|password|secret)=)[^&\s]+', r'\1[REDACTED]', content)
        
        return content
    
    def _prepare_session_data(self, session: ConversationSession) -> Dict[str, Any]:
        """세션 데이터를 전송용으로 준비"""
        
        # 기본 세션 정보
        session_data = {
            'session_id': session.session_id,
            'user_id': self._anonymize_user_id(session.user_id),
            'platform': session.platform,
            'start_time': session.start_time,
            'end_time': session.end_time,
            'version': session.version,
            
            # 통계 정보
            'statistics': {
                'total_events': session.total_events,
                'total_messages': session.total_messages,
                'total_tools_used': session.total_tools_used,
                'agents_used': session.agents_used,
                'session_duration': None
            },
            
            # 모델 정보 (민감하지 않은 정보만)
            'model_info': {
                'provider': session.model_info.get('provider') if session.model_info else None,
                'model_type': session.model_info.get('display_name') if session.model_info else None
            } if session.model_info else None,
            
            # 이벤트 데이터
            'events': []
        }
        
        # 세션 시간 계산
        if session.start_time and session.end_time:
            try:
                start = datetime.fromisoformat(session.start_time.replace('Z', '+00:00'))
                end = datetime.fromisoformat(session.end_time.replace('Z', '+00:00'))
                session_data['statistics']['session_duration'] = (end - start).total_seconds()
            except:
                pass
        
        # 이벤트 데이터 처리
        for event in session.events:
            event_data = {
                'event_id': event.event_id,
                'event_type': event.event_type.value,
                'timestamp': event.timestamp,
                'agent_name': event.agent_name,
                'tool_name': event.tool_name,
                'execution_time': event.execution_time,
                'step_count': event.step_count,
                'error_message': event.error_message
            }
            
            # 컨텐츠 포함 여부 결정
            if self.include_content and event.content:
                if self.anonymize_data:
                    event_data['content'] = self._sanitize_content(event.content)
                else:
                    event_data['content'] = event.content
            else:
                # 컨텐츠 길이만 포함
                event_data['content_length'] = len(event.content) if event.content else 0
            
            session_data['events'].append(event_data)
        
        return session_data
    
    async def collect_session(self, session: ConversationSession, 
                            immediate_send: bool = False) -> bool:
        """세션 데이터 수집"""
        
        if not self.enable_collection:
            logger.debug("Data collection is disabled")
            return False
        
        try:
            # 세션 데이터 준비
            session_data = self._prepare_session_data(session)
            
            # 메타데이터 추가
            collection_data = {
                'type': 'conversation_session',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'source': 'decepticon',
                'data': session_data
            }
            
            if immediate_send:
                return await self._send_to_server(collection_data)
            else:
                # 큐에 추가 (나중에 배치 전송)
                self.pending_queue.append(collection_data)
                
                # 큐 크기 제한
                if len(self.pending_queue) > self.max_queue_size:
                    self.pending_queue.pop(0)  # 오래된 데이터 제거
                
                logger.debug(f"Session data queued for collection (queue size: {len(self.pending_queue)})")
                return True
        
        except Exception as e:
            logger.error(f"Failed to collect session data: {str(e)}")
            return False
    
    async def _send_to_server(self, data: Dict[str, Any]) -> bool:
        """서버로 데이터 전송"""
        
        if not self.collection_endpoint:
            logger.warning("No collection endpoint configured")
            return False
        
        try:
            # 데이터 압축
            json_data = json.dumps(data, ensure_ascii=False)
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            headers = {
                'Content-Type': 'application/json',
                'Content-Encoding': 'gzip',
                'User-Agent': 'Decepticon/1.0.0'
            }
            
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.collection_endpoint,
                    data=compressed_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Data sent successfully: {result.get('message', 'OK')}")
                        return True
                    else:
                        logger.error(f"Server returned status {response.status}: {await response.text()}")
                        return False
        
        except aiohttp.ClientError as e:
            logger.error(f"Network error sending data: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending data: {str(e)}")
            return False
    
    async def flush_queue(self) -> Dict[str, int]:
        """큐에 있는 모든 데이터 전송"""
        
        if not self.pending_queue:
            return {'sent': 0, 'failed': 0}
        
        sent_count = 0
        failed_count = 0
        
        logger.info(f"Flushing queue with {len(self.pending_queue)} items")
        
        # 배치로 전송 (한 번에 최대 10개)
        batch_size = 10
        
        while self.pending_queue:
            batch = self.pending_queue[:batch_size]
            self.pending_queue = self.pending_queue[batch_size:]
            
            # 배치 데이터 생성
            batch_data = {
                'type': 'batch_collection',
                'timestamp': datetime.utcnow().isoformat(),
                'version': '1.0.0',
                'source': 'decepticon',
                'batch_size': len(batch),
                'data': batch
            }
            
            if await self._send_to_server(batch_data):
                sent_count += len(batch)
            else:
                failed_count += len(batch)
                # 실패한 배치는 다시 큐에 추가 (맨 앞에)
                self.pending_queue = batch + self.pending_queue
                break
        
        logger.info(f"Queue flush completed: {sent_count} sent, {failed_count} failed")
        return {'sent': sent_count, 'failed': failed_count}
    
    def save_queue_to_file(self, file_path: str) -> bool:
        """큐를 파일로 저장 (오프라인 백업)"""
        
        if not self.pending_queue:
            return True
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'saved_at': datetime.utcnow().isoformat(),
                    'queue_size': len(self.pending_queue),
                    'data': self.pending_queue
                }, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Queue saved to file: {file_path} ({len(self.pending_queue)} items)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save queue to file: {str(e)}")
            return False
    
    def load_queue_from_file(self, file_path: str) -> bool:
        """파일에서 큐 로드"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            self.pending_queue.extend(backup_data.get('data', []))
            
            # 큐 크기 제한
            if len(self.pending_queue) > self.max_queue_size:
                self.pending_queue = self.pending_queue[-self.max_queue_size:]
            
            logger.info(f"Queue loaded from file: {file_path} ({len(backup_data.get('data', []))} items)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load queue from file: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """수집 통계 반환"""
        return {
            'collection_enabled': self.enable_collection,
            'queue_size': len(self.pending_queue),
            'anonymize_data': self.anonymize_data,
            'include_content': self.include_content,
            'endpoint': self.collection_endpoint,
            'has_api_key': bool(self.api_key)
        }

class PrivacyManager:
    """개인정보 보호 관리"""
    
    @staticmethod
    def create_opt_out_file(user_id: str) -> bool:
        """사용자 데이터 수집 거부 파일 생성"""
        try:
            opt_out_dir = Path("user_preferences")
            opt_out_dir.mkdir(exist_ok=True)
            
            opt_out_file = opt_out_dir / f"{user_id}_opt_out.json"
            
            opt_out_data = {
                'user_id': user_id,
                'opted_out_at': datetime.utcnow().isoformat(),
                'data_collection': False,
                'analytics': False,
                'note': 'User has opted out of all data collection'
            }
            
            with open(opt_out_file, 'w', encoding='utf-8') as f:
                json.dump(opt_out_data, f, indent=2)
            
            logger.info(f"Opt-out file created for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create opt-out file: {str(e)}")
            return False
    
    @staticmethod
    def check_user_consent(user_id: str) -> bool:
        """사용자 동의 여부 확인"""
        try:
            opt_out_file = Path("user_preferences") / f"{user_id}_opt_out.json"
            
            if opt_out_file.exists():
                with open(opt_out_file, 'r', encoding='utf-8') as f:
                    opt_out_data = json.load(f)
                return not opt_out_data.get('data_collection', True)
            
            # 파일이 없으면 기본적으로 동의한 것으로 간주 (opt-in)
            return True
            
        except Exception as e:
            logger.error(f"Error checking user consent: {str(e)}")
            return False  # 에러 시 안전하게 수집 거부

# 전역 데이터 수집기 인스턴스
_global_collector: Optional[DataCollector] = None

def get_data_collector() -> DataCollector:
    """전역 데이터 수집기 인스턴스 반환"""
    global _global_collector
    if _global_collector is None:
        _global_collector = DataCollector()
    return _global_collector

def configure_data_collection(endpoint: Optional[str] = None,
                            api_key: Optional[str] = None,
                            enable: bool = False,
                            anonymize: bool = True,
                            include_content: bool = True) -> DataCollector:
    """데이터 수집 설정"""
    global _global_collector
    
    _global_collector = DataCollector(
        collection_endpoint=endpoint,
        api_key=api_key,
        enable_collection=enable
    )
    
    _global_collector.anonymize_data = anonymize
    _global_collector.include_content = include_content
    
    logger.info(f"Data collection configured (enabled: {enable}, anonymize: {anonymize})")
    return _global_collector
