"""
RAG chain logic — query condensing, context injection, and guardrails.

This module is the "brain" that sits between the API routers and the LLM.
It decides *what* gets sent to the model and *whether* to call it at all.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from config import settings
from mock_services import get_relevant_context
from schemas import HistoryMessage

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Prompt templates
# ═══════════════════════════════════════════════════════════════════════════

CONDENSE_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a helpful assistant. Given the following chat history and "
                "a follow-up question, rewrite the follow-up question into a clear, "
                "standalone question that captures the full intent without relying on "
                "the chat history for context."
            ),
        ),
        ("human", "Chat history:\n{history}\n\nFollow-up question: {question}"),
    ]
)

QA_SYSTEM_PROMPT = (
    "You are a precise document-grounded Q&A assistant.\n\n"
    "RULES:\n"
    "1. Answer ONLY based on the provided context below.\n"
    "2. If the context does not contain the answer, respond EXACTLY with: "
    "'I'm sorry, the information was not found in the provided documents.'\n"
    "3. Do NOT fabricate, speculate, or use prior knowledge.\n"
    "4. Cite specific sections when possible.\n\n"
    "Context:\n"
    "---\n"
    "{context}\n"
    "---"
)

QA_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", QA_SYSTEM_PROMPT),
        ("human", "{question}"),
    ]
)

FALLBACK_RESPONSE = (
    "I could not find any sufficiently relevant information in the indexed "
    "documents to answer your question. Please try rephrasing, or ensure "
    "the relevant document has been uploaded."
)


# ═══════════════════════════════════════════════════════════════════════════
# LLM factory
# ═══════════════════════════════════════════════════════════════════════════


def _get_llm(*, streaming: bool = False) -> ChatOpenAI:
    """
    Build a ChatOpenAI instance pointing at the local Ollama-compatible API.
    """
    return ChatOpenAI(
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
        model=settings.llm_model_name,
        streaming=streaming,
        temperature=0.1,  # low temp for factual QA
    )


# ═══════════════════════════════════════════════════════════════════════════
# Helper: format history for the condensing prompt
# ═══════════════════════════════════════════════════════════════════════════


def _format_history(history: list[HistoryMessage]) -> str:
    """Render conversation history into a flat string for the condenser."""
    lines: list[str] = []
    for msg in history:
        prefix = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{prefix}: {msg.content}")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# Step 1: Condense follow-up → standalone question
# ═══════════════════════════════════════════════════════════════════════════


async def condense_question(
    query: str,
    history: list[HistoryMessage],
) -> str:
    """
    If there is conversation history, call the LLM to rewrite the follow-up
    query into a self-contained standalone question.  Otherwise return as-is.
    """
    if not history:
        return query

    llm = _get_llm(streaming=False)
    chain = CONDENSE_TEMPLATE | llm

    result = await chain.ainvoke(
        {
            "history": _format_history(history),
            "question": query,
        }
    )
    standalone = result.content.strip()
    logger.info("Condensed query: %r → %r", query, standalone)
    return standalone


# ═══════════════════════════════════════════════════════════════════════════
# Step 2: Retrieve context + apply threshold filter
# ═══════════════════════════════════════════════════════════════════════════


async def retrieve_context(
    standalone_query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """
    Fetch top-k chunks from Member 1's retrieval module and discard any
    that fall below the configured similarity threshold.
    """
    raw_chunks = await get_relevant_context(standalone_query, top_k=top_k)

    threshold = settings.similarity_threshold
    filtered = [c for c in raw_chunks if c["score"] >= threshold]

    logger.info(
        "Retrieval: %d raw chunks → %d above threshold (%.2f)",
        len(raw_chunks),
        len(filtered),
        threshold,
    )
    return filtered


# ═══════════════════════════════════════════════════════════════════════════
# Step 3: Stream LLM answer (or yield fallback)
# ═══════════════════════════════════════════════════════════════════════════


async def stream_answer(
    question: str,
    chunks: list[dict[str, Any]],
) -> AsyncIterator[str]:
    """
    If *chunks* is empty (nothing passed the threshold), yield a single
    fallback message.  Otherwise inject the context into the QA prompt
    and stream the LLM response token-by-token.

    Yields:
        Individual token strings as they arrive from the LLM.
    """
    if not chunks:
        yield FALLBACK_RESPONSE
        return

    # Build a combined context block from the retrieved chunks.
    context_parts: list[str] = []
    for idx, chunk in enumerate(chunks, 1):
        context_parts.append(
            f"[{idx}] (source: {chunk['source_file']}, page {chunk['page_number']})\n"
            f"{chunk['text']}"
        )
    context_block = "\n\n".join(context_parts)

    llm = _get_llm(streaming=True)
    chain = QA_TEMPLATE | llm

    async for event in chain.astream(
        {"context": context_block, "question": question}
    ):
        token = event.content
        if token:
            yield token
