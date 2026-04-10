import logging
import os
from pathlib import Path
from typing import Any, Optional

from google import genai
from google.genai import errors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMWrapper:
    """Route requests to Gemma 4 first, then fall back to Gemini 2.5 Flash."""

    def __init__(self, api_key: Optional[str] = None):
        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=resolved_api_key)
        self.primary_model = "gemma-4-31b-it"
        self.fallback_model = "gemini-2.5-flash"
        self.repo_root = Path(__file__).resolve().parent

    def _read_local_file(self, filename: str) -> str:
        path = self.repo_root / filename
        if not path.exists():
            logger.warning("Missing prompt layer file: %s", path)
            return ""
        return path.read_text(encoding="utf-8")

    def _build_prompt(self, prompt: str) -> str:
        sections = [
            self._read_local_file("memory.md"),
            self._read_local_file("AGENTS.md"),
            self._read_local_file("SOUL.md"),
            prompt,
        ]
        return "\n\n---\n\n".join(section for section in sections if section)

    def _vault_path(self) -> Path:
        memory_text = self._read_local_file("memory.md")
        vault_path = os.path.expanduser("~/ObsidianVault")
        for line in memory_text.splitlines():
            if line.startswith("VAULT_PATH:"):
                vault_path = line.split("VAULT_PATH:", 1)[1].strip()
                break
        return Path(os.path.expanduser(vault_path))

    def read_vault_file(self, relative_path: str) -> str:
        path = self._vault_path() / relative_path
        if not path.exists():
            logger.warning("Vault file missing: %s", path)
            return ""
        return path.read_text(encoding="utf-8")

    def write_vault_file(self, relative_path: str, content: str, append: bool = False) -> None:
        path = self._vault_path() / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if append and path.exists():
            with path.open("a", encoding="utf-8") as handle:
                handle.write(content)
        else:
            path.write_text(content, encoding="utf-8")

    def generate_content(self, prompt: str, **kwargs: Any) -> str:
        expanded_prompt = self._build_prompt(prompt)
        try:
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=expanded_prompt,
                **kwargs,
            )
            return response.text

        except errors.APIError as e:
            logger.warning(
                "Primary model (%s) failed — code %s: %s. Falling back to %s.",
                self.primary_model,
                getattr(e, "code", None),
                getattr(e, "message", str(e)),
                self.fallback_model,
            )
            try:
                fallback_response = self.client.models.generate_content(
                    model=self.fallback_model,
                    contents=expanded_prompt,
                    **kwargs,
                )
                return fallback_response.text
            except errors.APIError as fallback_error:
                logger.error(
                    "Fallback model (%s) also failed — code %s: %s.",
                    self.fallback_model,
                    getattr(fallback_error, "code", None),
                    getattr(fallback_error, "message", str(fallback_error)),
                )
                raise
