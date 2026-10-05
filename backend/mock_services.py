"""
Mock implementations of Member 1's retrieval pipeline.

These stubs let the backend run and be fully tested end-to-end without
the real ChromaDB indexer or embedding model.  Replace each function body
with the real call once Member 1's module is ready.
"""

from __future__ import annotations

import asyncio
import hashlib
import random
from pathlib import Path
from typing import Any

from schemas import CitationSource


# ═══════════════════════════════════════════════════════════════════════════
# Document Indexing  (used by POST /api/v1/documents/upload)
# ═══════════════════════════════════════════════════════════════════════════


async def index_document(filepath: Path) -> int:
    """
    Simulate Member 1's PDF ingestion pipeline.

    In production this would:
      1.  Parse the PDF into pages / text blocks.
      2.  Chunk the text (e.g. RecursiveCharacterTextSplitter).
      3.  Embed and upsert into ChromaDB.

    Returns:
        The number of chunks that were indexed.
    """
    # Fake a short async delay to mimic real I/O work
    await asyncio.sleep(0.3)

    # Deterministic-ish chunk count derived from filename so repeated
    # uploads of the same file return a stable number.
    digest = int(hashlib.md5(filepath.name.encode()).hexdigest(), 16)
    chunks = (digest % 60) + 10  # between 10 and 69
    return chunks


# ═══════════════════════════════════════════════════════════════════════════
# Retrieval  (used by the RAG chain before calling the LLM)
# ═══════════════════════════════════════════════════════════════════════════


# A tiny corpus so the mock returns plausible-looking data.
_MOCK_CHUNKS: list[dict[str, Any]] = [
    {
        "text": (
            "Employees are entitled to 24 days of paid annual leave per calendar year. "
            "Unused leave may be carried over to the next year up to a maximum of 10 days."
        ),
        "source_file": "employee_handbook.pdf",
        "page_number": 14,
    },
    {
        "text": (
            "Sick leave requires a medical certificate if the absence exceeds two "
            "consecutive working days.  Up to 12 days of paid sick leave are granted annually."
        ),
        "source_file": "employee_handbook.pdf",
        "page_number": 15,
    },
    {
        "text": (
            "The company's data-retention policy mandates that all customer PII be "
            "encrypted at rest with AES-256 and purged after 7 years."
        ),
        "source_file": "data_policy_v3.pdf",
        "page_number": 4,
    },
    {
        "text": (
            "Remote work is permitted for up to 3 days per week, subject to manager "
            "approval.  Employees must be available during core hours (10 AM – 4 PM)."
        ),
        "source_file": "remote_work_guidelines.pdf",
        "page_number": 2,
    },
    {
        "text": (
            "Performance reviews are conducted biannually in June and December. "
            "Self-assessments must be submitted two weeks before the review meeting."
        ),
        "source_file": "performance_review_process.pdf",
        "page_number": 7,
    },
]


async def get_relevant_context(
    query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Simulate Member 1's `get_relevant_context(query)`.

    In production this would:
      1.  Embed the *standalone* query.
      2.  Vector-search ChromaDB for the top-k nearest chunks.
      3.  Return each chunk with its text, source metadata, and similarity score.

    Returns:
        A list of dicts, each containing:
            - text (str)
            - source_file (str)
            - page_number (int)
            - score (float)  — cosine similarity in [0, 1]
    """
    await asyncio.sleep(0.15)

    # Pick a random subset of the mock corpus and assign fake scores.
    selected = random.sample(_MOCK_CHUNKS, k=min(top_k, len(_MOCK_CHUNKS)))
    results: list[dict[str, Any]] = []
    for chunk in selected:
        results.append(
            {
                **chunk,
                "score": round(random.uniform(0.55, 0.97), 2),
            }
        )
    # Sort descending by score (most relevant first).
    results.sort(key=lambda c: c["score"], reverse=True)
    return results


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
