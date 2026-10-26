import chromadb
from chromadb.utils import embedding_functions
import os

class VectorStore:
    def __init__(self, persist_directory: str = "./chroma_db"):
        os.makedirs(persist_directory, exist_ok=True)
        # Initialize persistent ChromaDB local client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use sentence-transformers embedding model
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
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

    def search(self, query: str, top_k: int = 10) -> dict:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        return results