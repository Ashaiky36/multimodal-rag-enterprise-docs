"""
Hybrid retriever combining Dense (FAISS) and Sparse (BM25) search.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional
import logging
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import jieba  # For Chinese tokenization (optional)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines dense vector search with BM25 keyword search.
    """
    
    def __init__(self, vector_store, chunks_file: str, 
                 dense_weight: float = 0.5, sparse_weight: float = 0.5):
        """
        Args:
            vector_store: FAISS vector store
            chunks_file: Path to chunks JSON
            dense_weight: Weight for dense search (0-1)
            sparse_weight: Weight for BM25 search (0-1)
        """
        self.vector_store = vector_store
        self.dense_weight = dense_weight
        self.sparse_weight = sparse_weight
        
        # Load chunks
        with open(chunks_file, 'r', encoding='utf-8') as f:
            self.chunks = json.load(f)
        
        # Build BM25 index
        self._build_bm25_index()
        
        # Embedding model for query encoding
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        logger.info(f"HybridRetriever initialized: {len(self.chunks)} chunks")
        logger.info(f"Weights: Dense={dense_weight}, Sparse={sparse_weight}")
    
    def _build_bm25_index(self):
        """Build BM25 index from chunks."""
        # Tokenize chunk contents
        tokenized_corpus = []
        for chunk in self.chunks:
            content = chunk.get("content", "")
            tokens = self._tokenize(content)
            tokenized_corpus.append(tokens)
        
        self.bm25 = BM25Okapi(tokenized_corpus)
        logger.info(f"BM25 index built with {len(tokenized_corpus)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text for BM25.
        Handles both English and Chinese (via jieba if available).
        """
        # Lowercase
        text = text.lower()
        
        # Simple tokenization (split on non-alphanumeric)
        tokens = []
        import re
        for token in re.findall(r'[a-z0-9]+', text):
            tokens.append(token)
        
        # Add Chinese tokenization if available
        try:
            import jieba
            chinese_tokens = jieba.cut(text)
            tokens.extend([t for t in chinese_tokens if len(t) > 1])
        except ImportError:
            pass
        
        return tokens
    
    def search(self, query: str, k: int = 10) -> List[Dict]:
        """
        Perform hybrid search.
        
        Returns:
            List of chunks with combined scores
        """
        # Dense search
        query_embedding = self.embedding_model.encode([query])[0].astype('float32')
        dense_results = self.vector_store.search(query_embedding, k=k * 2)
        
        # BM25 search
        query_tokens = self._tokenize(query)
        bm25_scores = self.bm25.get_scores(query_tokens)
        
        # Combine scores
        combined_scores = {}
        
        # Dense scores (normalized)
        if dense_results:
            max_dense = max(r.get('similarity_score', 0) for r in dense_results)
            for result in dense_results:
                chunk_id = result.get('chunk_id')
                if chunk_id is not None:
                    dense_score = result.get('similarity_score', 0) / max_dense if max_dense > 0 else 0
                    combined_scores[chunk_id] = {
                        'dense': dense_score,
                        'bm25': 0,
                        'data': result
                    }
        
        # BM25 scores (normalized)
        max_bm25 = max(bm25_scores) if bm25_scores.size > 0 and max(bm25_scores) > 0 else 1
        for i, score in enumerate(bm25_scores):
            if i < len(self.chunks):
                chunk_id = self.chunks[i].get('chunk_id', i)
                if chunk_id not in combined_scores:
                    combined_scores[chunk_id] = {
                        'dense': 0,
                        'bm25': 0,
                        'data': self.chunks[i]
                    }
                combined_scores[chunk_id]['bm25'] = score / max_bm25 if max_bm25 > 0 else 0
        
        # Compute final scores
        for chunk_id, scores in combined_scores.items():
            scores['final'] = (self.dense_weight * scores['dense'] + 
                              self.sparse_weight * scores['bm25'])
        
        # Sort by final score
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['final'],
            reverse=True
        )[:k]
        
        # Return formatted results
        results = []
        for item in sorted_results:
            data = item['data'].copy()
            data['similarity_score'] = item['final']
            data['dense_score'] = item['dense']
            data['bm25_score'] = item['bm25']
            results.append(data)
        
        return results


if __name__ == "__main__":
    import sys
    from vector_store import VectorStore
    
    sys.path.append("src")
    
    chunks_file = "processed_docs/sample2/sample2_chunks_final.json"
    store_dir = "processed_docs/sample2/vector_store_final"
    
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    retriever = HybridRetriever(vector_store, chunks_file)
    
    test_query = "What is the Standalone Net Profit for 2022-23?"
    results = retriever.search(test_query, k=5)
    
    print(f"\nResults for: {test_query}")
    for i, r in enumerate(results):
        print(f"{i+1}. Score: {r['similarity_score']:.3f} (Dense: {r.get('dense_score', 0):.3f}, BM25: {r.get('bm25_score', 0):.3f})")
        preview = r.get('content', '').replace('\n', ' ')[:200]
        print(f"   Preview: {preview}...")