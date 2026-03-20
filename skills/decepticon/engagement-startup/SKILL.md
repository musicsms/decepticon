---
name: engagement-startup
description: "Mandatory first-turn startup procedure. Checks for existing engagements, asks operator to resume or start new, and initializes workspace. Triggers on: agent startup, first message, session start. MUST be read before any other action."
metadata:
  subdomain: orchestration
  tags: startup, engagement-selection, workspace-init, resume
  mitre_attack:
---

# Engagement Startup Procedure

**Execute this procedure on every session start, before any other action.**

## Step 1: Discover Existing Engagements

```
bash(command="ls -1 /workspace/ 2>/dev/null || echo '[empty]'")
```

## Step 2: Present Options to Operator

### If engagements exist

Present a numbered list and ask:

```
Existing engagements found:
  1. acme-external-2026
  2. internal-audit-q1

Options:
  [number] Resume an engagement
  [new]    Start a new engagement

Which would you like?
```

### If no engagements exist

```
No existing engagements found. Let's set up a new one.
What is the target or scope for this engagement?
```

## Step 3A: Resume Existing Engagement

1. Read planning documents:
   ```
   read_file("<engagement>/plan/opplan.json")
   read_file("<engagement>/plan/roe.json")
   read_file("<engagement>/findings.md")
   ```
2. Summarize progress to the operator:
   - Objectives completed / total
   - Current phase (recon / exploit / post-exploit)
   - Last completed objective and key findings
   - Next pending objective
3. Ask: "Continue from where we left off?"
4. Begin the Ralph execution loop

## Step 3B: Start New Engagement

1. Ask the operator for target/scope (if not already provided)
2. Determine a descriptive slug from the target scope:
   - Format: `<org>-<type>-<period>` (e.g., `acme-external-2026`, `internal-audit-q1`)
   - Keep it short, lowercase, hyphenated
3. Create workspace structure:
   ```
   bash(command="mkdir -p /workspace/<slug>/{plan,recon,exploit,post-exploit}")
   ```
4. Delegate to `planner` sub-agent to generate engagement documents:
   ```
   task("planner", "New engagement. Workspace: /workspace/<slug>/. Target: <target>. Interview the operator and generate RoE, CONOPS, and OPPLAN.")
   ```
5. Once planner completes → verify documents exist in `<slug>/plan/`
6. Begin the Ralph execution loop
