from __future__ import annotations

from datetime import date
from pathlib import Path
import os

VAULT_ROOT = Path(os.path.expanduser("~/ObsidianVault"))

FILES = {
    VAULT_ROOT / "Agent-Shared" / "user-profile.md": "# User Profile\n\n- Name: Sam Dyer\n- Notes: Placeholder content.\n",
    VAULT_ROOT / "Agent-Shared" / "project-state.md": "# Project State\n\n| To Do | In Progress | Done |\n| --- | --- | --- |\n| Centrax (dental product; X/Twitter, Instagram, YouTube, Facebook, dental publications, blog) |  |  |\n| Manito (X/Twitter, Instagram, YouTube, Facebook) |  |  |\n| Sea of Ink (X/Twitter, Instagram, YouTube, Facebook, Pinterest) |  |  |\n| Dyer Consulting (LinkedIn, X/Twitter, YouTube) |  |  |\n",
    VAULT_ROOT / "Agent-Shared" / "decisions-log.md": "# Decisions Log\n\n- Placeholder content.\n",
    VAULT_ROOT / "Agent-Steven" / "working-context.md": "# Working Context\n\n- Placeholder content.\n",
    VAULT_ROOT / "Agent-Steven" / "mistakes.md": "# Mistakes\n\n- Placeholder content.\n",
    VAULT_ROOT / "Agent-Steven" / "daily" / f"{date.today().isoformat()}.md": "# Daily Log\n\n- Placeholder content.\n",
}


def ensure_file(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    (VAULT_ROOT / "Agent-Shared").mkdir(parents=True, exist_ok=True)
    (VAULT_ROOT / "Agent-Steven" / "daily").mkdir(parents=True, exist_ok=True)
    (VAULT_ROOT / "Agent-OpenClaw").mkdir(parents=True, exist_ok=True)

    for path, content in FILES.items():
        ensure_file(path, content)


if __name__ == "__main__":
    main()
