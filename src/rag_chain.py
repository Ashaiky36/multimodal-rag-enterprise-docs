"""
Complete RAG chain with table and image support.
Uses local LLM for response generation.
"""

import subprocess
import json
from typing import List, Dict, Optional
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# class LocalLLM:
#     """
#     Wrapper for Ollama local LLM.
#     """
    
#     def __init__(self, model_name: str = "phi3:3.8b-mini-4k-instruct-q4_K_M"):
#         self.model_name = model_name
#         self._check_ollama()
    
#     def _check_ollama(self):
#         """Check if Ollama is running."""
#         try:
#             result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
#             if result.returncode != 0:
#                 print("Warning: Ollama not running. Start with: ollama serve")
#         except FileNotFoundError:
#             print("Error: Ollama not installed. Install from https://ollama.com")
    
#     def generate(self, prompt: str, max_tokens: int = 500) -> str:
#         """
#         Generate response from LLM.
#         """
#         try:
#             result = subprocess.run(
#                 ["ollama", "run", self.model_name, prompt],
#                 capture_output=True,
#                 text=True,
#                 timeout=60
#             )
            
#             if result.returncode == 0:
#                 return result.stdout.strip()
#             else:
#                 logger.error(f"LLM error: {result.stderr}")
#                 return f"Error generating response: {result.stderr}"
        
#         except subprocess.TimeoutExpired:
#             return "Error: LLM response timed out"
#         except Exception as e:
#             return f"Error: {e}"
class LocalLLM:
    """
    Wrapper for Ollama local LLM - Windows compatible.
    """
    
    def __init__(self, model_name: str = "tinyllama:1.1b"):
        self.model_name = model_name
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is running."""
        try:
            result = subprocess.run(
                ["ollama", "list"], 
                capture_output=True, 
                text=True,
                encoding='utf-8',  # Force UTF-8
                errors='replace'   # Replace unreadable characters
            )
            if result.returncode != 0:
                print("Warning: Ollama not running. Start with: ollama serve")
        except FileNotFoundError:
            print("Error: Ollama not installed. Install from https://ollama.com")
    
    def generate(self, prompt: str, max_tokens: int = 500) -> str:
        """
        Generate response from LLM using REST API instead of subprocess.
        More reliable on Windows.
        """
        import requests
        
        # Use Ollama's REST API instead of command line
        api_url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }
        
        try:
            response = requests.post(api_url, json=payload, timeout=120)
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                # Fallback to subprocess if API fails
                return self._generate_via_subprocess(prompt)
                
        except requests.exceptions.ConnectionError:
            logger.error("Cannot connect to Ollama API. Is Ollama running?")
            return "Error: Ollama server not running. Please start with 'ollama serve'"
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return f"Error: {e}"
    
    def _generate_via_subprocess(self, prompt: str) -> str:
        """
        Fallback: Use subprocess with proper encoding.
        """
        try:
            # Use 'ollama run' with proper encoding
            process = subprocess.Popen(
                ["ollama", "run", self.model_name],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
            
            stdout, stderr = process.communicate(input=prompt, timeout=60)
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                return f"Error: {stderr}"
                
        except subprocess.TimeoutExpired:
            process.kill()
            return "Error: LLM response timed out"
        except Exception as e:
            return f"Error: {e}"

class RAGChain:
    """
    Complete RAG chain: retrieve -> enhance -> generate.
    """
    
    def __init__(self, retriever, llm: Optional[LocalLLM] = None):
        self.retriever = retriever
        self.llm = llm or LocalLLM()


    def query(self, question: str, k: int = 3, max_context_tokens: int = 800) -> Dict:
        """
        Process a question with optimized context size for speed.
        """
        # Step 1: Retrieve fewer chunks (k=3 instead of 5)
        logger.info(f"Retrieving for: {question}")
        results = self.retriever.search(question, k=k)
        
        if not results:
            return {
                "question": question,
                "answer": "No relevant information found in the document.",
                "sources": [],
                "context_preview": ""
            }
        
        # Step 2: Build smaller context
        context = self._build_context(results, max_context_tokens)
        
        # Step 3: Generate prompt (shorter)
        prompt = self._build_prompt(question, context)
        
        # Step 4: Get LLM response with timeout
        logger.info("Generating response...")
        answer = self.llm.generate(prompt, max_tokens=300)  # Limit response length
        
        # Step 5: Prepare sources
        sources = []
        for result in results[:3]:
            sources.append({
                "type": result.get("type", "text"),
                "page": result.get("page_num"),
                "similarity": result.get("similarity_score"),
                "content_preview": result.get("content", "")[:200]
            })
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "context_preview": context[:500]
        }     
    
    # def query(self, question: str, k: int = 5, max_context_tokens: int = 2000) -> Dict:
    #     """
    #     Process a question through the RAG chain.
        
    #     Returns:
    #         Dictionary with answer, sources, and context
    #     """
    #     # Step 1: Retrieve relevant chunks
    #     logger.info(f"Retrieving for: {question}")
    #     results = self.retriever.search(question, k=k)
        
    #     # Step 2: Build context from results
    #     context = self._build_context(results, max_context_tokens)
        
    #     # Step 3: Generate prompt
    #     prompt = self._build_prompt(question, context)
        
    #     # Step 4: Get LLM response
    #     logger.info("Generating response...")
    #     answer = self.llm.generate(prompt)
        
    #     # Step 5: Prepare sources
    #     sources = []
    #     for result in results[:3]:  # Top 3 sources
    #         sources.append({
    #             "type": result.get("type", "text"),
    #             "page": result.get("page_num"),
    #             "similarity": result.get("similarity_score"),
    #             "content_preview": result.get("content", "")[:200]
    #         })
        
    #     return {
    #         "question": question,
    #         "answer": answer,
    #         "sources": sources,
    #         "context_preview": context[:500]
    #     }
    
    def _build_context(self, results: List[Dict], max_tokens: int) -> str:
        """
        Build context string from retrieved results.
        """
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results):
            # Use formatted content for tables, plain content for text
            content = result.get("formatted_content", result.get("content", ""))
            chunk_type = result.get("type", "text")
            page = result.get("page_num", "?")
            
            part = f"\n[Document {i+1} - Type: {chunk_type}, Page: {page}]\n{content}\n"
            
            # Rough token estimate (4 chars per token)
            if current_length + len(part) > max_tokens * 4:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """
        Build prompt for LLM with context and instruction.
        """
        return f"""You are a helpful assistant answering questions about a company's annual report.

Use ONLY the following context to answer the question. Do not use any external knowledge.

CONTEXT(includes text and table data from the document):
{context}

QUESTION: {question}

INSTRUCTIONS:
- If the context contains tables, interpret their structure and content.
- Table column headers indicate what the table represents. For example:
  * Columns like "Shareholder Name", "% Holding" indicate a shareholding pattern table
  * Columns like "Revenue", "2022", "2023" indicate financial performance
- Provide specific numbers from tables when answering quantitative questions.
- If you cannot find the answer, say so clearly.

ANSWER:"""


def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
    """
    Quick test function for RAG chain.
    """
    import sys
    sys.path.append('src')
    
    from vector_store import VectorStore
    from enhanced_retriever import EnhancedRetriever
    
    # Load components
    print("Loading vector store...")
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    print("Creating retriever...")
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    print("Initializing RAG chain...")
    rag = RAGChain(retriever)
    
    # Process question
    print(f"\nQuestion: {question}")
    print("-" * 50)
    
    result = rag.query(question)
    
    print(f"\nANSWER:\n{result['answer']}")
    print(f"\nSOURCES:")
    for i, source in enumerate(result['sources']):
        print(f"  {i+1}. {source['type']} (page {source['page']}, similarity: {source['similarity']:.3f})")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        question = sys.argv[1]
        chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
        store_dir = sys.argv[3] if len(sys.argv) > 3 else "vector_store"
        
        test_rag(question, chunks_file, store_dir)
    else:
        print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir]")
        print("\nExample: python rag_chain.py 'what are the terms of reference of the risk management committee?'")