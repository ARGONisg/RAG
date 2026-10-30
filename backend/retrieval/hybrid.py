import pickle
import os
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self, index_path: str | None = None):
        if not index_path:
            try:
                from config import settings
                index_path = os.path.join(settings.chroma_persist_dir, "bm25_index.pkl")
            except Exception:
                index_path = "./chroma_db/bm25_index.pkl"

        self.index_path = index_path
        self.corpus = []
        self.bm25 = None
        self.load()

    def load(self):
        """Load existing index from disk if it exists."""
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.corpus = data["corpus"]
                
                # Rebuild BM25 object in memory
                if self.corpus:
                    tokenized_corpus = [c["text_content"].lower().split() for c in self.corpus]
                    self.bm25 = BM25Okapi(tokenized_corpus)

    def save(self):
        """Persist corpus to disk to maintain state between server restarts."""
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"corpus": self.corpus}, f)

    def add_chunks(self, chunks: list[dict]):
        existing_ids = {c["chunk_id"] for c in self.corpus}
        new_chunks = [c for c in chunks if c["chunk_id"] not in existing_ids]
        if new_chunks:
            self.corpus.extend(new_chunks)
            tokenized_corpus = [c["text_content"].lower().split() for c in self.corpus]
            self.bm25 = BM25Okapi(tokenized_corpus)
            self.save()

    def search(self, query: str, top_k: int = 10, doc_name: str | None = None) -> list[dict]:
        if not self.bm25 or not self.corpus:
            return []
            
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get indices sorted by score descending
        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        results = []
        for idx in sorted_indices:
            if scores[idx] <= 0:
                continue
            chunk = self.corpus[idx]
            if doc_name and chunk.get("metadata", {}).get("source_file") != doc_name:
                continue
            results.append({
                "chunk_id": chunk["chunk_id"],
                "text_content": chunk["text_content"],
                "metadata": chunk["metadata"],
                "bm25_score": float(scores[idx])
            })
            if len(results) >= top_k:
                break
        return results