"""
Document upload router — POST /api/v1/documents/upload

Accepts a multipart PDF, persists it to disk, calls Member 1's
indexing pipeline, and returns a summary response.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from config import settings
from mock_services import index_document
from schemas import UploadResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/documents", tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a PDF for indexing",
)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    """
    1. Validate the upload is a PDF.
    2. Save the file to ``UPLOAD_DIR``.
    3. Call the indexing pipeline.
    4. Return chunk count.
    """
    # ── Validate MIME type ─────────────────────────────────────────────────
    if file.content_type not in ("application/pdf",):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Only PDF files are accepted. Received: {file.content_type}",
        )

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    # ── Persist to disk ────────────────────────────────────────────────────
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    dest = upload_dir / file.filename

    try:
        content = await file.read()
        dest.write_bytes(content)
        logger.info("Saved upload: %s (%d bytes)", dest, len(content))
    except Exception as exc:
        logger.exception("Failed to save uploaded file")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File save failed.",
        ) from exc
    finally:
        await file.close()

    # ── Index the document ─────────────────────────────────────────────────
    try:
        chunks_indexed = await index_document(dest)
    except Exception as exc:
        logger.exception("Indexing pipeline failed for %s", dest)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Indexing pipeline encountered an error.",
        ) from exc

    return UploadResponse(
        status="success",
        filename=file.filename,
        chunks_indexed=chunks_indexed,
    )
