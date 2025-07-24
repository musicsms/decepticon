"""
Frontend Utils - Direct CLI Execution을 위한 유틸리티 함수들
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv


def get_env_config() -> Dict[str, Any]:
    """환경 설정 로드"""
    load_dotenv()
    
    return {
        "debug_mode": os.getenv("DEBUG_MODE", "false").lower() == "true",
        "theme": os.getenv("THEME", "dark"),
        "docker_container": os.getenv("DOCKER_CONTAINER", "decepticon-kali"),
        "chat_height": int(os.getenv("CHAT_HEIGHT", "700"))
    }


def log_debug(message: str, data=None):
    """디버그 로깅"""
    config = get_env_config()
    if config.get("debug_mode", False):
        print(f"[DEBUG] {message}")
        if data:
            print(f"[DEBUG] Data: {data}")


def validate_environment() -> Dict[str, Any]:
    """환경 설정 검증"""
    config = get_env_config()
    validation_result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "config": config
    }
    
    # API 키 확인
    api_keys = ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY"]
    available_keys = []
    
    for key in api_keys:
        value = os.getenv(key)
        if value and value != "your-api-key":
            available_keys.append(key)
    
    if not available_keys:
        validation_result["errors"].append("No API keys configured")
        validation_result["valid"] = False
    else:
        validation_result["warnings"].append(f"Available API keys: {', '.join(available_keys)}")
    
    # CLI 모듈 확인
    try:
        from src.graphs.swarm import create_dynamic_swarm
        from src.utils.message import extract_message_content
    except ImportError as e:
        validation_result["errors"].append(f"CLI modules not available: {str(e)}")
        validation_result["valid"] = False
    
    return validation_result
