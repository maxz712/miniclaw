# MiniClaw Setup Guide

You are helping the user set up MiniClaw, a multi-platform AI assistant that bridges messaging platforms to local AI coding CLIs (Claude Code, Gemini, Codex, or Aider).

## Step 1: Install dependencies

Run:
```bash
pip install discord.py python-telegram-bot slack-bolt "pywa[fastapi]" uvicorn
```

## Step 2: Choose AI backend

Ask the user which AI CLI they want to use as their default backend:
- **Claude Code** (`claude`) - needs Claude Code installed and authenticated
- **Gemini CLI** (`gemini`) - needs Gemini CLI installed and authenticated
- **Codex CLI** (`codex`) - needs Codex CLI installed and authenticated
- **Aider** (`aider`) - needs `pip install aider-chat` and an API key for their chosen model

Verify the chosen CLI is installed by running `which <cli_name>`. Set the `"backend"` field in config.json.

## Step 3: Choose messaging platforms

Ask the user which platforms they want to set up. Options:
- **Discord** - needs a bot token from https://discord.com/developers/applications
- **Telegram** - needs a bot token from @BotFather on Telegram
- **Slack** - needs bot token + app token from https://api.slack.com/apps
- **WhatsApp** - needs Meta Business account + Cloud API credentials

For each platform the user wants, walk them through getting the token:

### Discord setup
1. Go to https://discord.com/developers/applications -> New Application
2. Go to Bot tab -> Reset Token -> copy the token
3. Enable MESSAGE CONTENT INTENT under Privileged Gateway Intents
4. Go to OAuth2 -> URL Generator -> select `bot` scope -> select `Send Messages` + `Read Message History` permissions
5. Copy the invite URL and open it to add the bot to their server

### Telegram setup
1. Message @BotFather on Telegram
2. Send /newbot, follow prompts
3. Copy the token BotFather gives you

### Slack setup
1. Go to https://api.slack.com/apps -> Create New App -> From Scratch
2. Under OAuth & Permissions, add scopes: `chat:write`, `channels:history`, `files:read`
3. Install to workspace, copy Bot User OAuth Token (xoxb-...)
4. Under Socket Mode, enable it and generate an App-Level Token (xapp-...)

### WhatsApp setup
1. Go to https://developers.facebook.com -> Create App -> Business type
2. Add WhatsApp product, get Phone Number ID and Access Token
3. Set up a webhook URL pointing to your server's port 8080
4. Set a Verify Token (any string you choose)

## Step 4: Update config.json

Edit config.json with:
- `"backend"` set to their chosen AI CLI
- Tokens for each enabled platform
- `"enabled": true` for each configured platform

## Step 5: Configure the command prefix

Ask if they want to change the default command prefix from `!c` to something else.

## Step 6: Choose permission mode

Ask what level of autonomy the agent should have:
- `"auto"` (default) - auto-approves safe actions, blocks risky ones
- `"acceptEdits"` - auto-approves file edits, blocks shell commands
- `"bypassPermissions"` - approves everything (full autonomous coding)

Set `"permission_mode"` in config.json.

## Step 7: Test

Run `python3 bot.py` and confirm it starts without errors. Tell the user to send a test message on their enabled platform using `!c hello`.

## Step 8: Optional - Heartbeat

Ask if they want proactive/scheduled features. If yes:
- Set `heartbeat.enabled` to `true` in config.json
- Set `heartbeat.notify` to point to a channel where alerts should go
- Edit `workspace/HEARTBEAT.md` with their checklist items

## Step 9: Optional - Multi-agent with different backends

Ask if they want multiple AI agents. If yes, add entries to the `agents` object in config.json. Each agent can have its own `backend`, `model`, `system_prompt`, and `permission_mode`. Example:

```json
{
  "default": {
    "backend": "claude",
    "system_prompt": "You are a helpful assistant."
  },
  "coder": {
    "backend": "gemini",
    "model": "gemini-2.5-pro",
    "system_prompt": "You are a code assistant."
  }
}
```

Users switch agents in chat with `!c agent coder`.
