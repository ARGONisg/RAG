from sentence_transformers import CrossEncoder

class Reranker:
    def __init__(self, model_name: str | None = None):
        if not model_name:
            try:
                from config import settings
                model_name = settings.reranker_model_name
            except Exception:
                model_name = "cross-encoder/ms-marco-MiniLM-L-6-v2"

        # The CrossEncoder computes a highly accurate similarity score
        # by passing the query and the document simultaneously into the transformer network.
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[dict], top_k: int = 4) -> list[dict]:
        if not candidates:
            return []
            
        # Create (query, text) pairs for the model
        pairs = [[query, c["text_content"]] for c in candidates]
        
        # Predict logits/scores
        scores = self.model.predict(pairs)
        
        # Assign scores and clean up intermediate fusion properties
        for idx, candidate in enumerate(candidates):
            candidate["metadata"]["score"] = float(scores[idx])
            candidate.pop("vec_score", None)
            candidate.pop("bm25_score", None)
            candidate.pop("fused_score", None)
            
        # Sort by cross-encoder score descending
        candidates.sort(key=lambda x: x["metadata"]["score"], reverse=True)
        
        # Return strict top_k as required by contract
        return candidates[:top_k]