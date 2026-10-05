"""
FastAPI application entry point.

- Mounts the document-upload and chat-streaming routers.
- Configures CORS for the Next.js frontend.
- Adds global exception handling and structured logging.
"""

from __future__ import annotations

import logging
import sys
import traceback

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.responses import JSONResponse

from config import settings
from routers.chat import router as chat_router
from routers.documents import router as documents_router

# ── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# ── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Q&A Backend",
    description=(
        "Intelligent Document Retrieval & Q&A System — exposes PDF upload "
        "and streaming chat endpoints for the Next.js frontend."
    ),
    version="0.1.0",
)

# ── CORS ───────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────

app.include_router(documents_router)
app.include_router(chat_router)

# ── Global Exception Handler ──────────────────────────────────────────────


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all that prevents raw tracebacks from leaking to the client.
    """
    logger.error(
        "Unhandled exception on %s %s:\n%s",
        request.method,
        request.url.path,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again."},
    )


# ── Health Check ───────────────────────────────────────────────────────────


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "healthy"}


# ── Dev server entry point ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
