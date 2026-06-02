"""
Vector database module using FAISS and sentence-transformers.
Stores document chunks as embeddings for semantic search.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VectorStore:
    """
    FAISS-based vector store for document chunks.
    Uses lightweight all-MiniLM-L6-v2 model (80MB).
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", index_path: Optional[str] = None):
        """
        Initialize vector store with embedding model.
        
        Args:
            model_name: Sentence transformer model (lightweight for CPU)
            index_path: Path to load existing index from
        """
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        
        if index_path and Path(index_path).exists():
            self.load(index_path)
        else:
            self.index = faiss.IndexFlatL2(self.dimension)
            self.chunks = []  # Store chunk metadata
            self.next_id = 0
        
        logger.info(f"Vector store ready. Dimension: {self.dimension}, Current chunks: {len(self.chunks)}")
    
    # def add_chunks(self, chunks: List[Dict]) -> int:
    #     """
    #     Add chunks to vector store.
        
    #     Args:
    #         chunks: List of chunk dictionaries with 'content' field
        
    #     Returns:
    #         Number of chunks added
    #     """
    #     if not chunks:
    #         return 0
        
    #     # Extract text content for embedding
    #     texts = [chunk["content"] for chunk in chunks]
        
    #     # Generate embeddings in batches (memory efficient)
    #     logger.info(f"Generating embeddings for {len(texts)} chunks...")
    #     embeddings = []
    #     batch_size = 32
        
    #     for i in range(0, len(texts), batch_size):
    #         batch = texts[i:i+batch_size]
    #         batch_embeddings = self.model.encode(batch, show_progress_bar=False)
    #         embeddings.append(batch_embeddings)
        
    #     embeddings = np.vstack(embeddings).astype('float32')
        
    #     # Add to FAISS index
    #     self.index.add(embeddings)
        
    #     # Store chunk metadata
    #     for chunk in chunks:
    #         chunk["id"] = self.next_id
    #         self.chunks.append(chunk)
    #         self.next_id += 1
        
    #     logger.info(f"Added {len(chunks)} chunks. Total chunks: {len(self.chunks)}")
    #     return len(chunks)
    def add_chunks(self, chunks: List[Dict]) -> int:
        """Add chunks with smaller batch size for 8GB RAM."""
        if not chunks:
            return 0
        
        texts = [chunk["content"] for chunk in chunks]
        
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = []
        batch_size = 16  # Reduced from 32 to lower RAM usage
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_embeddings = self.model.encode(batch, show_progress_bar=False)
            embeddings.append(batch_embeddings)
        
        embeddings = np.vstack(embeddings).astype('float32')
        self.index.add(embeddings)
        
        for chunk in chunks:
            chunk["id"] = self.next_id
            self.chunks.append(chunk)
            self.next_id += 1
        
        logger.info(f"Added {len(chunks)} chunks. Total chunks: {len(self.chunks)}")
        return len(chunks)
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search for similar chunks.
        
        Args:
            query: Search query
            k: Number of results to return
        
        Returns:
            List of chunks with similarity scores
        """
        if len(self.chunks) == 0:
            logger.warning("No chunks in vector store")
            return []
        
        # Encode query
        query_embedding = self.model.encode([query])[0].astype('float32').reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding, min(k, len(self.chunks)))
        
        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.chunks):
                chunk = self.chunks[idx].copy()
                chunk["similarity_score"] = float(1.0 / (1.0 + distances[0][i]))  # Convert to similarity
                results.append(chunk)
        
        return results
    
    def save(self, path: str) -> None:
        """
        Save vector store to disk.
        """
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_path = save_path / "faiss.index"
        faiss.write_index(self.index, str(index_path))
        
        # Save chunks metadata
        chunks_path = save_path / "chunks.pkl"
        with open(chunks_path, 'wb') as f:
            pickle.dump({
                'chunks': self.chunks,
                'next_id': self.next_id,
                'dimension': self.dimension
            }, f)
        
        logger.info(f"Vector store saved to {path}")
    
    def load(self, path: str) -> None:
        """
        Load vector store from disk.
        """
        load_path = Path(path)
        
        # Load FAISS index
        index_path = load_path / "faiss.index"
        self.index = faiss.read_index(str(index_path))
        
        # Load chunks metadata
        chunks_path = load_path / "chunks.pkl"
        with open(chunks_path, 'rb') as f:
            data = pickle.load(f)
            self.chunks = data['chunks']
            self.next_id = data['next_id']
            self.dimension = data['dimension']
        
        logger.info(f"Loaded vector store from {path} with {len(self.chunks)} chunks")
    
    def get_stats(self) -> Dict:
        """
        Get vector store statistics.
        """
        chunk_types = {}
        for chunk in self.chunks:
            chunk_type = chunk.get('type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        return {
            "total_chunks": len(self.chunks),
            "chunk_types": chunk_types,
            "dimension": self.dimension,
            "index_size": self.index.ntotal
        }


def load_chunks_from_json(json_path: str) -> List[Dict]:
    """
    Load chunks from JSON file created by mineru_parser.
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    logger.info(f"Loaded {len(chunks)} chunks from {json_path}")
    return chunks


def build_vector_store_from_chunks(chunks_path: str, store_path: str = "vector_store") -> VectorStore:
    """
    Build vector store from chunks JSON file.
    """
    # Load chunks
    chunks = load_chunks_from_json(chunks_path)
    
    # Create vector store
    vector_store = VectorStore()
    
    # Add chunks
    vector_store.add_chunks(chunks)
    
    # Save
    vector_store.save(store_path)
    
    # Print stats
    stats = vector_store.get_stats()
    logger.info(f"Vector store built: {stats}")
    
    return vector_store


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        chunks_file = sys.argv[1]
        store_dir = sys.argv[2] if len(sys.argv) > 2 else "vector_store"
        
        print(f"Building vector store from: {chunks_file}")
        
        vector_store = build_vector_store_from_chunks(chunks_file, store_dir)
        
        # Test search
        print("\n===== TEST SEARCH =====")
        test_query = input("Enter test query (or press Enter to skip): ").strip()
        
        if test_query:
            results = vector_store.search(test_query, k=3)
            print(f"\nSearch results for: '{test_query}'")
            for i, result in enumerate(results):
                print(f"\n{i+1}. Type: {result['type']} (Score: {result['similarity_score']:.3f})")
                print(f"   Content: {result['content'][:200]}...")
                if result.get('page_num'):
                    print(f"   Page: {result['page_num']}")
    else:
        print("Usage: python vector_store.py <chunks_json_path> [store_dir]")