import os
import hashlib
from typing import List, Dict

# Local imports
from .parser import extract_text_from_pdf
from .chunker import chunk_text
from .vector_store import VectorStore
from .hybrid import BM25Index
from .reranker import Reranker

# Load singletons globally so models remain in memory across FastAPI requests
vector_store = VectorStore()
bm25_index = BM25Index()
reranker = Reranker()

def _normalize_scores(scores: list[float]) -> list[float]:
    """Min-Max scaler to normalize distances/scores between 0 and 1."""
    if not scores: return []
    min_s, max_s = min(scores), max(scores)
    if max_s - min_s == 0: return [1.0] * len(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]

def index_document(file_path: str) -> dict:
    """
    Parses a PDF, chunks it, and indexes it into both ChromaDB (Dense) and BM25 (Lexical).
    """
    filename = os.path.basename(file_path)
    
    # 1. Parse & Chunk
    pages = extract_text_from_pdf(file_path)
    raw_chunks = chunk_text(pages)
    
    # 2. Format to strict schema
    processed_chunks = []
    for i, c in enumerate(raw_chunks):
        # Generate a unique deterministic hash for the chunk
        doc_hash = hashlib.md5((filename + c["text"]).encode()).hexdigest()
        chunk_id = f"{doc_hash}_{i}"
        
        processed_chunks.append({
            "chunk_id": chunk_id,
            "text_content": c["text"],
            "metadata": {
                "source_file": filename,
                "page_number": c["page_number"]
            }
        })
        
    # 3. Index into storage systems
    vector_store.add_chunks(processed_chunks)
    bm25_index.add_chunks(processed_chunks)
    
    return {
        "status": "success",
        "filename": filename,
        "chunks_indexed": len(processed_chunks)
    }

def get_relevant_context(query: str, top_k: int = 4, doc_name: str | None = None) -> List[Dict]:
    """
    Retrieves candidates using Hybrid Search (Vector + BM25), fuses them, 
    and rescores with a Cross-Encoder.
    Optionally filters by doc_name (source_file) to isolate retrieval to a specific document.
    """
    # 1. Retrieve top-10 candidates from Vector DB (restricted to doc_name if provided)
    vec_results_raw = vector_store.search(query, top_k=10, doc_name=doc_name)
    
    candidate_pool = {}
    
    # 2. Process Vector Results
    if vec_results_raw["ids"] and vec_results_raw["ids"][0]:
        vec_ids = vec_results_raw["ids"][0]
        # Invert cosine distances to represent similarity scores (higher = better)
        vec_dists = vec_results_raw["distances"][0]
        vec_sims = [1.0 / (1.0 + d) for d in vec_dists] 
        norm_vec_scores = _normalize_scores(vec_sims)
        
        for i in range(len(vec_ids)):
            candidate_pool[vec_ids[i]] = {
                "chunk_id": vec_ids[i],
                "text_content": vec_results_raw["documents"][0][i],
                "metadata": vec_results_raw["metadatas"][0][i],
                "vec_score": norm_vec_scores[i],
                "bm25_score": 0.0
            }
            
    # 3. Retrieve and process top-10 from BM25 (restricted to doc_name if provided)
    bm25_results = bm25_index.search(query, top_k=10, doc_name=doc_name)
    bm25_scores = [r["bm25_score"] for r in bm25_results]
    norm_bm25_scores = _normalize_scores(bm25_scores)
    
    for i, r in enumerate(bm25_results):
        cid = r["chunk_id"]
        if cid in candidate_pool:
            candidate_pool[cid]["bm25_score"] = norm_bm25_scores[i]
        else:
            candidate_pool[cid] = {
                "chunk_id": cid,
                "text_content": r["text_content"],
                "metadata": r["metadata"],
                "vec_score": 0.0,
                "bm25_score": norm_bm25_scores[i]
            }
            
    # 4. Fuse Scores (Simple Reciprocal/Linear fusion)
    merged_candidates = list(candidate_pool.values())
    for c in merged_candidates:
        c["fused_score"] = (c["vec_score"] + c["bm25_score"]) / 2.0
        
    # Sort merged pool by fusion score to find the best overall candidates to rerank
    merged_candidates.sort(key=lambda x: x["fused_score"], reverse=True)
    
    # 5. Cross-Encoder Reranking
    final_results = reranker.rerank(query, merged_candidates, top_k=top_k)
    
    return final_results


if __name__ == "__main__":
    import json
    import sys
    
    # Allow running module locally
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    sample_pdf_path = "sample.pdf"
    
    if not os.path.exists(sample_pdf_path):
        print(f"--- [WARNING] ---")
        print(f"Please drop a PDF named '{sample_pdf_path}' in the root directory to test.")
        print(f"Current working dir: {os.getcwd()}")
    else:
        print(f"\n1. Indexing {sample_pdf_path}...")
        indexing_res = index_document(sample_pdf_path)
        print(json.dumps(indexing_res, indent=2))
        
        test_query = "What is this document about?"
        print(f"\n2. Querying Context for: '{test_query}'")
        
        context_res = get_relevant_context(test_query, top_k=3)
        print("\n--- Final Reranked Context Results ---")
        print(json.dumps(context_res, indent=2))