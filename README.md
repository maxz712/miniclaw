# MiniClaw

A lightweight [OpenClaw](https://github.com/openclaw/openclaw) alternative that uses local AI coding CLIs instead of the Anthropic API — bypassing the Anthropic ban on Claude powering third-party agentic tools like OpenClaw.

675 lines of Python. Same core features. Supports multiple AI backends.

## Supported backends

| Backend | CLI | What it can do |
|---------|-----|----------------|
| **Claude Code** | `claude` | Shell, files, browser, calendar, email, MCP |
| **Gemini CLI** | `gemini` | Shell, files, MCP, Google integrations |
| **Codex CLI** | `codex` | Shell, files, MCP, sandboxed execution |
| **Aider** | `aider` | Code editing, git integration, multi-model |

Set `"backend": "claude"` (or `"gemini"`, `"codex"`, `"aider"`) in config.json. Each agent can also override this with its own backend.

## Supported messaging platforms

| Platform | Library | Attachments |
|----------|---------|-------------|
| **Discord** | discord.py | Files, images |
| **Telegram** | python-telegram-bot | Documents, photos |
| **Slack** | slack-bolt (socket mode) | Files via URL |
| **WhatsApp** | pywa + FastAPI webhook | Images, documents |

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
!c hello                  # chat with the AI
!c reset                  # reset conversation
!c agent <name>           # switch agent
```

## Features

- **Multi-platform messaging** - Discord, Telegram, Slack, WhatsApp via channel adapter pattern
- **Multi-backend AI** - Claude Code, Gemini CLI, Codex CLI, Aider
- **Remote coding** - Users can ask the agent to write code, edit files, run commands, and build projects on the host machine
- **Per-channel sessions** - Conversations persist per channel or per user via CLI session management
- **Skills system** - Drop SKILL.md files into `workspace/skills/` to extend agent capabilities
- **Heartbeat daemon** - Proactive scheduled tasks via `workspace/HEARTBEAT.md`
- **Multi-agent** - Define multiple agents with different backends, models, system prompts, and permission levels
- **Local storage** - All data stored as Markdown files in `workspace/`
- **Access control** - User ID whitelists in config
- **File attachments** - Platform attachments downloaded and passed to the AI

## Permission modes

Control what the agent can do on your machine via `permission_mode` in config.json:

| Mode | Claude | Gemini | Codex |
|------|--------|--------|-------|
| `auto` | Auto-approve safe actions (default) | `auto_edit` | workspace-write |
| `acceptEdits` | Auto-approve file edits only | `auto_edit` | workspace-write |
| `bypassPermissions` | Approve everything | `yolo` | `--full-auto` |

## Multi-backend agents

Run different agents on different backends:

```json
{
  "agents": {
    "default": {
      "backend": "claude",
      "system_prompt": "You are a helpful assistant."
    },
    "coder": {
      "backend": "gemini",
      "system_prompt": "You are a code assistant.",
      "model": "gemini-2.5-pro"
    },
    "reviewer": {
      "backend": "aider",
      "model": "gpt-4o"
    }
  }
}
```

Switch in chat: `!c agent coder`

## Project structure

```
miniclaw/
├── bot.py              # Entry point, starts channels + heartbeat
├── channel.py          # Channel ABC, Message dataclass, shared routing
├── cli_runner.py       # Multi-backend CLI runner (claude/gemini/codex/aider)
├── skills.py           # SKILL.md loader
├── heartbeat.py        # Proactive daemon
├── channels/
│   ├── discord_ch.py   # Discord adapter
│   ├── telegram_ch.py  # Telegram adapter
│   ├── slack_ch.py     # Slack adapter
│   └── whatsapp_ch.py  # WhatsApp adapter
├── config.json         # All configuration
├── SETUP.md            # Interactive setup guide (for Claude Code)
├── CLAUDE.md           # Project context for Claude Code
└── workspace/
    ├── MEMORY.md       # Long-term memory (AI reads/writes)
    ├── HEARTBEAT.md    # Proactive task checklist
    ├── memory/         # Daily notes
    └── skills/         # SKILL.md files
```

## Extending

**Add a messaging platform:** Create `channels/<name>_ch.py` implementing `Channel`, add config block, register in `ADAPTERS` dict in `bot.py`. ~35-50 lines per adapter.

**Add an AI backend:** Add `_build_<name>_cmd()` and `_parse_<name>_output()` methods to `CLIRunner` in `cli_runner.py`, register in `BACKENDS` dict.
