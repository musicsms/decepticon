<BASH_TOOL>
## bash() — Sandbox Execution

All commands execute inside the Docker sandbox via tmux sessions. You have NO access to the host system or Docker CLI.

### Parameters
| Parameter | Default | Description |
|-----------|---------|-------------|
| `command` | `""` | Shell command to execute. Empty = read current screen output |
| `is_input` | `False` | Set `True` ONLY when sending input to a waiting process |
| `session` | `"main"` | Tmux session name. Different names = parallel execution |
| `timeout` | `120` | Max seconds to wait. Use `300` for long compilation (e.g. Sliver `generate`) |

### Interactive Programs (sliver-client, msfconsole, evil-winrm, etc.)

Programs that need a TTY or continuous interaction MUST use a dedicated session.

Interactive programs show their own prompt (e.g., `msf6 >`, `sliver >`). The bash tool **auto-detects** this and returns the output immediately with `[session: <name> — interactive, send next command with is_input=True]`. This is NOT a timeout — the program is ready for your next command.

```
# Step 1: Start the interactive program in a named session
bash(command="sliver-client console", session="c2")
# → Returns the Sliver banner + "sliver >" prompt + [session: c2 — interactive]

# Step 2: Send commands to the running program with is_input=True
bash(command="https --lhost 0.0.0.0 --lport 443", is_input=True, session="c2")
bash(command="sessions", is_input=True, session="c2")

# Step 3: Read screen output without sending a command
bash(command="", session="c2")

# Signals
bash(command="C-c", is_input=True, session="c2")   # Ctrl+C — interrupt
bash(command="C-z", is_input=True, session="c2")   # Ctrl+Z — suspend
bash(command="C-d", is_input=True, session="c2")   # Ctrl+D — EOF
```

**Rules:**
- `is_input=False` (default) → starts a NEW command. Use this first.
- `is_input=True` → sends keystrokes to an ALREADY RUNNING process. Only use when a previous command is waiting for input.
- NEVER start with `is_input=True` — the session must have a running process first.
- Do NOT fall back to `nohup ... &` or resource files. Always use the interactive session pattern.
- Do NOT use `sleep` to wait for programs. Use `bash(command="", session="name")` to check state.

### Parallel Execution

Use different session names to run commands in parallel:

```
bash(command="nmap -sV target -oN recon/nmap.txt", session="nmap")
bash(command="curl -sI http://target | head -20", session="main")
```

Each session is independent — one session's timeout or block does not affect others.

### Session Lifecycle

| Output Prefix | Meaning | Action |
|---------------|---------|--------|
| `[IDLE]` | Session ready, no command running | Send new commands |
| `[RUNNING]` | Command still executing | Wait or do other work |
| `[TIMEOUT]` | Command exceeded time limit | Read the screen preview. For interactive programs, use `is_input=True` to continue. For long operations (compilation), retry with higher `timeout` |
| `[ERROR]` | Session crashed or was killed | Will auto-recover on next call |

### write_file — File Creation

**ALWAYS** use `write_file` to create files. NEVER use `bash(command="cat > file << EOF ...")`.

Why: `cat > file << EOF` echoes the entire content back as tool output, wasting context tokens. `write_file` creates files silently.
</BASH_TOOL>
