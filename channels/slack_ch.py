import asyncio

from slack_bolt.async_app import AsyncApp
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

from channel import Channel, Message, handle_message


class SlackChannel(Channel):
    name = "slack"

    async def start(self):
        self.app = AsyncApp(token=self.ch_config["bot_token"])
        ch = self

        @self.app.event("message")
        async def on_message(event, say, client):
            if event.get("subtype") or event.get("bot_id"):
                return
            # Download files
            attachments = []
            for f in event.get("files", []):
                url = f.get("url_private_download")
                if url:
                    attachments.append(url)  # pass URL; claude can fetch it

            async def reply(text):
                await say(text=text, thread_ts=event.get("ts"))

            msg = Message(
                platform="slack", channel_id=event["channel"],
                user_id=event["user"], user_name=event.get("user", ""),
                text=event.get("text", ""), attachments=attachments, reply=reply, raw=event,
            )
            await handle_message(msg, ch.claude_cli, ch.skills, ch.config)

        handler = AsyncSocketModeHandler(self.app, self.ch_config["app_token"])
        asyncio.create_task(handler.start_async())

    async def stop(self):
        pass

    async def send(self, channel_id: str, text: str):
        await self.app.client.chat_postMessage(channel=channel_id, text=text)
