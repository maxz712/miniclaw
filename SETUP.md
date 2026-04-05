# MiniClaw Setup Guide

You are helping the user set up MiniClaw, a multi-platform AI assistant that bridges messaging platforms to the local Claude Code CLI.

## Step 1: Install dependencies

Run:
```bash
pip install discord.py python-telegram-bot slack-bolt "pywa[fastapi]" uvicorn
```

## Step 2: Ask which platforms to enable

Ask the user which platforms they want to set up. Options:
- **Discord** - needs a bot token from https://discord.com/developers/applications
- **Telegram** - needs a bot token from @BotFather on Telegram
- **Slack** - needs bot token + app token from https://api.slack.com/apps
- **WhatsApp** - needs Meta Business account + Cloud API credentials

For each platform the user wants, walk them through getting the token:

### Discord setup
1. Go to https://discord.com/developers/applications → New Application
2. Go to Bot tab → Reset Token → copy the token
3. Enable MESSAGE CONTENT INTENT under Privileged Gateway Intents
4. Go to OAuth2 → URL Generator → select `bot` scope → select `Send Messages` + `Read Message History` permissions
5. Copy the invite URL and open it to add the bot to their server

### Telegram setup
1. Message @BotFather on Telegram
2. Send /newbot, follow prompts
3. Copy the token BotFather gives you

### Slack setup
1. Go to https://api.slack.com/apps → Create New App → From Scratch
2. Under OAuth & Permissions, add scopes: `chat:write`, `channels:history`, `files:read`
3. Install to workspace, copy Bot User OAuth Token (xoxb-...)
4. Under Socket Mode, enable it and generate an App-Level Token (xapp-...)

### WhatsApp setup
1. Go to https://developers.facebook.com → Create App → Business type
2. Add WhatsApp product, get Phone Number ID and Access Token
3. Set up a webhook URL pointing to your server's port 8080
4. Set a Verify Token (any string you choose)

## Step 3: Update config.json

Edit config.json with the tokens the user provided. Set `enabled: true` for each platform they configured.

## Step 4: Configure the command prefix

Ask if they want to change the default command prefix from `!c` to something else.

## Step 5: Test

Run `python3 bot.py` and confirm it starts without errors. Tell the user to send a test message on their enabled platform using `!c hello`.

## Step 6: Optional - Heartbeat

Ask if they want proactive/scheduled features. If yes:
- Set `heartbeat.enabled` to `true` in config.json
- Set `heartbeat.notify` to point to a channel where alerts should go
- Edit `workspace/HEARTBEAT.md` with their checklist items

## Step 7: Optional - Custom agents

Ask if they want multiple AI personalities/agents. If yes, add entries to the `agents` object in config.json with different system prompts, models, or tool restrictions.
