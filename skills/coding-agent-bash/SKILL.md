---
name: coding-agent-bash
description: |
  Orchestrate coding agents (Codex, Claude Code, OpenCode, Pi) via bash with optional
  background mode. Use when: delegating coding tasks to Codex, Claude Code, or other
  CLI coding agents; running background sessions; monitoring progress; parallelizing
  with git worktrees; or reviewing PRs with external coding agents.
---

# Coding Agent (bash-first)

Use **bash** (with optional background mode) for all coding agent work.

## PTY Mode: Codex/Pi/OpenCode yes, Claude Code no

For **Codex, Pi, and OpenCode**, PTY is still required (interactive terminal apps):

```bash
# Correct for Codex/Pi/OpenCode
bash pty:true command:"codex exec 'Your prompt'"
```

For **Claude Code** (`claude` CLI), use `--print --permission-mode bypassPermissions` instead.
`--dangerously-skip-permissions` with PTY can exit after the confirmation dialog.

```bash
# Correct for Claude Code (no PTY needed)
cd /path/to/project && claude --permission-mode bypassPermissions --print 'Your task'

# Wrong for Claude Code
bash pty:true command:"claude --dangerously-skip-permissions 'task'"
```

### Bash Tool Parameters

| Parameter    | Type    | Description |
| ------------ | ------- | ----------- |
| `command`    | string  | The shell command to run |
| `pty`        | boolean | Use for coding agents — allocates a pseudo-terminal for interactive CLIs |
| `workdir`    | string  | Working directory (agent sees only this folder's context) |
| `background` | boolean | Run in background, returns sessionId for monitoring |
| `timeout`    | number  | Timeout in seconds (kills process on expiry) |
| `elevated`   | boolean | Run on host instead of sandbox (if allowed) |

### Process Tool Actions (for background sessions)

| Action      | Description |
| ----------- | ----------- |
| `list`      | List all running/recent sessions |
| `poll`      | Check if session is still running |
| `log`       | Get session output (with optional offset/limit) |
| `write`     | Send raw data to stdin |
| `submit`    | Send data + newline (like typing and pressing Enter) |
| `send-keys` | Send key tokens or hex bytes |
| `paste`     | Paste text (with optional bracketed mode) |
| `kill`      | Terminate the session |

---

## Quick Start: One-Shot Tasks

```bash
# Quick chat (Codex needs a git repo!)
SCRATCH=$(mktemp -d) && cd $SCRATCH && git init && codex exec "Your prompt here"

# Or in a real project
bash pty:true workdir:~/Projects/myproject command:"codex exec 'Add error handling to the API calls'"
```

**Why git init?** Codex refuses to run outside a trusted git directory.

---

## The Pattern: workdir + background + pty

```bash
# Start agent in target directory
bash pty:true workdir:~/project background:true command:"codex exec --full-auto 'Build a snake game'"
# Returns sessionId for tracking

# Monitor progress
process action:log sessionId:XXX

# Check if done
process action:poll sessionId:XXX

# Send input (if agent asks a question)
process action:write sessionId:XXX data:"y"

# Submit with Enter
process action:submit sessionId:XXX data:"yes"

# Kill if needed
process action:kill sessionId:XXX
```

**Why workdir matters:** Agent wakes up in a focused directory, doesn't wander off reading unrelated files.

---

## Codex CLI

**Model:** `gpt-5.2-codex` is the default (set in `~/.codex/config.toml`)

### Flags

| Flag            | Effect |
| --------------- | ------ |
| `exec "prompt"` | One-shot execution, exits when done |
| `--full-auto`   | Sandboxed but auto-approves in workspace |
| `--yolo`        | No sandbox, no approvals (fastest, most dangerous) |

### Building/Creating

```bash
# Quick one-shot (auto-approves)
bash pty:true workdir:~/project command:"codex exec --full-auto 'Build a dark mode toggle'"

# Background for longer work
bash pty:true workdir:~/project background:true command:"codex --yolo 'Refactor the auth module'"
```

### Reviewing PRs

**CRITICAL: Never review PRs in OpenClaw's own project folder!**
Clone to temp folder or use git worktree.

```bash
# Clone to temp for safe review
REVIEW_DIR=$(mktemp -d)
git clone https://github.com/user/repo.git $REVIEW_DIR
cd $REVIEW_DIR && gh pr checkout 130
bash pty:true workdir:$REVIEW_DIR command:"codex review --base origin/main"

# Or use git worktree (keeps main intact)
git worktree add /tmp/pr-130-review pr-130-branch
bash pty:true workdir:/tmp/pr-130-review command:"codex review --base main"
```

### Batch PR Reviews (parallel)

```bash
# Fetch all PR refs first
git fetch origin '+refs/pull/*/head:refs/remotes/origin/pr/*'

# Deploy one Codex per PR
bash pty:true workdir:~/project background:true command:"codex exec 'Review PR #86. git diff origin/main...origin/pr/86'"
bash pty:true workdir:~/project background:true command:"codex exec 'Review PR #87. git diff origin/main...origin/pr/87'"

# Monitor all
process action:list

# Post results to GitHub
gh pr comment <PR#> --body "<review content>"
```

---

## Claude Code

```bash
# Foreground
bash workdir:~/project command:"claude --permission-mode bypassPermissions --print 'Your task'"

# Background
bash workdir:~/project background:true command:"claude --permission-mode bypassPermissions --print 'Your task'"
```

---

## OpenCode

```bash
bash pty:true workdir:~/project command:"opencode run 'Your task'"
```

---

## Pi Coding Agent

```bash
# Install: npm install -g @mariozechner/pi-coding-agent
bash pty:true workdir:~/project command:"pi 'Your task'"

# Non-interactive mode
bash pty:true command:"pi -p 'Summarize src/'"

# Different provider/model
bash pty:true command:"pi --provider openai --model gpt-4o-mini -p 'Your task'"
```

---

## Parallel Issue Fixing with git worktrees

```bash
# 1. Create worktrees for each issue
git worktree add -b fix/issue-78 /tmp/issue-78 main
git worktree add -b fix/issue-99 /tmp/issue-99 main

# 2. Launch Codex in each (background + PTY)
bash pty:true workdir:/tmp/issue-78 background:true command:"pnpm install && codex --yolo 'Fix issue #78. Commit and push.'"
bash pty:true workdir:/tmp/issue-99 background:true command:"pnpm install && codex --yolo 'Fix issue #99. Commit and push.'"

# 3. Monitor progress
process action:list
process action:log sessionId:XXX

# 4. Create PRs after fixes
cd /tmp/issue-78 && git push -u origin fix/issue-78
gh pr create --repo user/repo --head fix/issue-78 --title "fix: ..." --body "..."

# 5. Cleanup
git worktree remove /tmp/issue-78
git worktree remove /tmp/issue-99
```

---

## Rules

1. **Use the right execution mode per agent:**
   - Codex/Pi/OpenCode: `pty:true`
   - Claude Code: `--print --permission-mode bypassPermissions` (no PTY)
2. **Respect tool choice** — if user asks for Codex, use Codex. Do NOT hand-code patches yourself.
3. **Be patient** — don't kill sessions because they're "slow"
4. **Monitor with process:log** — check progress without interfering
5. **--full-auto for building** — auto-approves changes
6. **Parallel is OK** — run many Codex processes at once for batch work
7. **NEVER start Codex inside your OpenClaw state directory** (`$OPENCLAW_STATE_DIR`, default `~/.openclaw`)
8. **NEVER checkout branches in `~/Projects/openclaw/`** — that's the LIVE OpenClaw instance

---

## Progress Updates (Critical)

When you spawn coding agents in the background, keep the user in the loop:

- Send 1 short message when you start (what's running + where).
- Then only update when something changes: milestone completes, agent asks a question, error occurs, or agent finishes.
- If you kill a session, immediately say you killed it and why.

---

## Auto-Notify on Completion

Append a wake trigger to your prompt so OpenClaw gets notified immediately:

```bash
bash pty:true workdir:~/project background:true command:"codex --yolo exec 'Build a REST API for todos.

When completely finished, run: openclaw system event --text \"Done: Built todos REST API with CRUD endpoints\" --mode now'"
```

---

## Key Learnings

- **PTY is essential:** Coding agents are interactive terminal apps. Without `pty:true`, output breaks or agent hangs.
- **Git repo required:** Codex won't run outside a git directory. Use `mktemp -d && git init` for scratch work.
- **exec is your friend:** `codex exec "prompt"` runs and exits cleanly — perfect for one-shots.
- **submit vs write:** Use `submit` to send input + Enter, `write` for raw data without newline.
