---
name: RAG Backend Context
description: Context and conventions for working on the FastAPI RAG backend.
---

# RAG Backend Guidelines

When working on the RAG backend in this repository, keep the following in mind:

1. **Environment:**
   - A virtual environment is set up at `/Users/parth/repos/RAG/RAG/.venv`. Always source it or use the python interpreter inside it when running commands or tests.
   - Dependencies are managed in `backend/requirements.txt`.

2. **State of the Code:**
   - The backend is a FastAPI application that uses LangChain to talk to an LLM (currently configured for Ollama).
   - **Crucial:** `backend/mock_services.py` currently holds stubbed versions of the indexing and retrieval logic. These need to be replaced with the real ChromaDB vector search and embedding implementations once they are ready. Do not write business logic assuming these mock services are permanent.
   - Streaming is implemented via Server-Sent Events (SSE) in `backend/streamer.py`.

3. **Running the Server:**
   - The server can be run from the `backend` directory using `uvicorn main:app --reload --port 8000`.
   - A testing script is available at `backend/test_endpoints.sh`.
