"""
Pydantic models defining the API data contracts between backend ↔ frontend.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


# ── Chat Request / Response ────────────────────────────────────────────────


class HistoryMessage(BaseModel):
    """A single turn in conversation history."""

    role: str = Field(..., pattern="^(user|assistant)$", description="Either 'user' or 'assistant'.")
    content: str


class ChatRequest(BaseModel):
    """POST /api/v1/chat request body."""

    query: str = Field(..., min_length=1, description="The user's current question.")
    session_id: str = Field(..., description="Unique session identifier for multi-turn context.")
    history: list[HistoryMessage] = Field(
        default_factory=list,
        description="Previous conversation turns (oldest first).",
    )


class TokenEvent(BaseModel):
    """SSE payload for a single streamed token."""

    type: str = "token"
    content: str


class CitationSource(BaseModel):
    """One retrieved chunk's provenance."""

    source_file: str
    page_number: int
    score: float


class CitationsEvent(BaseModel):
    """SSE payload appended after the last token event."""

    type: str = "citations"
    sources: list[CitationSource]


# ── Document Upload ────────────────────────────────────────────────────────


class UploadResponse(BaseModel):
    """POST /api/v1/documents/upload response body."""

    status: str = "success"
    filename: str
    chunks_indexed: int
