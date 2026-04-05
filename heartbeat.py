import asyncio
import logging
from pathlib import Path

logger = logging.getLogger("openclaw.heartbeat")


class Heartbeat:
    def __init__(self, claude_cli, skills, active_channels: dict, config: dict):
        self.claude_cli = claude_cli
        self.skills = skills
        self.channels = active_channels
        self.config = config
        self.hb_config = config.get("heartbeat", {})
        self.workspace = Path(config.get("workspace", "./workspace"))

    async def start(self):
        interval = self.hb_config.get("interval_minutes", 30) * 60
        logger.info(f"Heartbeat started, interval={interval}s")
        while True:
            await asyncio.sleep(interval)
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Heartbeat error: {e}")

    async def run_once(self):
        hb_file = self.workspace / "HEARTBEAT.md"
        if not hb_file.exists():
            return
        content = hb_file.read_text().strip()
        if not content or all(line.startswith("#") or not line.strip() for line in content.splitlines()):
            return

        prompt = f"Run your heartbeat check. Here is your checklist:\n\n{content}\n\nIf nothing needs attention, respond with exactly: HEARTBEAT_OK"
        agent = self.config["agents"].get("default", {})
        session_id = self.claude_cli.get_session_id("heartbeat:default")
        skills_prompt = self.skills.build_prompt()

        response = await self.claude_cli.ask(prompt, session_id, agent, skills_prompt)

        if "HEARTBEAT_OK" in response:
            logger.debug("Heartbeat: all clear")
            return

        # Notify configured channels
        for target in self.hb_config.get("notify", []):
            ch_name = target.get("channel")
            ch_id = target.get("id")
            if ch_name in self.channels and ch_id:
                try:
                    await self.channels[ch_name].send(ch_id, f"**Heartbeat Alert**\n{response}")
                except Exception as e:
                    logger.error(f"Failed to send heartbeat to {ch_name}:{ch_id}: {e}")
