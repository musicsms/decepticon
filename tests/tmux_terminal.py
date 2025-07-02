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
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.returncode != 0:
            raise Exception(f"Failed to create session: {result.stderr}")
        
        return session_id
        
    except Exception as e:
        raise Exception(f"Failed to create session: {str(e)}")


@mcp.tool(description="List all active tmux sessions")
def session_list() -> Annotated[List[str], "List of session IDs"]:
    """활성 tmux 세션 목록"""
    try:
        result = subprocess.run(
            ["docker", "exec", CONTAINER_NAME, "tmux", "list-sessions"],
            capture_output=True, text=True, encoding='utf-8'
        )
        
        if result.returncode != 0:
            return []
        
        session_ids = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                session_id = line.split(':')[0].strip()
                session_ids.append(session_id)
        
        return session_ids
        
    except Exception as e:
        return []


@mcp.tool(description="Execute command and get clean output")
def command_exec(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
) -> Annotated[str, "Command output"]:
    """명령어 실행 후 깔끔한 출력 반환 (프롬프트 + 명령어 + 결과)"""
    try:
        # 1. 화면 클리어
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, "clear", "Enter"
        ])
        
        time.sleep(0.5)  # clear 완료 대기
        
        # 2. 명령어 실행
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, command, "Enter"
        ])
        
       
        
        # 4. 전체 화면 캡처 (clear 후 내용만 나옴)
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Failed to capture output: {result.stderr}")
        
        # 5. 빈 줄 제거하고 깔끔하게 정리
        output = result.stdout.strip()
        return output
        
    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")


@mcp.tool(description="Execute command without clearing screen")
def command_exec_no_clear(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
    wait_time: Annotated[int, "Wait time in seconds"] = 3
) -> Annotated[str, "Command output"]:
    """화면 클리어 없이 명령어 실행"""
    try:
        # 명령어 실행
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, command, "Enter"
        ])
        
        time.sleep(wait_time)
        
        # 화면 캡처
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ], capture_output=True, text=True)
        
        return result.stdout.strip()
        
    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")


@mcp.tool(description="Execute command with marker-based output")
def command_exec_with_marker(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"]
) -> Annotated[str, "Command output only"]:
    """마커를 사용해서 명령어 출력만 정확히 캡처"""
    try:
        # 고유한 시작/종료 마커 생성
        start_marker = f"===START_{int(time.time())}_{session_id[:4]}==="
        end_marker = f"===END_{int(time.time())}_{session_id[:4]}==="
        
        # 시작 마커 출력
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, f"echo '{start_marker}'", "Enter"
        ])
        
        time.sleep(0.5)
        
        # 실제 명령어 실행
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, command, "Enter"
        ])
        
        # 명령어 완료까지 대기 (프롬프트 나타날 때까지)
        max_wait = 300  # 5분
        for i in range(max_wait):
            time.sleep(1)
            
            result = subprocess.run([
                "docker", "exec", CONTAINER_NAME, "tmux", 
                "capture-pane", "-t", session_id, "-p"
            ], capture_output=True, text=True)
            
            lines = result.stdout.strip().split('\n')
            last_line = lines[-1] if lines else ""
            
            # 프롬프트 패턴 확인
            if (last_line.endswith('$ ') or last_line.endswith('# ') or 
                last_line.endswith('> ') or last_line.endswith('$') or 
                last_line.endswith('#') or last_line.endswith('>')):
                break
        
        # 종료 마커 출력
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, f"echo '{end_marker}'", "Enter"
        ])
        
        time.sleep(0.5)
        
        # 전체 출력 캡처
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ], capture_output=True, text=True)
        
        # 마커 사이의 내용만 추출
        output_lines = result.stdout.split('\n')
        start_idx = -1
        end_idx = -1
        
        for i, line in enumerate(output_lines):
            if start_marker in line:
                start_idx = i + 1  # 마커 다음 줄부터
            elif end_marker in line:
                end_idx = i  # 마커 이전 줄까지
                break
        
        if start_idx != -1 and end_idx != -1:
            command_output = '\n'.join(output_lines[start_idx:end_idx])
            return command_output.strip()
        else:
            return "Failed to extract command output"
        
    except Exception as e:
        raise Exception(f"Failed to execute command with marker: {str(e)}")


@mcp.tool(description="Get current session output")
def session_capture(
    session_id: Annotated[str, "Session ID"]
) -> Annotated[str, "Current session output"]:
    """현재 세션 화면 캡처"""
    try:
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ], capture_output=True, text=True)
        
        return result.stdout.strip()
        
    except Exception as e:
        raise Exception(f"Failed to capture session: {str(e)}")


@mcp.tool(description="Kill tmux session")
def session_kill(
    session_id: Annotated[str, "Session ID to kill"]
) -> Annotated[str, "Result"]:
    """tmux 세션 종료"""
    try:
        subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "kill-session", "-t", session_id
        ])
        
        return f"Session {session_id} killed"
        
    except Exception as e:
        return f"Session {session_id} killed (with warning: {str(e)})"


@mcp.tool(description="Check if session exists")
def session_exists(
    session_id: Annotated[str, "Session ID to check"]
) -> Annotated[bool, "True if session exists"]:
    """세션 존재 여부 확인"""
    try:
        result = subprocess.run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "has-session", "-t", session_id
        ], capture_output=True)
        
        return result.returncode == 0
        
    except Exception:
        return False



if __name__ == "__main__":
    mcp.run(transport="streamable-http")
