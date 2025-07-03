from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List
import subprocess
import uuid
import time

mcp = FastMCP("tmux_terminal", port=3006)

CONTAINER_NAME = "attacker"


@mcp.tool(description="Create new tmux terminal session")
def session_create() -> Annotated[str, "Session ID"]:
    """새 tmux 터미널 세션 생성"""
    session_id = str(uuid.uuid4())[:8]
    
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "new-session", "-d", "-s", session_id],
            capture_output=True, text=True, encoding='utf-8', timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to create session: {result.stderr}")
        
        return session_id
        
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while creating session")
    except Exception as e:
        raise Exception(f"Failed to create session: {str(e)}")


@mcp.tool(description="List all active tmux sessions")
def session_list() -> Annotated[List[str], "List of session IDs"]:
    """활성 tmux 세션 목록"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "list-sessions"],
            capture_output=True, text=True, encoding='utf-8', timeout=10
        )
        
        if result.returncode != 0:
            # tmux 세션이 없을 때는 빈 리스트 반환
            return []
        
        session_ids = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                session_id = line.split(':')[0].strip()
                session_ids.append(session_id)
        
        return session_ids
        
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while listing sessions")
    except Exception as e:
        return []


@mcp.tool(description="Execute command in tmux session")
def command_exec(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
    wait_time: Annotated[float, "Wait time after command in seconds"] = 1.0
) -> Annotated[str, "Command output"]:
    """tmux 세션에서 명령어 실행"""
    try:
        # 명령어 전송
        send_result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "send-keys", "-t", session_id, command, "Enter"],
            capture_output=True, text=True, encoding='utf-8', timeout=5
        )
        
        if send_result.returncode != 0:
            raise Exception(f"Failed to send command: {send_result.stderr}")
        
        # 명령어 실행 완료 대기
        time.sleep(wait_time)
        
        # 출력 캡처
        capture_result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "capture-pane", "-t", session_id, "-p"],
            capture_output=True, text=True, encoding='utf-8', timeout=10
        )
        
        if capture_result.returncode != 0:
            raise Exception(f"Failed to capture output: {capture_result.stderr}")
        
        return capture_result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while executing command")
    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")


@mcp.tool(description="Capture current tmux session output")
def session_capture(
    session_id: Annotated[str, "Session ID"]
) -> Annotated[str, "Session output"]:
    """tmux 세션의 현재 출력 캡처"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "capture-pane", "-t", session_id, "-p"],
            capture_output=True, text=True, encoding='utf-8', timeout=10
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to capture session output: {result.stderr}")
        
        return result.stdout.strip()
        
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while capturing session output")
    except Exception as e:
        raise Exception(f"Failed to capture session output: {str(e)}")


@mcp.tool(description="Kill tmux session")
def session_kill(
    session_id: Annotated[str, "Session ID to kill"]
) -> Annotated[str, "Result"]:
    """tmux 세션 종료"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "kill-session", "-t", session_id],
            capture_output=True, text=True, encoding='utf-8', timeout=10
        )
        
        # 세션이 이미 없어도 성공으로 간주
        return f"Session {session_id} killed"
        
    except subprocess.TimeoutExpired:
        raise Exception("Timeout while killing session")
    except Exception as e:
        return f"Session {session_id} killed (with warning: {str(e)})"


@mcp.tool(description="Check if tmux session exists")
def session_exists(
    session_id: Annotated[str, "Session ID to check"]
) -> Annotated[bool, "True if session exists"]:
    """tmux 세션 존재 여부 확인"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "has-session", "-t", session_id],
            capture_output=True, text=True, encoding='utf-8', timeout=5
        )
        
        return result.returncode == 0
        
    except Exception:
        return False


@mcp.tool(description="Clear tmux session screen")
def session_clear(
    session_id: Annotated[str, "Session ID"]
) -> Annotated[str, "Result"]:
    """tmux 세션 화면 지우기"""
    try:
        subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "send-keys", "-t", session_id, "clear", "Enter"],
            capture_output=True, text=True, encoding='utf-8', timeout=5
        )
        
        return f"Session {session_id} screen cleared"
        
    except Exception as e:
        raise Exception(f"Failed to clear session: {str(e)}")


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
