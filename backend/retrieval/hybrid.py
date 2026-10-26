import pickle
import os
from rank_bm25 import BM25Okapi

class BM25Index:
    def __init__(self, index_path: str = "./chroma_db/bm25_index.pkl"):
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
        self.corpus.extend(chunks)
        tokenized_corpus = [c["text_content"].lower().split() for c in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.save()

    def search(self, query: str, top_k: int = 10) -> list[dict]:
        if not self.bm25 or not self.corpus:
            return []
            
        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get indices of top k scores
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    "chunk_id": self.corpus[idx]["chunk_id"],
                    "text_content": self.corpus[idx]["text_content"],
                    "metadata": self.corpus[idx]["metadata"],
                    "bm25_score": float(scores[idx])
                })
        return results