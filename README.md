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
- Claude Code handles everything: shell commands, file access, browser, calendar, email
- Per-channel conversation sessions
- SKILL.md-based skills system
- Heartbeat daemon for proactive scheduled tasks
- Multi-agent support with isolated sessions
- All data stored locally as Markdown files
