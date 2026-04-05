import asyncio
import json
import os
import uuid


# Each backend defines how to build CLI commands and parse output.
BACKENDS = {
    "claude": {
        "bin": "claude",
        "build_cmd": "_build_claude_cmd",
        "parse_output": "_parse_claude_output",
    },
    "gemini": {
        "bin": "gemini",
        "build_cmd": "_build_gemini_cmd",
        "parse_output": "_parse_gemini_output",
    },
    "codex": {
        "bin": "codex",
        "build_cmd": "_build_codex_cmd",
        "parse_output": "_parse_codex_output",
    },
    "aider": {
        "bin": "aider",
        "build_cmd": "_build_aider_cmd",
        "parse_output": "_parse_text_output",
    },
}


class CLIRunner:
    def __init__(self, config):
        self.config = config
        self.sessions: dict[str, str] = {}
        self.agent_selection: dict[str, str] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    def get_session_key(self, agent_name, platform, channel_id, user_id, session_per):
        target = channel_id if session_per == "channel" else user_id
        return f"agent:{agent_name}:{platform}:{target}"

    def get_session_id(self, key):
        if key not in self.sessions:
            self.sessions[key] = str(uuid.uuid4())
        return self.sessions[key]

    def reset_session(self, key):
        self.sessions.pop(key, None)

    def get_agent(self, platform, channel_id):
        key = f"{platform}:{channel_id}"
        name = self.agent_selection.get(key, "default")
        agent = self.config["agents"].get(name, self.config["agents"]["default"])
        return name, agent

    def set_agent(self, platform, channel_id, agent_name):
        if agent_name not in self.config["agents"]:
            return False
        self.agent_selection[f"{platform}:{channel_id}"] = agent_name
        return True

    def _get_lock(self, session_id):
        if session_id not in self._locks:
            self._locks[session_id] = asyncio.Lock()
        return self._locks[session_id]

    async def ask(self, prompt, session_id, agent, skills_prompt=""):
        backend_name = agent.get("backend") or self.config.get("backend", "claude")
        backend = BACKENDS.get(backend_name)
        if not backend:
            return f"[Error: unknown backend '{backend_name}']"

        cmd, env = getattr(self, backend["build_cmd"])(prompt, session_id, agent, skills_prompt)
        parse_fn = getattr(self, backend["parse_output"])
        timeout = self.config.get("subprocess_timeout_seconds", 300)

        # Serialize requests per session to prevent "session already in use" errors
        async with self._get_lock(session_id):
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                env={**os.environ, **env} if env else None,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return f"[Error: {backend_name} timed out after {timeout}s]"

        if proc.returncode != 0:
            err = stderr.decode(errors="replace").strip()[:500]
            return f"[Error: {backend_name} exited with code {proc.returncode}]\n{err}"

        return parse_fn(stdout.decode(errors="replace"))

    # ── Claude ──────────────────────────────────────────────

    def _build_claude_cmd(self, prompt, session_id, agent, skills_prompt):
        workspace = self.config.get("workspace", "./workspace")
        cmd = ["claude", "--session-id", session_id, "-p", prompt,
               "--output-format", "json", "--add-dir", workspace]
        perm = agent.get("permission_mode") or self.config.get("permission_mode", "auto")
        cmd += ["--permission-mode", perm]
        if skills_prompt:
            cmd += ["--append-system-prompt", skills_prompt]
        if agent.get("system_prompt"):
            cmd += ["--system-prompt", agent["system_prompt"]]
        if agent.get("model"):
            cmd += ["--model", agent["model"]]
        if agent.get("allowed_tools"):
            cmd += ["--allowed-tools", agent["allowed_tools"]]
        return cmd, {}

    def _parse_claude_output(self, text):
        try:
            data = json.loads(text)
            return data.get("result", "[No result in response]")
        except json.JSONDecodeError:
            return text.strip() or "[Empty response]"

    # ── Gemini ──────────────────────────────────────────────

    def _build_gemini_cmd(self, prompt, session_id, agent, skills_prompt):
        cmd = ["gemini", "-p", prompt, "-o", "json"]
        approval = agent.get("permission_mode") or self.config.get("permission_mode", "auto")
        approval_map = {"auto": "auto_edit", "bypassPermissions": "yolo", "acceptEdits": "auto_edit"}
        cmd += ["--approval-mode", approval_map.get(approval, approval)]
        if agent.get("model"):
            cmd += ["-m", agent["model"]]
        # Gemini uses env var for system prompt, and .gemini/system.md file
        env = {}
        if agent.get("system_prompt"):
            # Write system prompt to workspace and point env to it
            sp_path = os.path.join(self.config.get("workspace", "./workspace"), ".gemini_system.md")
            with open(sp_path, "w") as f:
                f.write(agent["system_prompt"])
                if skills_prompt:
                    f.write("\n\n" + skills_prompt)
            env["GEMINI_SYSTEM_MD"] = sp_path
        elif skills_prompt:
            sp_path = os.path.join(self.config.get("workspace", "./workspace"), ".gemini_system.md")
            with open(sp_path, "w") as f:
                f.write(skills_prompt)
            env["GEMINI_SYSTEM_MD"] = sp_path
        return cmd, env

    def _parse_gemini_output(self, text):
        try:
            data = json.loads(text)
            return data.get("response", data.get("text", data.get("result", text.strip())))
        except json.JSONDecodeError:
            return text.strip() or "[Empty response]"

    # ── Codex ───────────────────────────────────────────────

    def _build_codex_cmd(self, prompt, session_id, agent, skills_prompt):
        full_prompt = prompt
        if skills_prompt:
            full_prompt = f"{skills_prompt}\n\n{prompt}"
        cmd = ["codex", "exec", full_prompt, "--json"]
        approval = agent.get("permission_mode") or self.config.get("permission_mode", "auto")
        if approval == "bypassPermissions":
            cmd += ["--full-auto"]
        else:
            cmd += ["-s", "workspace-write"]
        if agent.get("model"):
            cmd += ["-c", f"model={agent['model']}"]
        return cmd, {}

    def _parse_codex_output(self, text):
        # Codex outputs JSONL - take last non-empty line
        lines = [l for l in text.strip().splitlines() if l.strip()]
        if not lines:
            return "[Empty response]"
        try:
            data = json.loads(lines[-1])
            return data.get("content", data.get("text", data.get("message", lines[-1])))
        except json.JSONDecodeError:
            return text.strip()

    # ── Aider ───────────────────────────────────────────────

    def _build_aider_cmd(self, prompt, session_id, agent, skills_prompt):
        full_prompt = prompt
        if skills_prompt:
            full_prompt = f"{skills_prompt}\n\n{prompt}"
        cmd = ["aider", "--message", full_prompt, "--yes", "--no-pretty", "--no-stream"]
        if agent.get("model"):
            cmd += ["--model", agent["model"]]
        return cmd, {}

    def _parse_text_output(self, text):
        return text.strip() or "[Empty response]"
