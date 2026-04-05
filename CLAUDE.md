# MiniClaw

A lightweight OpenClaw alternative. Bridges messaging platforms (Discord, Telegram, Slack, WhatsApp) to local AI coding CLIs (Claude Code, Gemini, Codex, Aider).

## Architecture

```
messaging platform → channel adapter → shared handler → CLI runner → AI CLI subprocess → response back
```

**Core files:**
- `bot.py` - Entry point. Loads config, starts enabled channel adapters, starts heartbeat.
- `channel.py` - `Channel` ABC, `Message` dataclass, `handle_message()` shared routing logic (access control, commands, prompt building, response chunking).
- `cli_runner.py` - `CLIRunner` class. Builds CLI commands per backend (claude/gemini/codex/aider), runs via `asyncio.create_subprocess_exec`, parses output. Session management (UUID per channel/user).
- `skills.py` - Loads `workspace/skills/*.md` SKILL.md files, parses YAML frontmatter, checks requirements, builds prompt text injected via system prompt flags.
- `heartbeat.py` - Async loop that reads `workspace/HEARTBEAT.md` on interval, calls CLI, sends alerts to configured notification channels.

**Channel adapters** (`channels/`):
- `discord_ch.py` - discord.py
- `telegram_ch.py` - python-telegram-bot
- `slack_ch.py` - slack-bolt (socket mode)
- `whatsapp_ch.py` - pywa + FastAPI webhook

**Workspace** (`workspace/`):
- `MEMORY.md` - Long-term facts (read/written by AI via `--add-dir`)
- `HEARTBEAT.md` - Proactive task checklist
- `memory/` - Daily notes
- `skills/` - SKILL.md files

## Key patterns

- All channel adapters convert platform events into a `Message` dataclass, then call `handle_message()`. Platform-specific logic stays in the adapter.
- `CLIRunner` uses a backend dispatch pattern: `BACKENDS` dict maps backend name → build/parse methods. Adding a backend = adding two methods.
- Session keys: `agent:<name>:<platform>:<channel_or_user_id>` → UUID
- Commands: `!c reset`, `!c agent <name>` are handled in `handle_message()` before reaching the CLI.

## Config

`config.json` has: `backend` (global default), `channels` (per-platform tokens + enabled flag), `agents` (each with optional backend/model/system_prompt/permission_mode), `heartbeat`, `permission_mode`, `command_prefix`, `allowed_user_ids`.

## Adding a new channel adapter

1. Create `channels/<name>_ch.py` implementing `Channel` (start, stop, send)
2. Add config block in `config.json`
3. Register in `ADAPTERS` dict in `bot.py`

## Adding a new AI backend

1. Add entry to `BACKENDS` dict in `cli_runner.py`
2. Add `_build_<name>_cmd()` and `_parse_<name>_output()` methods to `CLIRunner`

## Dependencies

```
pip install discord.py python-telegram-bot slack-bolt "pywa[fastapi]" uvicorn
```
