"""
Core RAG chain for text and tables only.
No vision, no image processing - just reliable answers from text and tables.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging
import json

sys.path.append(str(Path(__file__).parent))

from gemini_client import GeminiClient
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CoreRAG:
    """
    Simple, reliable RAG chain for text and tables.
    No images, no complexity - just accurate answers.
    """
    
    def __init__(self, retriever):
        self.retriever = retriever
        self.llm = GeminiClient()
    
    def query(self, question: str, k: int = 5) -> Dict:
        """
        Process question with full context from top-k chunks.
        """
        # Step 1: Retrieve chunks
        logger.info(f"Retrieving for: {question}")
        results = self.retriever.search(question, k=k)
        
        if not results:
            return {
                "question": question,
                "answer": "No relevant information found.",
                "sources": [],
                "full_context": ""
            }
        
        # Step 2: Combine ALL retrieved chunks into full context
        full_context = self._build_full_context(results)
        
        # Step 3: Show what we're sending (for debugging)
        print(f"\n--- CONTEXT BEING SENT TO GEMINI ({len(full_context)} chars) ---")
        print(full_context[:1500])
        print("--- END OF CONTEXT PREVIEW ---\n")
        
        # Step 4: Generate answer
        prompt = self._build_prompt(question, full_context)
        answer = self.llm.generate(prompt)
        
        # Step 5: Prepare sources
        sources = []
        for result in results[:3]:
            sources.append({
                "type": result.get("type", "text"),
                "similarity": result.get("similarity_score"),
                "content_preview": result.get("content", "")[:200]
            })
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "full_context": full_context[:1000]
        }
    
    def _build_full_context(self, chunks: List[Dict]) -> str:
        """Combine all chunks into a single context string."""
        context_parts = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            chunk_type = chunk.get("type", "text")
            
            # Clean up the content - remove excessive whitespace
            content = ' '.join(content.split())
            
            context_parts.append(f"[Document {i+1} - Type: {chunk_type}]\n{content}\n")
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt for LLM."""
        return f"""You are a financial analyst. Answer the question based ONLY on the context below.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Extract exact numbers from tables
- If the context contains a table, read every row carefully
- Provide the complete answer, not partial or truncated
- If you cannot find the exact answer, say so

ANSWER:"""


def diagnose_chunks(chunks_file: str):
    """
    Diagnostic: Show all chunks to understand what's being retrieved.
    """
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    print(f"\n=== CHUNKS DIAGNOSTIC ===")
    print(f"Total chunks: {len(chunks)}")
    
    # Look for shareholding distribution
    for chunk in chunks:
        content = chunk.get("content", "")
        if "shareholding" in content.lower() or "distribution" in content.lower():
            print(f"\nChunk {chunk['chunk_id']} ({chunk['type']}):")
            print(f"Content preview: {content[:500]}...")
            print("-" * 50)


def test_retrieval_only(question: str, chunks_file: str, store_dir: str = "vector_store"):
    """
    Test only retrieval - see what chunks are found without LLM.
    """
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    results = retriever.search(question, k=5)
    
    print(f"\n=== RETRIEVAL RESULTS for: {question} ===")
    for i, result in enumerate(results):
        print(f"\n{i+1}. Type: {result['type']} (Score: {result['similarity_score']:.3f})")
        content = result.get("content", "")[:500]
        print(f"   Content: {content}")
    
    return results


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python rag_core.py query 'your question' [chunks_file] [store_dir]")
        print("  python rag_core.py diagnose [chunks_file]")
        print("  python rag_core.py retrieve 'your question' [chunks_file] [store_dir]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "diagnose":
        chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
        diagnose_chunks(chunks_file)
    
    elif command == "retrieve":
        question = sys.argv[2]
        chunks_file = sys.argv[3] if len(sys.argv) > 3 else "outputs/sample_digital1_chunks.json"
        store_dir = sys.argv[4] if len(sys.argv) > 4 else "vector_store"
        test_retrieval_only(question, chunks_file, store_dir)
    
    elif command == "query":
        question = sys.argv[2]
        chunks_file = sys.argv[3] if len(sys.argv) > 3 else "outputs/sample_digital1_chunks.json"
        store_dir = sys.argv[4] if len(sys.argv) > 4 else "vector_store"
        
        # Load components
        print("Loading vector store...")
        vector_store = VectorStore()
        vector_store.load(store_dir)
        
        print("Creating retriever...")
        retriever = EnhancedRetriever(vector_store, chunks_file)
        
        print("Initializing Core RAG...")
        rag = CoreRAG(retriever)
        
        print(f"\nQuestion: {question}")
        print("=" * 60)
        
        result = rag.query(question)
        
        print(f"\nANSWER:\n{result['answer']}")
        print(f"\nSOURCES:")
        for i, source in enumerate(result['sources']):
            print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f})")