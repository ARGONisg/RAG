"""
Chat streaming router — POST /api/v1/chat

Accepts a chat request, orchestrates the RAG pipeline, and returns
Server-Sent Events with token chunks, citation metadata, and [DONE].
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, status
from sse_starlette.sse import EventSourceResponse

from schemas import ChatRequest
from streamer import sse_stream

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Chat"])


@router.post(
    "/chat",
    status_code=status.HTTP_200_OK,
    summary="Chat with the RAG system (SSE stream)",
    response_description="Server-Sent Events stream of token chunks followed by citations and [DONE].",
)
async def chat(request: ChatRequest):
    """
    Orchestrate query condensing → retrieval → LLM streaming.

    Returns an ``EventSourceResponse`` whose ``data`` lines follow the
    contract documented in the project spec:

    - ``{"type": "token", "content": "..."}``
    - ``{"type": "citations", "sources": [...]}``
    - ``[DONE]``
    """
    logger.info(
        "[%s] New chat request — query=%r, history_turns=%d",
        request.session_id,
        request.query,
        len(request.history),
    )

    return EventSourceResponse(
        sse_stream(
            query=request.query,
            session_id=request.session_id,
            history=request.history,
        ),
        media_type="text/event-stream",
    )
