from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Message:
    platform: str
    channel_id: str
    user_id: str
    user_name: str
    text: str
    attachments: list[str] = field(default_factory=list)
    reply: Callable = None  # async fn(text)
    raw: Any = None


class Channel(ABC):
    name: str = ""
    msg_limit: int = 2000

    def __init__(self, ch_config, cli_runner, skills, config):
        self.ch_config = ch_config
        self.cli = cli_runner
        self.skills = skills
        self.config = config
        self.msg_limit = ch_config.get("msg_limit", 2000)

    @abstractmethod
    async def start(self): ...

    @abstractmethod
    async def stop(self): ...

    @abstractmethod
    async def send(self, channel_id: str, text: str): ...


def split_message(text: str, limit: int = 2000) -> list[str]:
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")
    return chunks


async def handle_message(msg: Message, cli, skills, config):
    allowed = config.get("allowed_user_ids", [])
    if allowed and msg.user_id not in allowed:
        return

    prefix = config.get("command_prefix", "!c")
    text = msg.text.strip()

    if not text.startswith(prefix):
        return
    text = text[len(prefix):].strip()
    if not text:
        return

    # Commands
    if text.lower() in ("reset", "new", "clear"):
        agent_name, agent = cli.get_agent(msg.platform, msg.channel_id)
        key = cli.get_session_key(agent_name, msg.platform, msg.channel_id, msg.user_id, agent.get("session_per", "channel"))
        cli.reset_session(key)
        await msg.reply("Session reset.")
        return

    if text.lower().startswith("agent "):
        agent_name = text[6:].strip()
        if cli.set_agent(msg.platform, msg.channel_id, agent_name):
            await msg.reply(f"Switched to agent: {agent_name}")
        else:
            available = ", ".join(config["agents"].keys())
            await msg.reply(f"Unknown agent. Available: {available}")
        return

    # Build prompt
    agent_name, agent = cli.get_agent(msg.platform, msg.channel_id)
    prompt = f"[{msg.platform} user: {msg.user_name}] {text}"
    if msg.attachments:
        prompt += "\n\nAttached files:\n" + "\n".join(f"- {p}" for p in msg.attachments)

    key = cli.get_session_key(agent_name, msg.platform, msg.channel_id, msg.user_id, agent.get("session_per", "channel"))
    session_id = cli.get_session_id(key)
    skills_prompt = skills.build_prompt()

    response = await cli.ask(prompt, session_id, agent, skills_prompt)

    max_len = config.get("max_response_length", 8000)
    if len(response) > max_len:
        response = response[:max_len] + "\n\n[...truncated]"

    msg_limit = config.get("channels", {}).get(msg.platform, {}).get("msg_limit", 2000)
    for chunk in split_message(response, msg_limit):
        await msg.reply(chunk)
