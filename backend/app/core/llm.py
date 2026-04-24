"""Shared Anthropic client and JSON-output call helper.

Design rules (from SECURITY.md / PROMPTS.md):
  - All document content is passed as data, never as system instructions.
  - Prompts explicitly instruct the model to treat document text as untrusted.
  - Structured JSON output is required for every AI step.
  - Graceful fallback when API key is not set.
"""
import json
import logging
import re
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Anthropic client (lazy-initialised so tests that don't set a key still import)
# ---------------------------------------------------------------------------

_client = None


def _get_client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def call_claude_json(
    system: str,
    user: str,
    model: str = "claude-haiku-4-5-20251001",
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """
    Call Claude and return the parsed JSON from the response.

    Raises RuntimeError when ANTHROPIC_API_KEY is not set.
    Returns {} if the model's response cannot be parsed as JSON.
    """
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

    client = _get_client()
    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    raw = message.content[0].text if message.content else ""
    return _extract_json(raw)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract a JSON object from a response that may be wrapped in markdown fences."""
    text = text.strip()

    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # 3. First {...} found anywhere
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract JSON from LLM response (first 300 chars): %s", text[:300])
    return {}
