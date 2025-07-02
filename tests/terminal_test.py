import asyncio
import signal
import subprocess
import time
from typing import Dict, Callable

class TerminalProcessMonitor:
    def __init__(self):
        self.active_processes: Dict[str, dict] = {}
        self.completion_callbacks = {}
        
    async def execute_command_with_monitor(
        self, 
        session_id: str, 
        command: str, 
        callback: Callable = None
    ):
        """명령어 실행 + 종료 신호 모니터링"""
        
        # 1. 고유 프로세스 ID 생성
        process_id = f"{session_id}_{int(time.time())}"
        
        # 2. 명령어 실행 (백그라운드)
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", "attacker", "tmux", 
            "send-keys", "-t", session_id, command, "Enter",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # 3. 프로세스 정보 저장
        self.active_processes[process_id] = {
            'session_id': session_id,
            'command': command,
            'proc': proc,
            'start_time': time.time()
        }
        
        # 4. 완료 콜백 등록
        if callback:
            self.completion_callbacks[process_id] = callback
        
        # 5. 종료 대기 (비동기)
        asyncio.create_task(self._wait_for_completion(process_id))
        
        return process_id
    
    async def _wait_for_completion(self, process_id: str):
        """프로세스 완료까지 비동기 대기"""
        process_info = self.active_processes[process_id]
        session_id = process_info['session_id']
        
        # tmux 프로세스 상태 모니터링
        while True:
            try:
                # 현재 실행 중인 명령어 확인
                result = await asyncio.create_subprocess_exec(
                    "docker", "exec", "attacker", "tmux",
                    "list-panes", "-t", session_id, "-F", "#{pane_current_command}",
                    stdout=asyncio.subprocess.PIPE
                )
                stdout, _ = await result.communicate()
                current_cmd = stdout.decode().strip()
                
                # bash로 돌아왔으면 명령어 완료
                if current_cmd == "bash":
                    await self._on_process_completed(process_id)
                    break
                    
                await asyncio.sleep(0.5)  # 500ms마다 체크
                
            except Exception as e:
                print(f"Monitor error: {e}")
                break
    
    async def _on_process_completed(self, process_id: str):
        """프로세스 완료 이벤트 핸들러"""
        if process_id not in self.active_processes:
            return
        
        process_info = self.active_processes[process_id]
        session_id = process_info['session_id']
        command = process_info['command']
        
        print(f"🔔 Process completed: {command}")
        
        # 출력 캡쳐
        output = await self._capture_output(session_id)
        
        # 콜백 실행
        if process_id in self.completion_callbacks:
            callback = self.completion_callbacks[process_id]
            await callback(process_id, command, output)
        
        # 정리
        del self.active_processes[process_id]
        if process_id in self.completion_callbacks:
            del self.completion_callbacks[process_id]
    
    async def _capture_output(self, session_id: str) -> str:
        """터미널 출력 캡쳐"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "exec", "attacker", "tmux",
            "capture-pane", "-t", session_id, "-p",
            stdout=asyncio.subprocess.PIPE
        )
        stdout, _ = await proc.communicate()
        return stdout.decode()

# 사용 예시
async def main():
    monitor = TerminalProcessMonitor()
    
    # 완료 콜백 정의
    async def on_scan_complete(process_id, command, output):
        print(f"✅ Scan completed!")
        print(f"Command: {command}")
        print(f"Output length: {len(output)} chars")
        print("="*50)
        print(output)
        print("="*50)
    
    # 여러 명령어 병렬 실행
    await monitor.execute_command_with_monitor(
        "1", "echo 'Task 1 started' && sleep 10 && echo 'Task 1 completed'", on_scan_complete
    )

    await monitor.execute_command_with_monitor(
        "2", "echo 'Task 2 started' && sleep 5 && echo 'Task 2 completed'", on_scan_complete
    )
    
    # 메인 루프
    while monitor.active_processes:
        await asyncio.sleep(1)

# 실행
asyncio.run(main())