import asyncio
import json
import logging
import sys
from pathlib import Path

from claude_cli import ClaudeCLI
from skills import SkillLoader
from heartbeat import Heartbeat

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger("openclaw")

ADAPTERS = {
    "discord": ("channels.discord_ch", "DiscordChannel"),
    "telegram": ("channels.telegram_ch", "TelegramChannel"),
    "slack": ("channels.slack_ch", "SlackChannel"),
    "whatsapp": ("channels.whatsapp_ch", "WhatsAppChannel"),
}


def load_adapter(name, ch_config, claude_cli, skills, config):
    if name not in ADAPTERS:
        logger.warning(f"Unknown channel: {name}")
        return None
    module_path, class_name = ADAPTERS[name]
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls(ch_config, claude_cli, skills, config)


async def main():
    config_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("config.json")
    config = json.loads(config_path.read_text())

    claude_cli = ClaudeCLI(config)
    skills = SkillLoader(str(Path(config.get("workspace", "./workspace")) / "skills"))

    active_channels = {}
    for name, ch_config in config.get("channels", {}).items():
        if not ch_config.get("enabled"):
            continue
        adapter = load_adapter(name, ch_config, claude_cli, skills, config)
        if adapter:
            await adapter.start()
            active_channels[name] = adapter
            logger.info(f"Started channel: {name}")

    if not active_channels:
        logger.error("No channels enabled. Enable at least one in config.json.")
        return

    if config.get("heartbeat", {}).get("enabled"):
        hb = Heartbeat(claude_cli, skills, active_channels, config)
        asyncio.create_task(hb.start())
        logger.info("Heartbeat started")

    logger.info(f"OpenClaw running with channels: {', '.join(active_channels)}")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
