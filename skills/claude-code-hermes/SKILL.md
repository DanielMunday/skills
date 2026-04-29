---
name: claude-code-hermes
description: |
  Delegate coding tasks to Claude Code (Anthropic's autonomous coding agent CLI) via
  the Hermes terminal. Use when: orchestrating Claude Code in print mode or interactive
  PTY mode, automating coding tasks, managing sessions, configuring hooks, MCP servers,
  subagents, or debugging tmux-based multi-turn workflows.
---

# Claude Code — Hermes Orchestration Guide

Delegate coding tasks to Claude Code (Anthropic's autonomous coding agent CLI) via the Hermes terminal. Claude Code v2.x can read files, write code, run shell commands, spawn subagents, and manage git workflows autonomously.

## Prerequisites

- **Install:** `npm install -g @anthropic-ai/claude-code`
- **Auth:** run `claude` once to log in (browser OAuth for Pro/Max, or set `ANTHROPIC_API_KEY`)
- **Console auth:** `claude auth login --console` for API key billing
- **SSO auth:** `claude auth login --sso` for Enterprise
- **Check status:** `claude auth status` (JSON) or `claude auth status --text` (human-readable)
- **Health check:** `claude doctor` — checks auto-updater and installation health
- **Version check:** `claude --version` (requires v2.x+)
- **Update:** `claude update` or `claude upgrade`

## Two Orchestration Modes

### Mode 1: Print Mode (`-p`) — Non-Interactive (PREFERRED for most tasks)

Print mode runs a one-shot task, returns the result, and exits. No PTY needed. No interactive prompts.

```
terminal(command="claude -p 'Add error handling to all API calls in src/' --allowedTools 'Read,Edit' --max-turns 10", workdir="/path/to/project", timeout=120)
```

**When to use print mode:**
- One-shot coding tasks (fix a bug, add a feature, refactor)
- CI/CD automation and scripting
- Structured data extraction with `--json-schema`
- Piped input processing (`cat file | claude -p "analyze this"`)
- Any task where you don't need multi-turn conversation

**Print mode skips ALL interactive dialogs** — no workspace trust prompt, no permission confirmations.

### Mode 2: Interactive PTY via tmux — Multi-Turn Sessions

```bash
# Start a tmux session
terminal(command="tmux new-session -d -s claude-work -x 140 -y 40")

# Launch Claude Code inside it
terminal(command="tmux send-keys -t claude-work 'cd /path/to/project && claude' Enter")

# Wait for startup (~3-5 seconds), then send task
terminal(command="sleep 5 && tmux send-keys -t claude-work 'Refactor the auth module to use JWT tokens' Enter")

# Monitor progress
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -50")

# Send follow-up
terminal(command="tmux send-keys -t claude-work 'Now add unit tests for the new JWT code' Enter")

# Exit when done
terminal(command="tmux send-keys -t claude-work '/exit' Enter")
```

**When to use interactive mode:**
- Multi-turn iterative work (refactor → review → fix → test cycle)
- Tasks requiring human-in-the-loop decisions
- When you need slash commands (`/compact`, `/review`, `/model`)

## PTY Dialog Handling (CRITICAL for Interactive Mode)

Claude Code presents up to two confirmation dialogs on first launch.

### Dialog 1: Workspace Trust (first visit to a directory)
```
❯ 1. Yes, I trust this folder    ← DEFAULT (just press Enter)
  2. No, exit
```
**Handling:** `tmux send-keys -t <session> Enter`

### Dialog 2: Bypass Permissions Warning (only with --dangerously-skip-permissions)
```
❯ 1. No, exit                    ← DEFAULT (WRONG choice!)
  2. Yes, I accept
```
**Handling:** Must navigate DOWN first, then Enter:
```bash
tmux send-keys -t <session> Down && sleep 0.3 && tmux send-keys -t <session> Enter
```

### Robust Dialog Handling Pattern
```bash
terminal(command="tmux send-keys -t claude-work 'claude --dangerously-skip-permissions \"your task\"' Enter")
terminal(command="sleep 4 && tmux send-keys -t claude-work Enter")           # Trust dialog
terminal(command="sleep 3 && tmux send-keys -t claude-work Down && sleep 0.3 && tmux send-keys -t claude-work Enter")  # Permissions dialog
terminal(command="sleep 15 && tmux capture-pane -t claude-work -p -S -60")
```

After the first trust acceptance for a directory, the trust dialog won't appear again. Only the permissions dialog recurs with `--dangerously-skip-permissions`.

## CLI Subcommands

| Subcommand | Purpose |
|------------|---------|
| `claude` | Start interactive REPL |
| `claude "query"` | Start REPL with initial prompt |
| `claude -p "query"` | Print mode (non-interactive) |
| `cat file \| claude -p "query"` | Pipe content as stdin context |
| `claude -c` | Continue most recent conversation in this directory |
| `claude -r "id"` | Resume a specific session by ID or name |
| `claude auth login` | Sign in (`--console` for API billing, `--sso` for Enterprise) |
| `claude auth status` | Check login status (`--text` for human-readable) |
| `claude mcp add <name> -- <cmd>` | Add an MCP server |
| `claude mcp list` | List configured MCP servers |
| `claude mcp remove <name>` | Remove an MCP server |
| `claude agents` | List configured agents |
| `claude doctor` | Run health checks |
| `claude update` / `claude upgrade` | Update to latest version |
| `claude remote-control` | Start server to control Claude from claude.ai or mobile app |
| `claude install [target]` | Install native build |
| `claude setup-token` | Set up long-lived auth token |
| `claude plugin` / `claude plugins` | Manage Claude Code plugins |
| `claude auto-mode` | Inspect auto mode classifier configuration |

## Print Mode Deep Dive

### Structured JSON Output
```bash
terminal(command="claude -p 'Analyze auth.py for security issues' --output-format json --max-turns 5", workdir="/project", timeout=120)
```

Returns:
```json
{
  "type": "result",
  "subtype": "success",
  "result": "The analysis text...",
  "session_id": "75e2167f-...",
  "num_turns": 3,
  "total_cost_usd": 0.0787,
  "duration_ms": 10276,
  "stop_reason": "end_turn",
  "terminal_reason": "completed"
}
```

Key fields: `session_id` for resumption, `num_turns`, `total_cost_usd`, `subtype` (`success`, `error_max_turns`, `error_budget`).

### Streaming JSON Output
```bash
claude -p "Write a summary" --output-format stream-json --verbose --include-partial-messages | \
  jq -rj 'select(.type == "stream_event" and .event.delta.type? == "text_delta") | .event.delta.text'
```

Stream events include `system/api_retry` with `attempt`, `max_retries`, and `error` fields.

### Bidirectional Streaming
```bash
claude -p "task" --input-format stream-json --output-format stream-json --replay-user-messages
```

### Piped Input
```bash
cat src/auth.py | claude -p 'Review this code for bugs' --max-turns 1
git diff HEAD~3 | claude -p 'Summarize these changes' --max-turns 1
```

### JSON Schema for Structured Extraction
```bash
terminal(command="claude -p 'List all functions in src/' --output-format json --json-schema '{\"type\":\"object\",\"properties\":{\"functions\":{\"type\":\"array\",\"items\":{\"type\":\"string\"}}},\"required\":[\"functions\"]}' --max-turns 5", workdir="/project", timeout=90)
```

Parse `structured_output` from the JSON result.

### Session Continuation
```bash
# Start a task, save session ID
terminal(command="claude -p 'Start refactoring the database layer' --output-format json --max-turns 10 > /tmp/session.json", workdir="/project", timeout=180)

# Resume with session ID
terminal(command="claude -p 'Continue and add connection pooling' --resume $(cat /tmp/session.json | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"session_id\"])') --max-turns 5", workdir="/project", timeout=120)

# Resume most recent session
terminal(command="claude -p 'What did you do last time?' --continue --max-turns 1", workdir="/project", timeout=30)

# Fork a session (new ID, keeps history)
terminal(command="claude -p 'Try a different approach' --resume <id> --fork-session --max-turns 10", workdir="/project", timeout=120)
```

### Bare Mode for CI/Scripting
```bash
terminal(command="claude --bare -p 'Run all tests and report failures' --allowedTools 'Read,Bash' --max-turns 10", workdir="/project", timeout=180)
```

`--bare` skips hooks, plugins, MCP discovery, and CLAUDE.md loading. Requires `ANTHROPIC_API_KEY`.

| To load in bare mode | Flag |
|------|------|
| System prompt additions | `--append-system-prompt "text"` or `--append-system-prompt-file path` |
| Settings | `--settings <file-or-json>` |
| MCP servers | `--mcp-config <file-or-json>` |
| Custom agents | `--agents '<json>'` |

### Fallback Model for Overload
```bash
terminal(command="claude -p 'task' --fallback-model haiku --max-turns 5", timeout=90)
```

## Complete CLI Flags Reference

### Session & Environment
| Flag | Effect |
|------|--------|
| `-p, --print` | Non-interactive one-shot mode |
| `-c, --continue` | Resume most recent conversation in current directory |
| `-r, --resume <id>` | Resume specific session by ID or name |
| `--fork-session` | When resuming, create new session ID |
| `--session-id <uuid>` | Use a specific UUID for the conversation |
| `--no-session-persistence` | Don't save session to disk (print mode only) |
| `--add-dir <paths...>` | Grant access to additional working directories |
| `-w, --worktree [name]` | Run in isolated git worktree at `.claude/worktrees/<name>` |
| `--tmux` | Create a tmux session for the worktree (requires `--worktree`) |
| `--ide` | Auto-connect to a valid IDE on startup |
| `--chrome` / `--no-chrome` | Enable/disable Chrome browser integration |
| `--from-pr [number]` | Resume session linked to a specific GitHub PR |

### Model & Performance
| Flag | Effect |
|------|--------|
| `--model <alias>` | `sonnet`, `opus`, `haiku`, or full model name |
| `--effort <level>` | `low`, `medium`, `high`, `max`, `auto` |
| `--max-turns <n>` | Limit agentic loops (print mode only) |
| `--max-budget-usd <n>` | Cap API spend in dollars (print mode only) |
| `--fallback-model <model>` | Auto-fallback on overload (print mode only) |
| `--betas <betas...>` | Beta headers (API key users only) |

### Permission & Safety
| Flag | Effect |
|------|--------|
| `--dangerously-skip-permissions` | Auto-approve ALL tool use |
| `--permission-mode <mode>` | `default`, `acceptEdits`, `plan`, `auto`, `dontAsk`, `bypassPermissions` |
| `--allowedTools <tools...>` | Whitelist specific tools |
| `--disallowedTools <tools...>` | Blacklist specific tools |
| `--tools <tools...>` | Override built-in tool set |

### Output & Input Format
| Flag | Effect |
|------|--------|
| `--output-format <fmt>` | `text`, `json`, `stream-json` |
| `--input-format <fmt>` | `text` or `stream-json` |
| `--json-schema <schema>` | Force structured JSON output |
| `--verbose` | Full turn-by-turn output |
| `--include-partial-messages` | Include partial message chunks |
| `--replay-user-messages` | Re-emit user messages on stdout |

### System Prompt & Context
| Flag | Effect |
|------|--------|
| `--append-system-prompt <text>` | **Add** to the default system prompt |
| `--append-system-prompt-file <path>` | **Add** file contents to system prompt |
| `--system-prompt <text>` | **Replace** entire system prompt |
| `--bare` | Skip hooks, plugins, MCP discovery, CLAUDE.md |
| `--agents '<json>'` | Define custom subagents dynamically |
| `--mcp-config <path>` | Load MCP servers from JSON file |
| `--strict-mcp-config` | Only use MCP servers from `--mcp-config` |
| `--settings <file-or-json>` | Load additional settings |
| `--plugin-dir <paths...>` | Load plugins from directories for this session |
| `--disable-slash-commands` | Disable all skills/slash commands |

### Debugging
| Flag | Effect |
|------|--------|
| `-d, --debug [filter]` | Enable debug logging (e.g., `"api,hooks"`, `"!1p,!file"`) |
| `--debug-file <path>` | Write debug logs to file |

### Tool Name Syntax for --allowedTools / --disallowedTools
```
Read                    # All file reading
Edit                    # File editing
Write                   # File creation
Bash                    # All shell commands
Bash(git *)             # Only git commands
Bash(git commit *)      # Only git commit commands
Bash(npm run lint:*)    # Pattern matching
WebSearch               # Web search
mcp__<server>__<tool>   # Specific MCP tool
```

## Settings & Configuration

### Settings Hierarchy (highest to lowest priority)
1. **CLI flags**
2. **Local project:** `.claude/settings.local.json` (personal, gitignored)
3. **Project:** `.claude/settings.json` (shared, git-tracked)
4. **User:** `~/.claude/settings.json` (global)

### Permissions in Settings
```json
{
  "permissions": {
    "allow": ["Bash(npm run lint:*)", "WebSearch", "Read"],
    "ask": ["Write(*.ts)", "Bash(git push*)"],
    "deny": ["Read(.env)", "Bash(rm -rf *)"]
  }
}
```

### CLAUDE.md Memory Files Hierarchy
1. **Global:** `~/.claude/CLAUDE.md`
2. **Project:** `./CLAUDE.md`
3. **Local:** `.claude/CLAUDE.local.md` (gitignored)

Use `#` prefix in interactive mode to quickly add to memory: `# Always use 2-space indentation`.

### Rules Directory (Modular CLAUDE.md)
- **Project rules:** `.claude/rules/*.md` — team-shared, git-tracked
- **User rules:** `~/.claude/rules/*.md` — personal, global

## Interactive Session: Slash Commands

### Session & Context
| Command | Purpose |
|---------|---------|
| `/help` | Show all commands |
| `/compact [focus]` | Compress context to save tokens |
| `/clear` | Wipe conversation history |
| `/context` | Visualize context usage with optimization tips |
| `/cost` | View token usage with per-model breakdowns |
| `/resume` | Switch to or resume a different session |
| `/rewind` | Revert to a previous checkpoint |
| `/btw <question>` | Ask a side question without adding to context cost |
| `/status` | Show version, connectivity, and session info |
| `/todos` | List tracked action items |
| `/exit` or `Ctrl+D` | End session |

### Development & Review
| Command | Purpose |
|---------|---------|
| `/review` | Request code review of current changes |
| `/security-review` | Perform security analysis |
| `/plan [description]` | Enter Plan mode for task planning |
| `/loop [interval]` | Schedule recurring tasks |
| `/batch` | Auto-create worktrees for large parallel changes |

### Configuration & Tools
| Command | Purpose |
|---------|---------|
| `/model [model]` | Switch models mid-session |
| `/effort [level]` | Set reasoning effort: `low`, `medium`, `high`, `max`, `auto` |
| `/init` | Create a CLAUDE.md file |
| `/memory` | Open CLAUDE.md for editing |
| `/config` | Open interactive settings configuration |
| `/permissions` | View/update tool permissions |
| `/agents` | Manage specialized subagents |
| `/mcp` | Interactive UI to manage MCP servers |
| `/add-dir` | Add additional working directories |
| `/usage` | Show plan limits and rate limit status |
| `/voice` | Enable push-to-talk voice mode |

### Custom Slash Commands
```markdown
# .claude/commands/deploy.md
Run the deploy pipeline:
1. Run all tests
2. Build the Docker image
3. Push to registry
4. Update the $ARGUMENTS environment (default: staging)
```

Usage: `/deploy production` — `$ARGUMENTS` is replaced with user input.

## Interactive Session: Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Cancel current input or generation |
| `Ctrl+D` | Exit session |
| `Ctrl+R` | Reverse search command history |
| `Ctrl+B` | Background a running task |
| `Ctrl+V` | Paste image into conversation |
| `Ctrl+O` | Transcript mode — see Claude's thinking process |
| `Ctrl+G` or `Ctrl+X Ctrl+E` | Open prompt in external editor |
| `Esc Esc` | Rewind conversation or code state |
| `Shift+Tab` | Cycle permission modes (Normal → Auto-Accept → Plan) |
| `Alt+P` | Switch model |
| `Alt+T` | Toggle thinking mode |
| `Alt+O` | Toggle Fast Mode |

### Input Prefixes
| Prefix | Action |
|--------|--------|
| `!` | Execute bash directly, bypassing AI |
| `@` | Reference files/directories with autocomplete |
| `#` | Quick add to CLAUDE.md memory |
| `/` | Slash commands |

### Pro Tip: "ultrathink"
Use the keyword **"ultrathink"** in your prompt for maximum reasoning effort on a specific turn.

## PR Review Patterns

### Quick Review (Print Mode)
```bash
terminal(command="cd /path/to/repo && git diff main...feature-branch | claude -p 'Review this diff for bugs, security issues, and style problems.' --max-turns 1", timeout=60)
```

### Deep Review (Interactive + Worktree)
```bash
terminal(command="tmux new-session -d -s review -x 140 -y 40")
terminal(command="tmux send-keys -t review 'cd /path/to/repo && claude -w pr-review' Enter")
terminal(command="sleep 5 && tmux send-keys -t review Enter")
terminal(command="sleep 2 && tmux send-keys -t review 'Review all changes vs main. Check for bugs, security issues, race conditions, and missing tests.' Enter")
terminal(command="sleep 30 && tmux capture-pane -t review -p -S -60")
```

### PR Review from Number
```bash
terminal(command="claude -p 'Review this PR thoroughly' --from-pr 42 --max-turns 10", workdir="/path/to/repo", timeout=120)
```

## Parallel Claude Instances

```bash
# Task 1: Fix backend
terminal(command="tmux new-session -d -s task1 && tmux send-keys -t task1 'cd ~/project && claude -p \"Fix the auth bug\" --allowedTools \"Read,Edit\" --max-turns 10' Enter")

# Task 2: Write tests
terminal(command="tmux new-session -d -s task2 && tmux send-keys -t task2 'cd ~/project && claude -p \"Write integration tests\" --allowedTools \"Read,Write,Bash\" --max-turns 15' Enter")

# Monitor all
terminal(command="sleep 30 && for s in task1 task2; do echo '=== '$s' ==='; tmux capture-pane -t $s -p -S -5 2>/dev/null; done")
```

## CLAUDE.md — Project Context File

```markdown
# Project: My API

## Architecture
- FastAPI backend with SQLAlchemy ORM
- PostgreSQL database, Redis cache

## Key Commands
- `make test` — run full test suite
- `make lint` — ruff + mypy
- `make dev` — start dev server on :8000

## Code Standards
- Type hints on all public functions
- 2-space indentation for YAML, 4-space for Python
```

**Be specific.** Instead of "Write good code", use "Use 2-space indentation for JS."

Auto-memory stored at `~/.claude/projects/<project>/memory/` (25KB or 200 lines per project).

## Custom Subagents

```markdown
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: Security-focused code review
model: opus
tools: [Read, Bash]
---
You are a senior security engineer. Review code for injection vulnerabilities,
auth flaws, secrets in code, and unsafe deserialization.
```

Invoke via: `@security-reviewer review the auth module`

### Dynamic Agents via CLI
```bash
terminal(command="claude --agents '{\"reviewer\": {\"description\": \"Reviews code\", \"prompt\": \"You are a code reviewer focused on performance\"}}' -p 'Use @reviewer to check auth.py'", timeout=120)
```

## Hooks — Automation on Events

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "Write(*.py)",
      "hooks": [{"type": "command", "command": "ruff check --fix $CLAUDE_FILE_PATHS"}]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{"type": "command", "command": "if echo \"$CLAUDE_TOOL_INPUT\" | grep -q 'rm -rf'; then echo 'Blocked!' && exit 2; fi"}]
    }]
  }
}
```

### All 8 Hook Types
| Hook | When it fires |
|------|--------------|
| `UserPromptSubmit` | Before Claude processes a user prompt |
| `PreToolUse` | Before tool execution (exit 2 = block) |
| `PostToolUse` | After a tool finishes |
| `Notification` | On permission requests or input waits |
| `Stop` | When Claude finishes a response |
| `SubagentStop` | When a subagent completes |
| `PreCompact` | Before context memory is cleared |
| `SessionStart` | When a session begins |

### Hook Environment Variables
| Variable | Content |
|----------|---------|
| `CLAUDE_PROJECT_DIR` | Current project path |
| `CLAUDE_FILE_PATHS` | Files being modified |
| `CLAUDE_TOOL_INPUT` | Tool parameters as JSON |

## MCP Integration

```bash
# GitHub integration
claude mcp add -s user github -- npx @modelcontextprotocol/server-github

# PostgreSQL queries
claude mcp add -s local postgres -- npx @anthropic-ai/server-postgres --connection-string postgresql://localhost/mydb

# Puppeteer for web testing
claude mcp add puppeteer -- npx @anthropic-ai/server-puppeteer
```

### MCP Scopes
| Flag | Scope | Storage |
|------|-------|---------|
| `-s user` | Global (all projects) | `~/.claude.json` |
| `-s local` | This project (personal) | `.claude/settings.local.json` (gitignored) |
| `-s project` | This project (team-shared) | `.claude/settings.json` (git-tracked) |

### MCP Limits & Tuning
- Tool descriptions: 2KB cap per server
- Result size: use `maxResultSizeChars` annotation for up to 500K chars
- Output tokens: `export MAX_MCP_OUTPUT_TOKENS=50000`

## Monitoring Interactive Sessions

```bash
# Periodic capture to check status
terminal(command="tmux capture-pane -t dev -p -S -10")
```

TUI indicators:
- `❯` at bottom = waiting for input (Claude is done)
- `●` lines = Claude is actively using tools
- `⏵⏵ bypass permissions on` = permissions bypass active
- `◐ medium · /effort` = current effort level

### Context Window Health
- **< 70%** — Normal operation
- **70-85%** — Use `/compact`
- **> 85%** — Hallucination risk; use `/compact` or `/clear`

## Environment Variables

| Variable | Effect |
|----------|--------|
| `ANTHROPIC_API_KEY` | API key for authentication |
| `CLAUDE_CODE_EFFORT_LEVEL` | Default effort level |
| `MAX_THINKING_TOKENS` | Cap thinking tokens (`0` to disable) |
| `MAX_MCP_OUTPUT_TOKENS` | Cap output from MCP servers |
| `CLAUDE_CODE_NO_FLICKER=1` | Eliminate terminal flicker |
| `CLAUDE_CODE_SUBPROCESS_ENV_SCRUB` | Strip credentials from sub-processes |

## Cost & Performance Tips

1. Use `--max-turns` in print mode (start with 5-10 for most tasks)
2. Use `--max-budget-usd` for cost caps (minimum ~$0.05)
3. Use `--effort low` for simple tasks; `high`/`max` for complex reasoning
4. Use `--bare` for CI/scripting to skip plugin/hook discovery overhead
5. Use `--allowedTools` to restrict to only what's needed
6. Use `/compact` in interactive sessions when context gets large
7. Use `--model haiku` for simple tasks; `--model opus` for complex work
8. Use `--fallback-model haiku` in print mode for overload resilience
9. Start new sessions for distinct tasks — fresh context is more efficient
10. Use `--no-session-persistence` in CI to avoid accumulating saved sessions

## Pitfalls & Gotchas

1. **Interactive mode REQUIRES tmux** — Claude Code is a full TUI app
2. **`--dangerously-skip-permissions` dialog defaults to "No, exit"** — send Down then Enter; print mode skips this entirely
3. **`--max-budget-usd` minimum is ~$0.05** — system prompt cache creation alone costs this
4. **`--max-turns` is print-mode only** — ignored in interactive sessions
5. **Session resumption requires same directory** — `--continue` finds most recent session for current directory
6. **`--json-schema` needs enough `--max-turns`** — Claude must read files before producing structured output
7. **Trust dialog only appears once per directory**
8. **Background tmux sessions persist** — clean up with `tmux kill-session -t <name>`
9. **Slash commands only work in interactive mode** — in `-p` mode, use natural language
10. **`--bare` requires `ANTHROPIC_API_KEY`** — skips OAuth
11. **Context degradation above 70%** — monitor with `/context`, proactively `/compact`

## Rules for Hermes Agents

1. Prefer print mode (`-p`) for single tasks — cleaner, structured output
2. Use tmux for multi-turn interactive work
3. Always set `workdir` — keep Claude focused on the right project
4. Set `--max-turns` in print mode — prevents runaway costs
5. Monitor tmux sessions with `tmux capture-pane -t <session> -p -S -50`
6. Look for `❯` prompt — indicates Claude is waiting for input
7. Clean up tmux sessions when done
8. Report results to user — summarize what Claude did and what changed
9. Don't kill slow sessions — check progress first
10. Use `--allowedTools` — restrict capabilities to what the task needs
