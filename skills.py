import os
import re
import shutil
from pathlib import Path


class SkillLoader:
    def __init__(self, skills_dir: str):
        self.skills_dir = Path(skills_dir)
        self._cache: list[dict] = []
        self._mtime: float = 0

    def _parse_frontmatter(self, text: str) -> tuple[dict, str]:
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
        if not m:
            return {}, text
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        return meta, m.group(2)

    def _check_requires(self, meta: dict) -> bool:
        requires = meta.get("requires", "")
        if not requires:
            return True
        # Simple check: comma-separated bin names
        for bin_name in requires.split(","):
            bin_name = bin_name.strip()
            if bin_name.startswith("env:"):
                if not os.environ.get(bin_name[4:]):
                    return False
            elif bin_name and not shutil.which(bin_name):
                return False
        return True

    def load_skills(self) -> list[dict]:
        if not self.skills_dir.exists():
            return []
        mtime = max((f.stat().st_mtime for f in self.skills_dir.glob("*.md")), default=0)
        if mtime == self._mtime and self._cache:
            return self._cache
        self._mtime = mtime
        skills = []
        for path in sorted(self.skills_dir.glob("*.md")):
            meta, body = self._parse_frontmatter(path.read_text())
            if not self._check_requires(meta):
                continue
            skills.append({"name": meta.get("name", path.stem), "description": meta.get("description", ""), "body": body.strip()})
        self._cache = skills
        return skills

    def build_prompt(self) -> str:
        skills = self.load_skills()
        if not skills:
            return ""
        lines = ["Available skills:"]
        for s in skills:
            lines.append(f"- {s['name']}: {s['description']}")
            if s["body"]:
                lines.append(f"  Instructions: {s['body'][:200]}")
        return "\n".join(lines)
