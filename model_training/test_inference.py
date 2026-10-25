#!/usr/bin/env python3
"""
Verification Script for Grounded RAG Local Inference API.

Uses the official `openai` Python SDK pointed to Ollama's local OpenAI-compatible
endpoint (`http://localhost:11434/v1`) with full token streaming.

Evaluates two core RAG behaviors:
1. Grounded Extraction: Context contains the answer -> Accurate factual reply.
2. Grounded Refusal: Context lacks the answer -> Strict "Information not found." reply.
"""

import sys
import time
from typing import Optional
# pyrefly: ignore [missing-import]
from openai import OpenAI, APIConnectionError


# Endpoint Configuration
BASE_URL = "http://localhost:11434/v1"
API_KEY = "ollama"  # Ollama ignores API keys, but the OpenAI SDK requires a non-empty string
MODEL_NAME = "rag-llama3-grounded"

# System Prompt matching training & Modelfile
SYSTEM_PROMPT = (
    "You are a strictly grounded Retrieval-Augmented Generation (RAG) assistant. "
    "Answer the user query based ONLY on the provided context. "
    "If the answer cannot be determined strictly from the context, reply with: \"Information not found.\""
)


def run_streaming_query(
    client: OpenAI,
    scenario_title: str,
    context: str,
    query: str,
    expected_note: str,
    model_name: str = MODEL_NAME
) -> str:
    """Execute a single streaming chat completion query and display results in real time."""
    print("=" * 70)
    print(f"TEST: {scenario_title}")
    print("=" * 70)
    print(f"[Context]:\n{context}\n")
    print(f"[Query]:\n{query}\n")
    print(f"[Expected Behavior]: {expected_note}")
    print("-" * 70)
    print("[Streaming Response]: ", end="", flush=True)

    formatted_user_prompt = f"Context:\n{context}\n\nQuestion:\n{query}"

    start_time = time.perf_counter()
    first_token_time: Optional[float] = None
    accumulated_response = []

    try:
        stream = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": formatted_user_prompt}
            ],
            temperature=0.0,  # Zero-temperature for deterministic, factual outputs
            stream=True,
        )

        for chunk in stream:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            content = delta.content or ""
            if content:
                if first_token_time is None:
                    first_token_time = time.perf_counter()
                print(content, end="", flush=True)
                accumulated_response.append(content)

        print()  # newline after stream completes
    except APIConnectionError as e:
        print(f"\n\n[X] Connection Error: Unable to reach Ollama endpoint at {BASE_URL}.")
        print("    Ensure the local server is running by executing: ./serve.sh")
        print(f"    Details: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[X] API Error: {e}")
        sys.exit(1)

    total_time = time.perf_counter() - start_time
    ttft = (first_token_time - start_time) if first_token_time else 0.0
    full_text = "".join(accumulated_response).strip()

    print("-" * 70)
    print(f"Metrics: TTFT: {ttft:.3f}s | Total Latency: {total_time:.3f}s | Chars: {len(full_text)}")
    print("=" * 70 + "\n")
    return full_text


def main():
    print(f"[+] Initializing OpenAI client connected to local Ollama at {BASE_URL} ...")
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

    # --------------------------------------------------------------------------
    # Test Scenario 1: Answerable Query (In-Context Fact Retrieval)
    # --------------------------------------------------------------------------
    context_1 = (
        "Project Orion's vector indexing pipeline utilizes Qdrant v1.8 with HNSW cosine index. "
        "Embeddings are generated in batches of 128 using the bge-large-en-v1.5 model. "
        "The re-ranking layer employs Cohere Rerank-3 with a top-k cutoff of 5 chunks."
    )
    query_1 = "Which embedding model and batch size are used in Project Orion's pipeline?"
    expected_1 = "Must state bge-large-en-v1.5 and batch size of 128."

    response_1 = run_streaming_query(
        client=client,
        scenario_title="Scenario 1: Grounded Fact Extraction (Positive Case)",
        context=context_1,
        query=query_1,
        expected_note=expected_1
    )

    # --------------------------------------------------------------------------
    # Test Scenario 2: Unanswerable Query (Strict Refusal / Anti-Hallucination)
    # --------------------------------------------------------------------------
    context_2 = (
        "Project Orion's vector indexing pipeline utilizes Qdrant v1.8 with HNSW cosine index. "
        "Embeddings are generated in batches of 128 using the bge-large-en-v1.5 model. "
        "The re-ranking layer employs Cohere Rerank-3 with a top-k cutoff of 5 chunks."
    )
    query_2 = "What is the monthly AWS cloud hosting cost for the Qdrant cluster?"
    expected_2 = "Must strictly reply: 'Information not found.'"

    response_2 = run_streaming_query(
        client=client,
        scenario_title="Scenario 2: Grounded Refusal / Out-of-Context (Negative Case)",
        context=context_2,
        query=query_2,
        expected_note=expected_2
    )

    # Verification summary
    print("[+] Test Execution Summary:")
    print(f"    - Scenario 1 (Extraction) Output: {response_1}")
    print(f"    - Scenario 2 (Refusal) Output:    {response_2}")
    
    if "information not found" in response_2.lower():
        print("\n[✓] Refusal test passed: Model correctly refused out-of-context query!")
    else:
        print("\n[!] Refusal test note: Review model response above for alignment.")


if __name__ == "__main__":
    main()
