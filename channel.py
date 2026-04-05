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


def _get_response_mode(msg, config):
    ch_config = config.get("channels", {}).get(msg.platform, {})
    return ch_config.get("response_mode") or config.get("response_mode", "command")


def _extract_prompt(msg, config):
    """Return (text, is_command) or None if message should be ignored."""
    text = msg.text.strip()
    if not text:
        return None
    mode = _get_response_mode(msg, config)

    # /commands always work in both modes
    if text.startswith("/"):
        return text[1:].strip(), True

    # Legacy prefix commands (!c etc) work in command mode
    prefix = config.get("command_prefix", "!c")
    if text.startswith(prefix):
        cmd = text[len(prefix):].strip()
        if cmd:
            return cmd, True
        return None

    # In auto mode, every message is a prompt
    if mode == "auto":
        return text, False

    # In command mode, ignore messages without prefix
    return None


async def handle_command(msg, cli, config, cmd_text):
    """Handle /reset, /agent, etc. Returns True if handled."""
    if cmd_text.lower() in ("reset", "new", "clear"):
        agent_name, agent = cli.get_agent(msg.platform, msg.channel_id)
        key = cli.get_session_key(agent_name, msg.platform, msg.channel_id, msg.user_id, agent.get("session_per", "channel"))
        cli.reset_session(key)
        await msg.reply("Session reset.")
        return True

    if cmd_text.lower().startswith("agent "):
        agent_name = cmd_text[6:].strip()
        if cli.set_agent(msg.platform, msg.channel_id, agent_name):
            await msg.reply(f"Switched to agent: {agent_name}")
        else:
            available = ", ".join(config["agents"].keys())
            await msg.reply(f"Unknown agent. Available: {available}")
        return True

    return False


async def handle_message(msg: Message, cli, skills, config):
    allowed = config.get("allowed_user_ids", [])
    if allowed and msg.user_id not in allowed:
        return

    result = _extract_prompt(msg, config)
    if result is None:
        return

    text, is_command = result

    # Try handling as a bot command first
    if is_command and await handle_command(msg, cli, config, text):
        return

    # If it was a /command we don't recognize, treat as prompt in auto mode, ignore in command mode
    if is_command and _get_response_mode(msg, config) == "command":
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
