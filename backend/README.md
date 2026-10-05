# RAG Q&A Backend

This is the FastAPI backend for the Intelligent Document Retrieval & Q&A System.

## Architecture

The backend exposes a REST API for document uploads and a Server-Sent Events (SSE) stream for chat interactions.

- **`main.py`**: The FastAPI application entry point. Configures CORS and mounts routers.
- **`config.py`**: Centralized configuration management using `pydantic-settings`. Reads from `.env`.
- **`schemas.py`**: Pydantic models defining the API contracts (requests, responses, SSE events).
- **`chains.py`**: The core RAG logic. Handles query condensing, context injection, and LLM communication using LangChain.
- **`streamer.py`**: Helper for streaming the LLM output as SSE events to the frontend.
- **`mock_services.py`**: Contains mock implementations for document ingestion and retrieval. **This is meant to be replaced when the real indexing/retrieval system (Member 1's work) is integrated.**
- **`routers/documents.py`**: Endpoint for uploading PDFs (`POST /api/v1/documents/upload`).
- **`routers/chat.py`**: Endpoint for querying the LLM with context (`POST /api/v1/chat`).

## Setup & Running

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r backend/requirements.txt
   ```

2. Copy `.env.example` to `.env` in the project root and adjust settings if necessary.

3. Start the server (runs on port 8000 by default):
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

4. Run the smoke tests:
   ```bash
   cd backend
   ./test_endpoints.sh
   ```
