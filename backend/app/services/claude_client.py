"""
Shared Anthropic Claude client with prompt caching helpers.
Usage:
    from app.services.claude_client import claude, heavy_claude, make_cached_block
"""
from typing import Any

import anthropic

from app.core.settings import settings

claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)


def heavy_claude() -> anthropic.Anthropic:
    """Return a client configured to use the heavy (Opus) model."""
    return claude


def make_cached_block(content: str) -> dict[str, Any]:
    """Wrap static prompt content in a cache_control block (ephemeral TTL)."""
    return {
        "type": "text",
        "text": content,
        "cache_control": {"type": "ephemeral"},
    }


def default_model() -> str:
    return settings.CLAUDE_MODEL_DEFAULT


def heavy_model() -> str:
    return settings.CLAUDE_MODEL_HEAVY
