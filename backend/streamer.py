"""
SSE streaming helper — wraps the RAG chain output into the exact
Server-Sent Events format the frontend expects.

Event shapes:
    Token:      data: {"type": "token", "content": "The "}\n\n
    Citations:  data: {"type": "citations", "sources": [...]}\n\n
    Done:       data: [DONE]\n\n
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from chains import condense_question, retrieve_context, stream_answer
from retrieval_bridge import chunks_to_citations
from schemas import CitationsEvent, HistoryMessage, TokenEvent

logger = logging.getLogger(__name__)


async def sse_stream(
    query: str,
    session_id: str,
    history: list[HistoryMessage],
    doc_name: str | None = None,
) -> AsyncIterator[str]:
    """
    Full orchestration generator consumed by ``EventSourceResponse``.

    1.  Condense the query (if history is present).
    2.  Retrieve & filter context chunks (isolated to doc_name if provided).
    3.  Stream LLM tokens as SSE ``token`` events.
    4.  Emit a ``citations`` event with source metadata.
    5.  Emit ``[DONE]`` sentinel.

    Yields:
        Strings formatted as SSE ``data:`` lines.
    """
    # ── 1. Condense ────────────────────────────────────────────────────────
    standalone_query = await condense_question(query, history)
    logger.info("[%s] standalone query: %s (doc_filter=%s)", session_id, standalone_query, doc_name)

    # ── 2. Retrieve ────────────────────────────────────────────────────────
    chunks = await retrieve_context(standalone_query, doc_name=doc_name)

    # ── 3. Stream tokens ───────────────────────────────────────────────────
    async for token in stream_answer(standalone_query, chunks):
        payload = TokenEvent(content=token).model_dump()
        yield json.dumps(payload)

    # ── 4. Citation metadata ───────────────────────────────────────────────
    citations = chunks_to_citations(chunks)
    cite_payload = CitationsEvent(sources=citations).model_dump()
    yield json.dumps(cite_payload)

    # ── 5. Completion marker ───────────────────────────────────────────────
    yield "[DONE]"
