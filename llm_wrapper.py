import logging
import os
from typing import Any

from google import genai
from google.genai import errors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMWrapper:
    """Route requests to Gemma 4 first, then fall back to Gemini 2.5 Flash."""

    def __init__(self, api_key: str | None = None):
        resolved_api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=resolved_api_key)
        self.primary_model = "gemma-4-31b-it"
        self.fallback_model = "gemini-2.5-flash"

    def generate_content(self, prompt: str, **kwargs: Any) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.primary_model,
                contents=prompt,
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
                    contents=prompt,
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
