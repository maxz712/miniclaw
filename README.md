# MiniClaw

Minimal open-source AI assistant that bridges Discord, Telegram, Slack, and WhatsApp to your local [Claude Code](https://claude.com/claude-code) CLI. ~550 lines of Python.

## Setup

```bash
git clone git@github.com:maxz712/miniclaw.git && cd miniclaw
```

Then open Claude Code and say:

```
Read SETUP.md and help me set up miniclaw
```

Claude will install dependencies, walk you through getting platform tokens, configure everything, and test it.

## Usage

```
!c hello                  # chat with Claude
!c reset                  # reset conversation
!c agent <name>           # switch agent
```

## What it does

- Receives messages from Discord/Telegram/Slack/WhatsApp
- Pipes them to your local `claude` CLI (no API keys needed beyond Claude Code)
- **Users can ask the agent to write code, edit files, run commands, and build projects on the host machine** - Claude Code handles all of this natively
- Claude Code also handles: browser control, calendar, email via MCP
- Per-channel conversation sessions
- SKILL.md-based skills system
- Heartbeat daemon for proactive scheduled tasks
- Multi-agent support with isolated sessions
- All data stored locally as Markdown files

## Permission modes

Control what the agent can do on your machine via `permission_mode` in config.json:

| Mode | Behavior |
|------|----------|
| `auto` | Auto-approves safe actions, prompts for risky ones (default) |
| `acceptEdits` | Auto-approves file edits, prompts for shell commands |
| `bypassPermissions` | Approves everything - full autonomous coding (use with caution) |
