import asyncio
import json
import uuid


class ClaudeCLI:
    def __init__(self, config):
        self.config = config
        self.sessions: dict[str, str] = {}
        self.agent_selection: dict[str, str] = {}  # channel_key -> agent_name

    def get_session_key(self, agent_name: str, platform: str, channel_id: str, user_id: str, session_per: str) -> str:
        target = channel_id if session_per == "channel" else user_id
        return f"agent:{agent_name}:{platform}:{target}"

    def get_session_id(self, key: str) -> str:
        if key not in self.sessions:
            self.sessions[key] = str(uuid.uuid4())
        return self.sessions[key]

    def reset_session(self, key: str):
        self.sessions.pop(key, None)

    def get_agent(self, platform: str, channel_id: str) -> tuple[str, dict]:
        key = f"{platform}:{channel_id}"
        name = self.agent_selection.get(key, "default")
        agent = self.config["agents"].get(name, self.config["agents"]["default"])
        return name, agent

    def set_agent(self, platform: str, channel_id: str, agent_name: str) -> bool:
        if agent_name not in self.config["agents"]:
            return False
        self.agent_selection[f"{platform}:{channel_id}"] = agent_name
        return True

    async def ask(self, prompt: str, session_id: str, agent: dict, skills_prompt: str = "") -> str:
        timeout = self.config.get("subprocess_timeout_seconds", 300)
        workspace = self.config.get("workspace", "./workspace")

        cmd = ["claude", "--session-id", session_id, "-p", prompt, "--output-format", "json", "--add-dir", workspace]

        # Permission mode: needed for non-interactive -p mode so Claude can actually act
        # "acceptEdits" = auto-approve file edits, prompt for shell commands
        # "auto" = auto-approve safe actions, prompt for risky ones
        # "bypassPermissions" = approve everything (use with caution)
        permission_mode = agent.get("permission_mode") or self.config.get("permission_mode", "auto")
        cmd += ["--permission-mode", permission_mode]

        if skills_prompt:
            cmd += ["--append-system-prompt", skills_prompt]
        if agent.get("system_prompt"):
            cmd += ["--system-prompt", agent["system_prompt"]]
        if agent.get("model"):
            cmd += ["--model", agent["model"]]
        if agent.get("allowed_tools"):
            cmd += ["--allowed-tools", agent["allowed_tools"]]

        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"[Error: timed out after {timeout}s]"

        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()[:500]
            return f"[Error: claude exited with code {proc.returncode}]\n{err}"

        try:
            data = json.loads(stdout.decode())
            return data.get("result", "[No result in response]")
        except json.JSONDecodeError:
            return stdout.decode(errors="replace").strip() or "[Empty response]"
