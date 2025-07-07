from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List
import subprocess
import uuid


mcp = FastMCP("terminal", port=3003)

CONTAINER_NAME = "attacker"

def run(command: List[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["docker", "exec", CONTAINER_NAME, "tmux"] + command,
        capture_output=True, text=True, encoding='utf-8'
    )

@mcp.tool(description="Create new terminal session")
def create_session() -> Annotated[str, "Session ID"]:
    """새 tmux 터미널 세션 생성"""
    session_id = str(uuid.uuid4())[:8]
    result = run(["new-session", "-d", "-s", session_id])
    if result.returncode != 0:
        raise Exception(f"Failed to create session: {result.stderr}")
    return session_id
    

@mcp.tool(description="List all active sessions")
def session_list() -> Annotated[List[str], "List of session IDs"]:
    result = run(["list-sessions"])
    if result.returncode != 0:
        return []
    return [line.split(":")[0].strip() for line in result.stdout.strip().split('\n') if line.strip()]

# @mcp.tool(description="Split pane in tmux session")
# def split_pane(
#     session_id: Annotated[str, "Session ID"],
# ) -> Annotated[int, "New pane index"]:
#     run(["split-window", "-t", session_id])
#     result = run(["list-panes", "-t", session_id, "-F", "#{pane_index}"])
#     panes = [int(x) for x in result.stdout.strip().split("\n")]
#     return max(panes)
    
@mcp.tool(description="Execute command in session")
def command_exec(
    session_id: Annotated[str, "Session ID"],
    command: Annotated[str, "Command to execute"],
) -> Annotated[str, "Command output"]:
    """command execute"""
    try:
        channel = f"done-{session_id}"

        full_command = f"({command}); tmux wait-for -S {channel}"
        result = run(["send-keys", "-t", session_id, full_command, "Enter"])
        
        if result.returncode != 0:
            raise Exception(f"Failed to execute command: {result.stderr}")
        
        wait_result = run(["wait-for", channel])
        if wait_result.returncode != 0:
            raise Exception(f"Command execution monitoring failed: {wait_result.stderr}")
        
        capture_result = run(["capture-pane", "-t", session_id, "-p"])
        
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
        run(["kill-session", "-t", session_id])
        
        # 세션이 이미 없어도 성공으로 간주
        return f"Session {session_id} killed"

    except Exception as e:
        return f"Session {session_id} killed (with warning: {str(e)})"

@mcp.tool(description="Kill server, Kill all session")
def kill_server() -> Annotated[str, "Session ID"]:
    try:
        run(["kill-server"])    
        # 세션이 이미 없어도 성공으로 간주
        return f"Server killed"

    except Exception as e:
        return f"Server killed (with warning: {str(e)})"


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
