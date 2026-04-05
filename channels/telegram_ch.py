import asyncio
import tempfile
from pathlib import Path

from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

from channel import Channel, Message, handle_message


class TelegramChannel(Channel):
    name = "telegram"

    async def start(self):
        self.app = Application.builder().token(self.ch_config["token"]).build()
        ch = self

        async def on_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
            msg = update.message
            if not msg or not msg.text:
                return
            # Download attachments
            attachments = []
            if msg.document:
                f = await context.bot.get_file(msg.document.file_id)
                path = Path(tempfile.gettempdir()) / msg.document.file_name
                await f.download_to_drive(path)
                attachments.append(str(path))
            if msg.photo:
                f = await context.bot.get_file(msg.photo[-1].file_id)
                path = Path(tempfile.gettempdir()) / f"{f.file_id}.jpg"
                await f.download_to_drive(path)
                attachments.append(str(path))

            async def reply(text):
                await msg.reply_text(text)

            m = Message(
                platform="telegram", channel_id=str(msg.chat_id),
                user_id=str(msg.from_user.id), user_name=msg.from_user.first_name or "",
                text=msg.text, attachments=attachments, reply=reply, raw=msg,
            )
            await context.bot.send_chat_action(chat_id=msg.chat_id, action="typing")
            await handle_message(m, ch.cli, ch.skills, ch.config)

        self.app.add_handler(MessageHandler(filters.TEXT, on_message))
        await self.app.initialize()
        await self.app.start()
        asyncio.create_task(self.app.updater.start_polling())

    async def stop(self):
        await self.app.updater.stop()
        await self.app.stop()
        await self.app.shutdown()

    async def send(self, chat_id: str, text: str):
        await self.app.bot.send_message(chat_id=int(chat_id), text=text)
