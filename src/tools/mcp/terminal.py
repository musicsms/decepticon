# from mcp.server.fastmcp import FastMCP
# from typing_extensions import Annotated
# from typing import Dict
# import subprocess
# import threading
# import uuid

# mcp = FastMCP("interactive_exec", port=3003)

# # 세션 관리
# sessions: Dict[str, bool] = {}
# session_lock = threading.Lock()
# CONTAINER_NAME = "attacker"


# @mcp.tool(description="Create persistent terminal session")
# def create_session() -> Annotated[str, "Session ID"]:
#     """터미널 세션 생성"""
#     # tmux 세션 생성하고 실제 세션 이름 받아오기
#     session_id = session_id = str(uuid.uuid4())[:8]  # 
#     result = subprocess.run(
#         ["docker", "exec", CONTAINER_NAME, "tmux", "new-session", "-d", "-s", session_id, "-P"], # -d : 백그라운드 실행
#         capture_output=True, text=True, encoding='utf-8'
#     )
    
#     if result.returncode != 0:
#         raise Exception(f"Failed to create tmux session: {result.stderr}")
    
    
#     with session_lock:
#         sessions[session_id] = True
    
#     return session_id


# @mcp.tool(description="Execute command in persistent session")
# def interactive_exec(
#     command: Annotated[str, "Interactive shell command"],
#     session_id: Annotated[str, "Session ID"]
# ) -> Annotated[str, "Session ID and command result"]:
#     """대화형 셸 명령어 실행"""
#     if session_id not in sessions:
#         raise Exception(f"Session '{session_id}' not found")
    
#     # tmux 세션에 명령어 전송
#     subprocess.run(
#         ["docker", "exec", CONTAINER_NAME, "tmux", "send-keys", "-t", session_id, command, "Enter"],
#         capture_output=True, encoding='utf-8'
#     )
    
#     # 출력 캡처
#     import time
#     time.sleep(0.5)
    
#     result = subprocess.run(
#         ["docker", "exec", CONTAINER_NAME, "tmux", "capture-pane", "-t", session_id, "-p"],
#         capture_output=True, text=True, encoding='utf-8'
#     )
    
#     if result.returncode == 0:
#         return result.stdout.strip()  # ✅ 전체 출력
#     else:
#         return result.stderr.strip()


# @mcp.tool(description="Terminate persistent session")
# def kill_session(
#     session_id: Annotated[str, "Session ID to kill"]
# ) -> Annotated[str, "Result"]:
#     """터미널 세션 종료"""
#     if session_id not in sessions:
#         raise Exception(f"Session '{session_id}' not found")
    
#     # tmux 세션 종료
#     subprocess.run(
#         ["docker", "exec", CONTAINER_NAME, "tmux", "kill-session", "-t", session_id],
#         capture_output=True, encoding='utf-8'
#     )
    
#     with session_lock:
#         del sessions[session_id]
    
#     return f"killed {session_id}"

# if __name__ == "__main__":
#     mcp.run(transport="streamable-http")

from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List
import subprocess
import uuid
import time

mcp = FastMCP("terminal", port=3003)

CONTAINER_NAME = "attacker"


@mcp.tool(description="Create new terminal session")
def create_session() -> Annotated[str, "Session ID"]:
    """새 tmux 터미널 세션 생성"""
    session_id = str(uuid.uuid4())[:8]
    
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "new-session", "-d", "-s", session_id],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to create session: {result.stderr}")
        
        return session_id
    
    except Exception as e:
        raise Exception(f"Failed to create session: {str(e)}")

@mcp.tool(description="List all active sessions")
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
    
    except Exception as e:
        return []

@mcp.tool(description="Execute command in tmux session")
def command_exec(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
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
        time.sleep(0.5)
        
        # 출력 캡처
        capture_result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "capture-pane", "-t", session_id, "-p"],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if capture_result.returncode != 0:
            raise Exception(f"Failed to capture output: {capture_result.stderr}")
        
        return capture_result.stdout.strip()

    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")


@mcp.tool(description="Kill session")
def kill_session(
    session_id: Annotated[str, "Session ID to kill"]
) -> Annotated[str, "Result"]:
    """tmux 세션 종료"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "kill-session", "-t", session_id],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        # 세션이 이미 없어도 성공으로 간주
        return f"Session {session_id} killed"

    except Exception as e:
        return f"Session {session_id} killed (with warning: {str(e)})"

@mcp.tool(description="Kill server, Kill all session")
def kill_server() -> Annotated[str, "Session ID"]:
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "kill-server"],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        # 세션이 이미 없어도 성공으로 간주
        return f"Server killed"

    except Exception as e:
        return f"Server killed (with warning: {str(e)})"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
