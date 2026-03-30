<SKILLS>
## Skill System — Progressive Disclosure

Skills are markdown knowledge files (SKILL.md) containing detailed workflows, tool commands, and checklists for specific techniques.

### How It Works
1. **Auto-injected metadata**: On startup, you receive a list of available skill names + one-line descriptions. This tells you WHAT skills exist.
2. **On-demand full load**: The metadata is NOT enough to execute. You MUST `read_file` the full SKILL.md before using any technique it covers.

### How to Load Skills
Skills are on the host filesystem at `/skills/`, routed through a virtual backend.

```
read_file("/skills/<category>/<skill-name>/SKILL.md")
```

**IMPORTANT**: Skills are NOT accessible via bash. The sandbox does not mount `/skills/`.
- `bash(command="ls /skills/")` → will FAIL
- `bash(command="cat /skills/.../SKILL.md")` → will FAIL
- `read_file("/skills/.../SKILL.md")` → CORRECT

### When to Load
- **Before each new phase** (recon, exploit, post-exploit, C2 setup): read the relevant skill FIRST, then execute.
- **Before using a specific tool or technique**: if a skill covers it, read it first.
- Do NOT skip skill loading even if you think you know the technique — skills contain environment-specific instructions (paths, configs, container names) that differ from generic knowledge.

### Skill References
Some skills have a `references/` subdirectory with additional files (quickstart guides, cheat sheets). These are also accessible via `read_file`:
```
read_file("/skills/post-exploit/c2-sliver/references/sliver-cheatsheet.md")
```
</SKILLS>
