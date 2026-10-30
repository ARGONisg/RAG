"""
Retrieval Bridge — Unified adapter between FastAPI routers and Member 1's retrieval engine.

Resolves sync/async threading, handles schema mapping, and enables seamless toggling
between real indexing (PyMuPDF + ChromaDB + BM25 + CrossEncoder) and mock services.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from config import settings
from schemas import CitationSource

logger = logging.getLogger(__name__)


async def index_document(filepath: Path) -> int:
    """
    Index a PDF document into the hybrid retrieval store (ChromaDB + BM25).
    
    If settings.use_mock_retrieval is True, delegates to mock_services.
    Otherwise, executes retrieval.engine.index_document in a thread pool.
    """
    if settings.use_mock_retrieval:
        from mock_services import index_document as mock_index
        return await mock_index(filepath)

    try:
        from retrieval.engine import index_document as real_index
        
        # Offload synchronous parsing, embedding & indexing to thread pool
        result = await asyncio.to_thread(real_index, str(filepath))
        chunks_indexed = int(result.get("chunks_indexed", 0))
        logger.info(
            "Indexed %s with real pipeline: %d chunks",
            filepath.name,
            chunks_indexed,
        )
        return chunks_indexed
    except Exception as exc:
        logger.exception("Real indexing pipeline failed; falling back to mock")
        from mock_services import index_document as mock_index
        return await mock_index(filepath)


async def get_relevant_context(
    query: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """
    Retrieve top relevant context chunks for a given standalone query.
    
    Adapts the output schema from retrieval.engine to the unified contract:
      - text: str
      - source_file: str
      - page_number: int
      - score: float
    """
    effective_top_k = top_k or settings.top_k_chunks

    if settings.use_mock_retrieval:
        from mock_services import get_relevant_context as mock_get_context
        return await mock_get_context(query, top_k=effective_top_k)

    try:
        from retrieval.engine import get_relevant_context as real_get_context

        # Offload vector search, BM25 & cross-encoder reranking to thread pool
        raw_candidates = await asyncio.to_thread(real_get_context, query, top_k=effective_top_k)
        
        adapted_chunks: list[dict[str, Any]] = []
        for c in raw_candidates:
            metadata = c.get("metadata", {})
            adapted_chunks.append({
                "chunk_id": c.get("chunk_id", ""),
                "text": c.get("text_content", ""),
                "source_file": metadata.get("source_file", "unknown"),
                "page_number": int(metadata.get("page_number", 1)),
                "score": float(metadata.get("score", 0.0)),
            })
            
        logger.info(
            "Retrieved %d candidate chunks from real hybrid retrieval engine",
            len(adapted_chunks),
        )
        return adapted_chunks
    except Exception as exc:
        logger.exception("Real retrieval pipeline failed; falling back to mock")
        from mock_services import get_relevant_context as mock_get_context
        return await mock_get_context(query, top_k=effective_top_k)


def chunks_to_citations(chunks: list[dict[str, Any]]) -> list[CitationSource]:
    """Convert raw retrieval results into the API-contract citation schema."""
    return [
        CitationSource(
            source_file=c["source_file"],
            page_number=c["page_number"],
            score=c["score"],
        )
        for c in chunks
    ]

