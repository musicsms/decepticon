import os
import sys
import locale

# Windows 인코딩 문제 해결
if sys.platform.startswith('win'):
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass

from mcp.server.fastmcp import FastMCP
from typing_extensions import Annotated
from typing import List, Dict
import subprocess
import uuid
import time
import threading
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

mcp = FastMCP("tmux_terminal", port=3006)

CONTAINER_NAME = "attacker"

# Flask 앱 및 SocketIO 설정
app = Flask(__name__)
app.config['SECRET_KEY'] = 'tmux_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# 활성 스트리밍 세션들
streaming_sessions = {}
streaming_threads = {}
session_last_content = {}  # 마지막 캡쳐된 내용 저장


def safe_subprocess_run(cmd, **kwargs):
    """인코딩 안전한 subprocess 실행"""
    default_kwargs = {
        'encoding': 'utf-8',
        'errors': 'ignore',
        'capture_output': True,
        'text': True
    }
    default_kwargs.update(kwargs)
    return subprocess.run(cmd, **default_kwargs)


def stream_session_output_polling(session_id):
    """polling 방식으로 세션 출력을 실시간 스트리밍"""
    print(f"Starting polling stream for session: {session_id}")
    
    while streaming_sessions.get(session_id, False):
        try:
            # tmux capture-pane으로 현재 화면 내용 가져오기
            result = safe_subprocess_run([
                "docker", "exec", CONTAINER_NAME, "tmux", 
                "capture-pane", "-t", session_id, "-p"
            ])
            
            if result.returncode == 0:
                current_content = result.stdout
                last_content = session_last_content.get(session_id, "")
                
                # 내용이 변경되었으면 전송
                if current_content != last_content:
                    session_last_content[session_id] = current_content
                    
                    # WebSocket으로 전체 화면 내용 전송
                    socketio.emit('terminal_update', {
                        'session_id': session_id,
                        'content': current_content,
                        'timestamp': time.time()
                    }, namespace='/terminal')
                    
                    print(f"Content updated for session {session_id}")
            
            time.sleep(0.5)  # 500ms마다 체크
            
        except Exception as e:
            print(f"Polling error for {session_id}: {e}")
            break
    
    print(f"Stopped polling stream for session: {session_id}")


# HTML 템플릿
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Real-time tmux Terminal</title>
    <meta charset="UTF-8">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body {
            font-family: 'Courier New', monospace;
            background: #1e1e1e;
            color: #00ff00;
            margin: 0;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .controls {
            background: #333;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .controls input, .controls button, .controls select {
            margin: 5px;
            padding: 8px;
            font-family: 'Courier New', monospace;
        }
        
        .terminal {
            background: #000;
            border: 2px solid #333;
            border-radius: 5px;
            padding: 15px;
            height: 600px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
            line-height: 1.4;
            font-family: 'Courier New', monospace;
        }
        
        .terminal::-webkit-scrollbar {
            width: 8px;
        }
        
        .terminal::-webkit-scrollbar-track {
            background: #333;
        }
        
        .terminal::-webkit-scrollbar-thumb {
            background: #666;
            border-radius: 4px;
        }
        
        .status {
            margin-bottom: 10px;
            padding: 10px;
            background: #222;
            border-radius: 3px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .connected { color: #00ff00; }
        .disconnected { color: #ff0000; }
        .updating { color: #ffff00; }
        
        .command-input {
            margin-top: 15px;
        }
        
        .command-input input {
            width: 70%;
            padding: 10px;
            font-family: 'Courier New', monospace;
            background: #333;
            color: #fff;
            border: 1px solid #666;
        }
        
        .command-input button {
            padding: 10px 20px;
            background: #007700;
            color: white;
            border: none;
            cursor: pointer;
        }
        
        .command-input button:hover {
            background: #009900;
        }
        
        h1 {
            color: #00ff00;
            text-shadow: 0 0 10px #00ff00;
        }
        
        .update-indicator {
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Real-time tmux Terminal Monitor</h1>
        
        <div class="controls">
            <label>Session ID:</label>
            <input type="text" id="sessionId" placeholder="Enter session ID">
            <button onclick="connectToSession()">Connect</button>
            <button onclick="disconnectSession()">Disconnect</button>
            <button onclick="clearTerminal()">Clear Display</button>
            <button onclick="refreshNow()">Refresh Now</button>
            
            <br>
            
            <label>Quick Actions:</label>
            <select id="quickCommands">
                <option value="">Select command...</option>
                <option value="whoami">whoami</option>
                <option value="pwd">pwd</option>
                <option value="ls -la">ls -la</option>
                <option value="ps aux">ps aux</option>
                <option value="netstat -tuln">netstat -tuln</option>
                <option value="nmap --version">nmap --version</option>
                <option value="nmap -sn 127.0.0.1">nmap -sn 127.0.0.1</option>
                <option value="top">top</option>
                <option value="htop">htop</option>
            </select>
            <button onclick="executeQuickCommand()">Execute</button>
        </div>
        
        <div class="status" id="status">
            <span class="disconnected">● Disconnected</span>
            <span class="update-indicator" id="updateIndicator">Ready</span>
        </div>
        
        <div class="terminal" id="terminal">
            <div style="color: #666;">🚀 Terminal ready - Enter session ID and click Connect...
            
This interface polls tmux every 500ms for real-time updates.
            </div>
        </div>
        
        <div class="command-input">
            <input type="text" id="commandInput" placeholder="Enter command..." onkeypress="handleKeyPress(event)">
            <button onclick="executeCommand()">Execute</button>
        </div>
    </div>

    <script>
        const socket = io('/terminal');
        let currentSessionId = null;
        let isConnected = false;
        let updateCount = 0;
        
        const terminal = document.getElementById('terminal');
        const status = document.getElementById('status');
        const commandInput = document.getElementById('commandInput');
        const updateIndicator = document.getElementById('updateIndicator');
        
        // Socket.IO 이벤트 핸들러
        socket.on('connect', function() {
            console.log('Socket connected');
        });
        
        socket.on('disconnect', function() {
            console.log('Socket disconnected');
            updateStatus(false);
        });
        
        socket.on('terminal_update', function(data) {
            if (data.session_id === currentSessionId) {
                updateCount++;
                terminal.textContent = data.content;
                terminal.scrollTop = terminal.scrollHeight;
                
                // 업데이트 표시
                updateIndicator.textContent = `Updated: ${updateCount} (${new Date().toLocaleTimeString()})`;
                updateIndicator.className = 'update-indicator updating';
                
                setTimeout(() => {
                    updateIndicator.className = 'update-indicator';
                }, 1000);
            }
        });
        
        socket.on('session_connected', function(data) {
            updateStatus(true, data.session_id);
            updateCount = 0;
        });
        
        socket.on('session_error', function(data) {
            appendToTerminal('\\n[ERROR] ' + data.message + '\\n');
        });
        
        socket.on('debug_message', function(data) {
            console.log('Debug:', data.message);
        });
        
        // 함수들
        function connectToSession() {
            const sessionId = document.getElementById('sessionId').value.trim();
            if (!sessionId) {
                alert('Please enter session ID');
                return;
            }
            
            currentSessionId = sessionId;
            clearTerminal();
            appendToTerminal(`🔌 Connecting to session: ${sessionId}...\\n`);
            
            socket.emit('connect_session', {session_id: sessionId});
        }
        
        function disconnectSession() {
            if (currentSessionId) {
                socket.emit('disconnect_session', {session_id: currentSessionId});
                currentSessionId = null;
                updateStatus(false);
                appendToTerminal('\\n🔌 [DISCONNECTED]\\n');
                updateIndicator.textContent = 'Disconnected';
            }
        }
        
        function executeCommand() {
            const command = commandInput.value.trim();
            if (!command || !currentSessionId) return;
            
            socket.emit('execute_command', {
                session_id: currentSessionId,
                command: command
            });
            
            commandInput.value = '';
        }
        
        function executeQuickCommand() {
            const select = document.getElementById('quickCommands');
            const command = select.value;
            if (command && currentSessionId) {
                socket.emit('execute_command', {
                    session_id: currentSessionId,
                    command: command
                });
            }
        }
        
        function clearTerminal() {
            terminal.innerHTML = '';
        }
        
        function appendToTerminal(text) {
            terminal.textContent += text;
            terminal.scrollTop = terminal.scrollHeight;
        }
        
        function refreshNow() {
            if (currentSessionId) {
                socket.emit('force_refresh', {session_id: currentSessionId});
            }
        }
        
        function updateStatus(connected, sessionId = null) {
            isConnected = connected;
            if (connected) {
                status.innerHTML = `<span class="connected">● Connected to session: ${sessionId || currentSessionId}</span><span class="update-indicator" id="updateIndicator">Polling...</span>`;
            } else {
                status.innerHTML = '<span class="disconnected">● Disconnected</span><span class="update-indicator" id="updateIndicator">Ready</span>';
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                executeCommand();
            }
        }
        
        // 페이지 로드 시 초기화
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Terminal interface loaded');
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """웹 터미널 페이지"""
    return render_template_string(HTML_TEMPLATE)


@socketio.on('connect', namespace='/terminal')
def handle_connect():
    """WebSocket 연결"""
    print('Client connected to WebSocket')
    emit('debug_message', {'message': 'WebSocket connected successfully'})


@socketio.on('disconnect', namespace='/terminal')
def handle_disconnect():
    """WebSocket 연결 해제"""
    print('Client disconnected from WebSocket')


@socketio.on('connect_session', namespace='/terminal')
def handle_connect_session(data):
    """터미널 세션 연결"""
    session_id = data.get('session_id')
    
    if not session_id:
        emit('session_error', {'message': 'Session ID required'})
        return
    
    # 세션 존재 확인
    try:
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "has-session", "-t", session_id
        ])
        
        if result.returncode != 0:
            emit('session_error', {'message': f'Session {session_id} not found'})
            return
        
        # 기존 스트리밍 중지
        if session_id in streaming_sessions:
            streaming_sessions[session_id] = False
            time.sleep(0.1)
        
        # 새 스트리밍 시작
        streaming_sessions[session_id] = True
        session_last_content[session_id] = ""
        
        # 스트리밍 스레드 시작
        thread = threading.Thread(target=stream_session_output_polling, args=(session_id,))
        thread.daemon = True
        thread.start()
        streaming_threads[session_id] = thread
        
        # 즉시 현재 화면 내용 전송
        current_output = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ])
        
        if current_output.returncode == 0:
            emit('terminal_update', {
                'session_id': session_id,
                'content': current_output.stdout,
                'timestamp': time.time()
            })
            session_last_content[session_id] = current_output.stdout
        
        emit('session_connected', {'session_id': session_id})
        emit('debug_message', {'message': f'Polling started for session {session_id}'})
        print(f'✅ Connected to session: {session_id}')
        
    except Exception as e:
        emit('session_error', {'message': f'Failed to connect: {str(e)}'})
        print(f'❌ Connection failed: {e}')


@socketio.on('disconnect_session', namespace='/terminal')
def handle_disconnect_session(data):
    """터미널 세션 연결 해제"""
    session_id = data.get('session_id')
    
    if session_id in streaming_sessions:
        streaming_sessions[session_id] = False
        if session_id in session_last_content:
            del session_last_content[session_id]
        print(f'🔌 Disconnected from session: {session_id}')


@socketio.on('execute_command', namespace='/terminal')
def handle_execute_command(data):
    """명령어 실행"""
    session_id = data.get('session_id')
    command = data.get('command')
    
    if not session_id or not command:
        emit('session_error', {'message': 'Session ID and command required'})
        return
    
    try:
        # 명령어 전송
        safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, command, "Enter"
        ], capture_output=False)
        
        print(f'⚡ Command executed in {session_id}: {command}')
        emit('debug_message', {'message': f'Command executed: {command}'})
        
    except Exception as e:
        emit('session_error', {'message': f'Failed to execute command: {str(e)}'})


@socketio.on('force_refresh', namespace='/terminal')
def handle_force_refresh(data):
    """강제 새로고침"""
    session_id = data.get('session_id')
    
    if not session_id:
        return
    
    try:
        current_output = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ])
        
        if current_output.returncode == 0:
            emit('terminal_update', {
                'session_id': session_id,
                'content': current_output.stdout,
                'timestamp': time.time()
            })
            print(f'🔄 Force refresh for session: {session_id}')
        
    except Exception as e:
        emit('session_error', {'message': f'Failed to refresh: {str(e)}'})


def start_web_server():
    """웹 서버 시작"""
    print("🌐 Starting Flask-SocketIO web server...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)


# 웹 서버를 별도 스레드에서 시작
web_server_thread = threading.Thread(target=start_web_server)
web_server_thread.daemon = True
web_server_thread.start()

time.sleep(2)  # 웹 서버 시작 대기


# MCP 도구들
@mcp.tool(description="Create new tmux terminal session")
def session_create() -> Annotated[str, "Session ID"]:
    """새 tmux 터미널 세션 생성"""
    session_id = str(uuid.uuid4())[:8]
    
    try:
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "new-session", "-d", "-s", session_id
        ])
        
        if result.returncode != 0:
            raise Exception(f"Failed to create session: {result.stderr}")
        
        print(f"✅ Session created: {session_id}")
        return session_id
        
    except Exception as e:
        raise Exception(f"Failed to create session: {str(e)}")


@mcp.tool(description="List all active tmux sessions")
def session_list() -> Annotated[List[str], "List of session IDs"]:
    """활성 tmux 세션 목록"""
    try:
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", "list-sessions"
        ])
        
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
    wait_time: Annotated[int, "Wait time in seconds"] = 3
) -> Annotated[str, "Command output"]:
    """명령어 실행 후 깔끔한 출력 반환"""
    try:
        # 화면 클리어
        safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, "clear", "Enter"
        ], capture_output=False)
        
        time.sleep(0.5)
        
        # 명령어 실행
        safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "send-keys", "-t", session_id, command, "Enter"
        ], capture_output=False)
        
        time.sleep(wait_time)
        
        # 출력 캡처
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ])
        
        return result.stdout.strip()
        
    except Exception as e:
        raise Exception(f"Failed to execute command: {str(e)}")


@mcp.tool(description="Start web streaming for session")
def session_start_web_streaming(
    session_id: Annotated[str, "Session ID"]
) -> Annotated[str, "Web streaming status"]:
    """세션의 웹 스트리밍 시작 (자동으로 시작됨)"""
    return f"🌐 Session {session_id} is ready for web streaming. Visit: http://localhost:5000"


@mcp.tool(description="Get current session output")
def session_capture(
    session_id: Annotated[str, "Session ID"]
) -> Annotated[str, "Current session output"]:
    """현재 세션 화면 캡처"""
    try:
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "capture-pane", "-t", session_id, "-p"
        ])
        
        return result.stdout.strip()
        
    except Exception as e:
        raise Exception(f"Failed to capture session: {str(e)}")


@mcp.tool(description="Kill tmux session")
def session_kill(
    session_id: Annotated[str, "Session ID to kill"]
) -> Annotated[str, "Result"]:
    """tmux 세션 종료"""
    try:
        # 스트리밍 중지
        if session_id in streaming_sessions:
            streaming_sessions[session_id] = False
        
        safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "kill-session", "-t", session_id
        ], capture_output=False)
        
        return f"Session {session_id} killed"
        
    except Exception as e:
        return f"Session {session_id} killed (with warning: {str(e)})"


@mcp.tool(description="Check if session exists")
def session_exists(
    session_id: Annotated[str, "Session ID to check"]
) -> Annotated[bool, "True if session exists"]:
    """세션 존재 여부 확인"""
    try:
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "tmux", 
            "has-session", "-t", session_id
        ])
        
        return result.returncode == 0
        
    except Exception:
        return False


@mcp.tool(description="Get web interface URL")
def get_web_url() -> Annotated[str, "Web interface URL"]:
    """웹 인터페이스 URL 반환"""
    return "🌐 Web Terminal Interface: http://localhost:5000"


@mcp.tool(description="Test docker container connection")
def test_connection() -> Annotated[str, "Connection test result"]:
    """Docker 컨테이너 연결 테스트"""
    try:
        result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "whoami"
        ])
        
        if result.returncode != 0:
            return f"Connection failed: {result.stderr}"
        
        user = result.stdout.strip()
        
        # tmux 확인
        tmux_result = safe_subprocess_run([
            "docker", "exec", CONTAINER_NAME, "which", "tmux"
        ])
        
        tmux_status = "Available" if tmux_result.returncode == 0 else "Not available"
        
        return f"Container: {CONTAINER_NAME} | User: {user} | Tmux: {tmux_status}"
        
    except Exception as e:
        return f"Connection test failed: {str(e)}"


@mcp.tool(description="Show streaming sessions status")
def streaming_status() -> Annotated[Dict[str, str], "Streaming sessions status"]:
    """현재 스트리밍 중인 세션들 상태"""
    status = {}
    for session_id, is_active in streaming_sessions.items():
        status[session_id] = "Active" if is_active else "Inactive"
    return status


if __name__ == "__main__":
    print("🚀 Starting MCP Terminal Server with Real-time Web Interface...")
    print("📱 Web Interface: http://localhost:5000")
    print("🔌 MCP Server: port 3006")
    print("📡 Polling interval: 500ms")
    print("💡 Tip: Create session first, then connect via web interface")
    mcp.run(transport="streamable-http")
