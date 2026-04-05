import asyncio
import logging

from pywa import WhatsApp as PyWa
from pywa.types import Message as WaMessage
from fastapi import FastAPI
import uvicorn

from channel import Channel, Message, handle_message

logger = logging.getLogger("openclaw.whatsapp")


class WhatsAppChannel(Channel):
    name = "whatsapp"

    async def start(self):
        self.fastapi = FastAPI()
        self.wa = PyWa(
            phone_id=self.ch_config["phone_number_id"],
            token=self.ch_config["access_token"],
            server=self.fastapi,
            verify_token=self.ch_config["verify_token"],
        )
        ch = self

        @self.wa.on_message()
        async def on_message(client: PyWa, wa_msg: WaMessage):
            attachments = []
            if wa_msg.image:
                path = wa_msg.image.download(in_memory=False)
                attachments.append(str(path))
            if wa_msg.document:
                path = wa_msg.document.download(in_memory=False)
                attachments.append(str(path))

            async def reply(text):
                client.send_message(to=wa_msg.from_user.wa_id, text=text)

            msg = Message(
                platform="whatsapp", channel_id=wa_msg.from_user.wa_id,
                user_id=wa_msg.from_user.wa_id, user_name=wa_msg.from_user.name or "",
                text=wa_msg.text or "", attachments=attachments, reply=reply, raw=wa_msg,
            )
            await handle_message(msg, ch.cli, ch.skills, ch.config)

        port = self.ch_config.get("webhook_port", 8080)
        config = uvicorn.Config(self.fastapi, host="0.0.0.0", port=port, log_level="warning")
        server = uvicorn.Server(config)
        asyncio.create_task(server.serve())
        logger.info(f"WhatsApp webhook listening on port {port}")

    async def stop(self):
        pass

    async def send(self, phone_number: str, text: str):
        self.wa.send_message(to=phone_number, text=text)
