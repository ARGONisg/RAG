import chromadb
from chromadb.utils import embedding_functions
import os

class VectorStore:
    def __init__(self, persist_directory: str | None = None):
        if not persist_directory:
            try:
                from config import settings
                persist_directory = settings.chroma_persist_dir
                model_name = settings.embedding_model_name
            except Exception:
                persist_directory = "./chroma_db"
                model_name = "all-MiniLM-L6-v2"
        else:
            model_name = "all-MiniLM-L6-v2"

        os.makedirs(persist_directory, exist_ok=True)
        # Initialize persistent ChromaDB local client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence-transformers embedding model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=model_name
        )
        
        # Get or create our RAG collection
        self.collection = self.client.get_or_create_collection(
            name="rag_docs",
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"} # Use cosine similarity
        )

    def add_chunks(self, chunks: list[dict]):
        if not chunks:
            return
            
        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text_content"] for c in chunks]
        metadatas = [c["metadata"] for c in chunks]
        
        # Upsert automatically handles duplicate chunk IDs
        self.collection.upsert(documents=texts, metadatas=metadatas, ids=ids)

    def search(self, query: str, top_k: int = 10, doc_name: str | None = None) -> dict:
        kwargs: dict = {
            "query_texts": [query],
            "n_results": top_k,
        }
        if doc_name:
            kwargs["where"] = {"source_file": doc_name}
        results = self.collection.query(**kwargs)
        return results