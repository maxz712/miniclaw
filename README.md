# MiniClaw

A lightweight [OpenClaw](https://github.com/openclaw/openclaw) alternative that uses local AI coding CLIs instead of the Anthropic API — bypassing the Anthropic ban on Claude powering third-party agentic tools like OpenClaw.

~600 lines of Python. Same core features. Supports multiple AI backends.

## Supported backends

| Backend | CLI | What it can do |
|---------|-----|----------------|
| **Claude Code** | `claude` | Shell, files, browser, calendar, email, MCP |
| **Gemini CLI** | `gemini` | Shell, files, MCP, Google integrations |
| **Codex CLI** | `codex` | Shell, files, MCP, sandboxed execution |
| **Aider** | `aider` | Code editing, git integration, multi-model |

Set `"backend": "claude"` (or `"gemini"`, `"codex"`, `"aider"`) in config.json. Each agent can also use a different backend.

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

## What it does

- Receives messages from Discord/Telegram/Slack/WhatsApp
- Pipes them to your local AI CLI (Claude Code, Gemini, Codex, or Aider)
- **Users can ask the agent to write code, edit files, run commands, and build projects on the host machine**
- Per-channel conversation sessions
- SKILL.md-based skills system
- Heartbeat daemon for proactive scheduled tasks
- Multi-agent support with isolated sessions (each agent can use a different backend)
- All data stored locally as Markdown files

## Permission modes

Control what the agent can do on your machine via `permission_mode` in config.json:

| Mode | Claude | Gemini | Codex |
|------|--------|--------|-------|
| `auto` | Auto-approve safe actions (default) | `auto_edit` | workspace-write |
| `acceptEdits` | Auto-approve file edits only | `auto_edit` | workspace-write |
| `bypassPermissions` | Approve everything | `yolo` | `--full-auto` |

## Multi-backend agents

You can run different agents on different backends:

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

Switch between them in chat: `!c agent coder`
