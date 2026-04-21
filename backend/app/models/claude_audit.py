"""
Claude AI audit log model.
Records token usage and outcomes for every Claude API call — no raw prompts or PII.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ClaudeAuditLog(Base):
    """One row per Claude API call."""

    __tablename__ = "claude_audit_logs"

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # Which feature triggered the call: 'weekly_review', 'meal_variations', 'pdf_parse'
    feature: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_read_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_write_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 'ok' | 'error' | 'fallback'
    outcome: Mapped[str] = mapped_column(String(20), nullable=False, default="ok")
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
