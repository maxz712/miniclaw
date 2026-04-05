import asyncio
import tempfile
from pathlib import Path

import discord

from channel import Channel, Message, handle_message


class DiscordChannel(Channel):
    name = "discord"

    async def start(self):
        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        ch = self  # capture for closure

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
            async with message.channel.typing():
                await handle_message(msg, ch.cli, ch.skills, ch.config)

        asyncio.create_task(self.client.start(self.ch_config["token"]))

    async def stop(self):
        await self.client.close()

    async def send(self, channel_id: str, text: str):
        channel = self.client.get_channel(int(channel_id))
        if channel:
            await channel.send(text)
