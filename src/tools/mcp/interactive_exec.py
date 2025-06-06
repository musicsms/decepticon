from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import Dict
import subprocess
import threading
import uuid

mcp = FastMCP("interactive_exec", port=3003)

# 세션 관리
sessions: Dict[str, bool] = {}
session_lock = threading.Lock()
CONTAINER_NAME = "attacker"


@mcp.tool(description="Create persistent terminal session")
def create_session() -> Annotated[str, "Session ID"]:
    """터미널 세션 생성"""
    # tmux 세션 생성하고 실제 세션 이름 받아오기
    session_id = session_id = str(uuid.uuid4())[:8]  # 
    result = subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "tmux", "new-session", "-d", "-s", session_id, "-P"], # -d : 백그라운드 실행
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if result.returncode != 0:
        raise Exception(f"Failed to create tmux session: {result.stderr}")
    
    
    with session_lock:
        sessions[session_id] = True
    
    return session_id


@mcp.tool(description="Execute command in persistent session")
def interactive_exec(
    command: Annotated[str, "Interactive shell command"],
    session_id: Annotated[str, "Session ID"]
) -> Annotated[str, "Session ID and command result"]:
    """대화형 셸 명령어 실행"""
    if session_id not in sessions:
        raise Exception(f"Session '{session_id}' not found")
    
    # tmux 세션에 명령어 전송
    subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "tmux", "send-keys", "-t", session_id, command, "Enter"],
        capture_output=True, encoding='utf-8'
    )
    
    # 출력 캡처
    import time
    time.sleep(0.5)
    
    result = subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "tmux", "capture-pane", "-t", session_id, "-p"],
        capture_output=True, text=True, encoding='utf-8'
    )
    
    if result.returncode == 0:
        return result.stdout.strip()  # ✅ 전체 출력
    else:
        return result.stderr.strip()


@mcp.tool(description="Terminate persistent session")
def kill_session(
    session_id: Annotated[str, "Session ID to kill"]
) -> Annotated[str, "Result"]:
    """터미널 세션 종료"""
    if session_id not in sessions:
        raise Exception(f"Session '{session_id}' not found")
    
    # tmux 세션 종료
    subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "tmux", "kill-session", "-t", session_id],
        capture_output=True, encoding='utf-8'
    )
    
    with session_lock:
        del sessions[session_id]
    
    return f"killed {session_id}"

if __name__ == "__main__":
    mcp.run(transport="streamable-http")
