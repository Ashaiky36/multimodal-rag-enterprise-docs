"""
Complete RAG system using ONLY local Llama models.
No API calls, no Gemini.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging
import ollama
import json

sys.path.append(str(Path(__file__).parent))

from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class LlamaRAG:
    """
    RAG chain using ONLY local Ollama models.
    - Text model: llama3.2:3b for answering questions
    - Vision model: llama3.2-vision:11b for image descriptions (used during ingestion)
    """
    
    def __init__(self, retriever, 
                 text_model: str = "llama3.1:8b-instruct-q3_K_L",
                 vision_model: str = "qwen2.5vl:3b"):
        self.retriever = retriever
        self.text_model = text_model
        self.vision_model = vision_model
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is running and models are available."""
        try:
            models = ollama.list()
            model_names = [m.get('model', '') for m in models.get('models', [])]
            logger.info(f"Available models: {model_names}")
            
            if self.text_model not in model_names:
                logger.warning(f"Text model {self.text_model} not found. Pulling...")
                ollama.pull(self.text_model)
            
            if self.vision_model not in model_names:
                logger.warning(f"Vision model {self.vision_model} not found. Pulling...")
                ollama.pull(self.vision_model)
                
            logger.info(f"✅ Ollama ready. Text: {self.text_model}, Vision: {self.vision_model}")
        except Exception as e:
            logger.error(f"Ollama not running: {e}")
            logger.info("Please start Ollama: ollama serve")
    
    def query(self, question: str, k: int = 5) -> Dict:
        """Process question using local Llama models."""
        
        # Step 1: Retrieve chunks
        logger.info(f"Retrieving for: {question}")
        results = self.retriever.search(question, k=k)
        
        if not results:
            return {
                "question": question,
                "answer": "No relevant information found in the document.",
                "sources": []
            }
        
        # Step 2: Build context
        context = self._build_context(results)
        
        # Step 3: Check if visual question (for debugging)
        is_visual = self._is_visual_question(question)
        logger.info(f"Visual question: {is_visual}")
        
        # Step 4: Generate prompt
        prompt = self._build_prompt(question, context)
        
        # Step 5: Get response from Llama text model
        try:
            logger.info(f"Generating answer with {self.text_model}...")
            response = ollama.generate(
                model=self.text_model,
                prompt=prompt,
                options={
                    "temperature": 0.2,
                    "num_predict": 500
                }
            )
            answer = response['response'].strip()
            logger.info(f"Answer generated ({len(answer)} chars)")
        except Exception as e:
            logger.error(f"Llama generation failed: {e}")
            answer = f"Error: {e}"
        
        # Step 6: Prepare sources
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
            "used_vision": is_visual
        }
    
    def _is_visual_question(self, question: str) -> bool:
        """Detect if question requires chart/image understanding."""
        visual_keywords = [
            "chart", "graph", "plot", "figure", "trajectory",
            "intersect", "line", "trend", "pie", "bar", "visual",
            "performance", "comparison", "broad based indices"
        ]
        return any(kw in question.lower() for kw in visual_keywords)
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context from chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):
            content = chunk.get("content", "")[:1500]
            chunk_type = chunk.get("type", "text")
            context_parts.append(f"[Source {i+1} - Type: {chunk_type}]\n{content}")
        return "\n\n".join(context_parts)

    def _build_prompt(self, question: str, context: str) -> str:
        """Build prompt with better instructions for smaller models."""
        return f"""You are a financial auditor analyzing an annual report.

    CONTEXT:
    {context}

    USER QUESTION:
    {question}

    IMPORTANT INSTRUCTIONS:
    1. READ the context carefully. The user may use different wording than the context (e.g., "Whistle Blower" = "unethical reporting code").
    2. If the context contains HTML tables, READ them as tables - the columns and rows are structured.
    3. If calculations are needed (percentages, differences, growth rates), SHOW your step-by-step math.
    4. If you cannot find the exact answer, say "I cannot find this information in the provided context."
    5. Be precise with numbers - extract them exactly as they appear.

    ANSWER:"""    
    
#     def _build_prompt(self, question: str, context: str) -> str:
#         """Build prompt for Llama."""
#         return f"""You are a financial analyst. Answer the question based ONLY on the context below.

# CONTEXT:
# {context}

# QUESTION: {question}

# INSTRUCTIONS:
# - Extract exact numbers from tables and vision descriptions
# - If you see [VISION DESCRIPTION], treat it as authoritative data
# - Be precise and concise
# - If you cannot find the answer, say so

# ANSWER:"""


def create_llama_rag(chunks_file: str, store_dir: str = "vector_store") -> LlamaRAG:
    """Create a LlamaRAG instance from chunks and vector store."""
    
    logger.info("Loading vector store...")
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    logger.info("Creating retriever...")
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    logger.info("Initializing Llama RAG...")
    rag = LlamaRAG(retriever)
    
    return rag


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python rag_llama.py query 'your question' [chunks_file] [store_dir]")
        print("  python rag_llama.py test [chunks_file] [store_dir]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "query":
        question = sys.argv[2]
        chunks_file = sys.argv[3] if len(sys.argv) > 3 else "processed_docs/984934ca5db0/984934ca5db0_chunks.json"
        store_dir = sys.argv[4] if len(sys.argv) > 4 else "processed_docs/984934ca5db0/vector_store"
        
        rag = create_llama_rag(chunks_file, store_dir)
        
        print(f"\nQuestion: {question}")
        print("=" * 60)
        
        result = rag.query(question)
        
        print(f"\nANSWER:\n{result['answer']}")
        print(f"\nSOURCES:")
        for i, source in enumerate(result['sources']):
            print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f})")
    
    elif command == "test":
        chunks_file = sys.argv[2] if len(sys.argv) > 2 else "processed_docs/984934ca5db0/984934ca5db0_chunks.json"
        store_dir = sys.argv[3] if len(sys.argv) > 3 else "processed_docs/984934ca5db0/vector_store"
        
        rag = create_llama_rag(chunks_file, store_dir)
        
        # Test queries
        test_questions = [
            "What is the shareholding pattern?",
            "Compare AIL vs SENSEX line plot and tell me at what month do they intersect?"
        ]
        
        for q in test_questions:
            print(f"\n{'='*60}")
            print(f"Question: {q}")
            print(f"{'='*60}")
            result = rag.query(q)
            print(f"\nANSWER:\n{result['answer']}")
            print(f"\nSources: {len(result['sources'])}")