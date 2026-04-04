# CLI Reference

## CLI Commands

| Command | Description |
|---------|-------------|
| `decepticon` | Start all services and open the interactive CLI |
| `decepticon demo` | Run guided demo against Metasploitable 2 (full kill chain + Sliver C2) |
| `decepticon stop` | Stop all services |
| `decepticon update [-f]` | Pull latest images and sync configuration (`--force` to re-pull same version) |
| `decepticon status` | Show service status |
| `decepticon logs [service]` | Follow service logs (default: langgraph) |
| `decepticon config` | Edit API keys and settings |
| `decepticon victims` | Start vulnerable test targets (DVWA, Metasploitable) |
| `decepticon remove` | Uninstall Decepticon completely |
| `decepticon --version` | Show installed version |

## Interactive CLI

Once inside the CLI, you have two **screen modes** and a set of slash commands.

**Prompt mode** (default) shows a compact view — sub-agent sessions are collapsed, consecutive tool calls are grouped, and only the latest bash output is expanded. **Transcript mode** (`ctrl+o`) expands everything: full event history, sub-agent details, and complete tool outputs.

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `ctrl+o` | Toggle between prompt and transcript mode |
| `ctrl+c` | Cancel running stream / exit transcript / exit app |
| `Esc` | Exit transcript mode |

### Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands and shortcuts |
| `/clear` | Clear conversation history |
| `/quit` | Exit Decepticon CLI |
