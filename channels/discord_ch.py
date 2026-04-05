import asyncio
import logging
import tempfile
from pathlib import Path

import discord
from discord import app_commands

from channel import Channel, Message, handle_message

log = logging.getLogger("openclaw")


class DiscordChannel(Channel):
    name = "discord"

    async def start(self):
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        self.tree = app_commands.CommandTree(self.client)
        ch = self

        # -- Native Discord slash commands --

        @self.tree.command(name="reset", description="Reset the current AI session")
        async def slash_reset(interaction: discord.Interaction):
            agent_name, agent = ch.cli.get_agent("discord", str(interaction.channel_id))
            key = ch.cli.get_session_key(agent_name, "discord", str(interaction.channel_id),
                                          str(interaction.user.id), agent.get("session_per", "channel"))
            ch.cli.reset_session(key)
            await interaction.response.send_message("Session reset.")

        @self.tree.command(name="agent", description="Switch AI agent")
        @app_commands.describe(name="Agent name to switch to")
        async def slash_agent(interaction: discord.Interaction, name: str):
            if ch.cli.set_agent("discord", str(interaction.channel_id), name):
                await interaction.response.send_message(f"Switched to agent: {name}")
            else:
                available = ", ".join(ch.config["agents"].keys())
                await interaction.response.send_message(f"Unknown agent. Available: {available}")

        @self.client.event
        async def on_ready():
            await self.tree.sync()
            log.info("Discord slash commands synced")

        # -- Message handler --

        @self.client.event
        async def on_message(message):
            if message.author.bot:
                return

            # Download attachments
            attachments = []
            for att in message.attachments:
                path = Path(tempfile.gettempdir()) / att.filename
                await att.save(path)
                attachments.append(str(path))

            async def reply(text):
                await message.reply(text, mention_author=False)

            msg = Message(
                platform="discord", channel_id=str(message.channel.id),
                user_id=str(message.author.id), user_name=message.author.display_name,
                text=message.content, attachments=attachments, reply=reply, raw=message,
            )
            try:
                async with message.channel.typing():
                    await handle_message(msg, ch.cli, ch.skills, ch.config)
            except Exception:
                log.exception("Error handling message")

        asyncio.create_task(self.client.start(self.ch_config["token"]))

    async def stop(self):
        await self.client.close()

    async def send(self, channel_id: str, text: str):
        channel = self.client.get_channel(int(channel_id))
        if channel:
            await channel.send(text)
