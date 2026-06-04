# # """
# # Complete RAG chain with table and image support.
# # Uses local LLM for response generation.
# # """

# # import subprocess
# # import json
# # from typing import List, Dict, Optional
# # import logging
# # from pathlib import Path

# # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # logger = logging.getLogger(__name__)


# # # class LocalLLM:
# # #     """
# # #     Wrapper for Ollama local LLM.
# # #     """
    
# # #     def __init__(self, model_name: str = "phi3:3.8b-mini-4k-instruct-q4_K_M"):
# # #         self.model_name = model_name
# # #         self._check_ollama()
    
# # #     def _check_ollama(self):
# # #         """Check if Ollama is running."""
# # #         try:
# # #             result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
# # #             if result.returncode != 0:
# # #                 print("Warning: Ollama not running. Start with: ollama serve")
# # #         except FileNotFoundError:
# # #             print("Error: Ollama not installed. Install from https://ollama.com")
    
# # #     def generate(self, prompt: str, max_tokens: int = 500) -> str:
# # #         """
# # #         Generate response from LLM.
# # #         """
# # #         try:
# # #             result = subprocess.run(
# # #                 ["ollama", "run", self.model_name, prompt],
# # #                 capture_output=True,
# # #                 text=True,
# # #                 timeout=60
# # #             )
            
# # #             if result.returncode == 0:
# # #                 return result.stdout.strip()
# # #             else:
# # #                 logger.error(f"LLM error: {result.stderr}")
# # #                 return f"Error generating response: {result.stderr}"
        
# # #         except subprocess.TimeoutExpired:
# # #             return "Error: LLM response timed out"
# # #         except Exception as e:
# # #             return f"Error: {e}"
# # class LocalLLM:
# #     """
# #     Wrapper for Ollama local LLM - Windows compatible.
# #     """
    
# #     def __init__(self, model_name: str = "phi3:3.8b-mini-4k-instruct-q4_K_M"):
# #         self.model_name = model_name
# #         self._check_ollama()
    
# #     def _check_ollama(self):
# #         """Check if Ollama is running."""
# #         try:
# #             result = subprocess.run(
# #                 ["ollama", "list"], 
# #                 capture_output=True, 
# #                 text=True,
# #                 encoding='utf-8',  # Force UTF-8
# #                 errors='replace'   # Replace unreadable characters
# #             )
# #             if result.returncode != 0:
# #                 print("Warning: Ollama not running. Start with: ollama serve")
# #         except FileNotFoundError:
# #             print("Error: Ollama not installed. Install from https://ollama.com")
    
# #     def generate(self, prompt: str, max_tokens: int = 500) -> str:
# #         """
# #         Generate response from LLM using REST API instead of subprocess.
# #         More reliable on Windows.
# #         """
# #         import requests
        
# #         # Use Ollama's REST API instead of command line
# #         api_url = "http://localhost:11434/api/generate"
        
# #         payload = {
# #             "model": self.model_name,
# #             "prompt": prompt,
# #             "stream": False,
# #             "options": {
# #                 "num_predict": max_tokens,
# #                 "temperature": 0.7
# #             }
# #         }
        
# #         try:
# #             response = requests.post(api_url, json=payload, timeout=120)
            
# #             if response.status_code == 200:
# #                 result = response.json()
# #                 return result.get("response", "No response generated")
# #             else:
# #                 # Fallback to subprocess if API fails
# #                 return self._generate_via_subprocess(prompt)
                
# #         except requests.exceptions.ConnectionError:
# #             logger.error("Cannot connect to Ollama API. Is Ollama running?")
# #             return "Error: Ollama server not running. Please start with 'ollama serve'"
# #         except Exception as e:
# #             logger.error(f"LLM API error: {e}")
# #             return f"Error: {e}"
    
# #     def _generate_via_subprocess(self, prompt: str) -> str:
# #         """
# #         Fallback: Use subprocess with proper encoding.
# #         """
# #         try:
# #             # Use 'ollama run' with proper encoding
# #             process = subprocess.Popen(
# #                 ["ollama", "run", self.model_name],
# #                 stdin=subprocess.PIPE,
# #                 stdout=subprocess.PIPE,
# #                 stderr=subprocess.PIPE,
# #                 text=True,
# #                 encoding='utf-8',
# #                 errors='replace'
# #             )
            
# #             stdout, stderr = process.communicate(input=prompt, timeout=60)
            
# #             if process.returncode == 0:
# #                 return stdout.strip()
# #             else:
# #                 return f"Error: {stderr}"
                
# #         except subprocess.TimeoutExpired:
# #             process.kill()
# #             return "Error: LLM response timed out"
# #         except Exception as e:
# #             return f"Error: {e}"

# # class RAGChain:
# #     """
# #     Complete RAG chain: retrieve -> enhance -> generate.
# #     """
    
# #     def __init__(self, retriever, llm: Optional[LocalLLM] = None):
# #         self.retriever = retriever
# #         self.llm = llm or LocalLLM()


# #     def query(self, question: str, k: int = 3, max_context_tokens: int = 800) -> Dict:
# #         """
# #         Process a question with optimized context size for speed.
# #         """
# #         # Step 1: Retrieve fewer chunks (k=3 instead of 5)
# #         logger.info(f"Retrieving for: {question}")
# #         results = self.retriever.search(question, k=k)
        
# #         if not results:
# #             return {
# #                 "question": question,
# #                 "answer": "No relevant information found in the document.",
# #                 "sources": [],
# #                 "context_preview": ""
# #             }
        
# #         # Step 2: Build smaller context
# #         context = self._build_context(results, max_context_tokens)
        
# #         # Step 3: Generate prompt (shorter)
# #         prompt = self._build_prompt(question, context)
        
# #         # Step 4: Get LLM response with timeout
# #         logger.info("Generating response...")
# #         answer = self.llm.generate(prompt, max_tokens=300)  # Limit response length
        
# #         # Step 5: Prepare sources
# #         sources = []
# #         for result in results[:3]:
# #             sources.append({
# #                 "type": result.get("type", "text"),
# #                 "page": result.get("page_num"),
# #                 "similarity": result.get("similarity_score"),
# #                 "content_preview": result.get("content", "")[:200]
# #             })
        
# #         return {
# #             "question": question,
# #             "answer": answer,
# #             "sources": sources,
# #             "context_preview": context[:500]
# #         }     
    
# #     # def query(self, question: str, k: int = 5, max_context_tokens: int = 2000) -> Dict:
# #     #     """
# #     #     Process a question through the RAG chain.
        
# #     #     Returns:
# #     #         Dictionary with answer, sources, and context
# #     #     """
# #     #     # Step 1: Retrieve relevant chunks
# #     #     logger.info(f"Retrieving for: {question}")
# #     #     results = self.retriever.search(question, k=k)
        
# #     #     # Step 2: Build context from results
# #     #     context = self._build_context(results, max_context_tokens)
        
# #     #     # Step 3: Generate prompt
# #     #     prompt = self._build_prompt(question, context)
        
# #     #     # Step 4: Get LLM response
# #     #     logger.info("Generating response...")
# #     #     answer = self.llm.generate(prompt)
        
# #     #     # Step 5: Prepare sources
# #     #     sources = []
# #     #     for result in results[:3]:  # Top 3 sources
# #     #         sources.append({
# #     #             "type": result.get("type", "text"),
# #     #             "page": result.get("page_num"),
# #     #             "similarity": result.get("similarity_score"),
# #     #             "content_preview": result.get("content", "")[:200]
# #     #         })
        
# #     #     return {
# #     #         "question": question,
# #     #         "answer": answer,
# #     #         "sources": sources,
# #     #         "context_preview": context[:500]
# #     #     }
    
# #     def _build_context(self, results: List[Dict], max_tokens: int) -> str:
# #         """
# #         Build context string from retrieved results.
# #         """
# #         context_parts = []
# #         current_length = 0
        
# #         for i, result in enumerate(results):
# #             # Use formatted content for tables, plain content for text
# #             content = result.get("formatted_content", result.get("content", ""))
# #             chunk_type = result.get("type", "text")
# #             page = result.get("page_num", "?")
            
# #             part = f"\n[Document {i+1} - Type: {chunk_type}, Page: {page}]\n{content}\n"
            
# #             # Rough token estimate (4 chars per token)
# #             if current_length + len(part) > max_tokens * 4:
# #                 break
            
# #             context_parts.append(part)
# #             current_length += len(part)
        
# #         return "\n".join(context_parts)
    
# #     def _build_prompt(self, question: str, context: str) -> str:
# #         """
# #         Build prompt for LLM with context and instruction.
# #         """
# #         return f"""You are a helpful assistant answering questions about a company's annual report.

# # Use ONLY the following context to answer the question. Do not use any external knowledge.

# # CONTEXT(includes text and table data from the document):
# # {context}

# # QUESTION: {question}

# # INSTRUCTIONS:
# # - If the context contains tables, interpret their structure and content.
# # - Table column headers indicate what the table represents. For example:
# #   * Columns like "Shareholder Name", "% Holding" indicate a shareholding pattern table
# #   * Columns like "Revenue", "2022", "2023" indicate financial performance
# # - Provide specific numbers from tables when answering quantitative questions.
# # - If you cannot find the answer, say so clearly.

# # ANSWER:"""


# # def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
# #     """
# #     Quick test function for RAG chain.
# #     """
# #     import sys
# #     sys.path.append('src')
    
# #     from vector_store import VectorStore
# #     from enhanced_retriever import EnhancedRetriever
    
# #     # Load components
# #     print("Loading vector store...")
# #     vector_store = VectorStore()
# #     vector_store.load(store_dir)
    
# #     print("Creating retriever...")
# #     retriever = EnhancedRetriever(vector_store, chunks_file)
    
# #     print("Initializing RAG chain...")
# #     rag = RAGChain(retriever)
    
# #     # Process question
# #     print(f"\nQuestion: {question}")
# #     print("-" * 50)
    
# #     result = rag.query(question)
    
# #     print(f"\nANSWER:\n{result['answer']}")
# #     print(f"\nSOURCES:")
# #     for i, source in enumerate(result['sources']):
# #         print(f"  {i+1}. {source['type']} (page {source['page']}, similarity: {source['similarity']:.3f})")
    
# #     return result


# # if __name__ == "__main__":
# #     import sys
    
# #     if len(sys.argv) > 1:
# #         question = sys.argv[1]
# #         chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
# #         store_dir = sys.argv[3] if len(sys.argv) > 3 else "vector_store"
        
# #         test_rag(question, chunks_file, store_dir)
# #     else:
# #         print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir]")
# #         print("\nExample: python rag_chain.py 'what are the terms of reference of the risk management committee?'")

# """
# RAG chain using Gemini API for fast, accurate responses.
# """

# import sys
# from typing import List, Dict, Optional
# import logging
# from pathlib import Path

# sys.path.append(str(Path(__file__).parent))
# from gemini_client import GeminiClient
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class RAGChain:
#     """
#     RAG chain using Gemini API.
#     Fast, accurate, no local RAM usage.
#     """
    
#     def __init__(self, retriever, api_key: Optional[str] = None):
#         self.retriever = retriever
#         self.llm = GeminiClient(api_key=api_key)
    
#     # def query(self, question: str, k: int = 5) -> Dict:
#     #     """
#     #     Process a question through the RAG chain.
#     #     """
#     #     # Step 1: Retrieve relevant chunks
#     #     logger.info(f"Retrieving for: {question}")
#     #     results = self.retriever.search(question, k=k)
        
#     #     if not results:
#     #         return {
#     #             "question": question,
#     #             "answer": "No relevant information found in the document.",
#     #             "sources": [],
#     #             "context_preview": ""
#     #         }
        
#     #     # Step 2: Generate answer with Gemini
#     #     logger.info("Generating response with Gemini...")
#     #     answer = self.llm.generate_with_tables_and_chunks(question, results)
        
#     #     # Step 3: Prepare sources
#     #     sources = []
#     #     for result in results[:3]:
#     #         sources.append({
#     #             "type": result.get("type", "text"),
#     #             "page": result.get("page_num"),
#     #             "similarity": result.get("similarity_score"),
#     #             "content_preview": result.get("content", "")[:200]
#     #         })
        
#     #     return {
#     #         "question": question,
#     #         "answer": answer,
#     #         "sources": sources,
#     #         "context_preview": self._preview_context(results)
#     #     }
#     def query(self, question: str, k: int = 5) -> Dict:
#         """
#         Process a question through the RAG chain.
#         Automatically handles images with vision model.
#         """
#         # Step 1: Retrieve relevant chunks
#         logger.info(f"Retrieving for: {question}")
#         results = self.retriever.search(question, k=k)
        
#         if not results:
#             return {
#                 "question": question,
#                 "answer": "No relevant information found.",
#                 "sources": [],
#                 "context_preview": ""
#             }
        
#         # Step 2: Check if any image chunk is highly relevant
#         image_results = [r for r in results if r.get("type") == "image" and r.get("similarity_score", 0) > 0.5]
        
#         if image_results and self._is_visual_question(question):
#             # Use vision for chart questions
#             logger.info("Detected visual question, using vision model...")
#             best_image = image_results[0]
#             image_path = best_image.get("image_path")
            
#             if image_path and Path(image_path).exists():
#                 # Build prompt for vision
#                 vision_prompt = self._build_vision_prompt(question, results)
#                 answer = self.llm.generate_with_image(vision_prompt, image_path)
#             else:
#                 answer = self.llm.generate_with_tables_and_chunks(question, results)
#         else:
#             # Use text-only for normal questions
#             answer = self.llm.generate_with_tables_and_chunks(question, results)
        
#         # Step 3: Prepare sources
#         sources = []
#         for result in results[:3]:
#             sources.append({
#                 "type": result.get("type", "text"),
#                 "page": result.get("page_num"),
#                 "similarity": result.get("similarity_score"),
#                 "content_preview": result.get("content", "")[:200],
#                 "image_path": result.get("image_path") if result.get("type") == "image" else None
#             })
        
#         return {
#             "question": question,
#             "answer": answer,
#             "sources": sources,
#             "used_vision": len(image_results) > 0 and self._is_visual_question(question)
#         }


#     def _is_visual_question(self, question: str) -> bool:
#         """
#         Detect if a question requires understanding a chart/graph.
#         """
#         visual_keywords = [
#             "chart", "graph", "plot", "figure", "trend", "increase", "decrease",
#             "rise", "fall", "peak", "decline", "growth", "visual", "diagram",
#             "shows", "illustrates", "depicts", "bar", "line", "pie"
#         ]
        
#         question_lower = question.lower()
#         return any(keyword in question_lower for keyword in visual_keywords)
    
#     def _preview_context(self, results: List[Dict]) -> str:
#         """Preview the context sent to the LLM."""
#         preview_parts = []
#         for r in results[:2]:
#             preview_parts.append(r.get("content", "")[:200])
#         return "\n...\n".join(preview_parts)


# def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
#     """Test the RAG chain."""
    
#     # Load components
#     print("Loading vector store...")
#     vector_store = VectorStore()
#     vector_store.load(store_dir)
    
#     print("Creating retriever...")
#     retriever = EnhancedRetriever(vector_store, chunks_file)
    
#     print("Initializing RAG chain with Gemini...")
#     rag = RAGChain(retriever)
    
#     # Process question
#     print(f"\nQuestion: {question}")
#     print("-" * 50)
    
#     result = rag.query(question)
    
#     print(f"\nANSWER:\n{result['answer']}")
#     print(f"\nSOURCES:")
#     for i, source in enumerate(result['sources']):
#         print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f})")
    
#     return result


# if __name__ == "__main__":
#     import sys
    
#     # Set your API key or use environment variable
#     # os.environ["GOOGLE_API_KEY"] = "your-key-here"
    
#     if len(sys.argv) > 1:
#         question = sys.argv[1]
#         chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
#         store_dir = sys.argv[3] if len(sys.argv) > 3 else "vector_store"
        
#         test_rag(question, chunks_file, store_dir)
#     else:
#         print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir]")

"""
RAG chain using Gemini API with proper image handling.
"""

# import sys
# from pathlib import Path
# from typing import List, Dict, Optional
# import logging

# sys.path.append(str(Path(__file__).parent))

# from gemini_client import GeminiClient
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class RAGChain:
#     """
#     RAG chain that properly handles images by passing them to Gemini Vision API.
#     """
    
#     def __init__(self, retriever, api_key: Optional[str] = None):
#         self.retriever = retriever
#         self.llm = GeminiClient(api_key=api_key)
    
#     def query(self, question: str, k: int = 5) -> Dict:
#         """
#         Process a question through the RAG chain.
#         Automatically uses vision API for image-related questions.
#         """
#         # Step 1: Retrieve relevant chunks
#         logger.info(f"Retrieving for: {question}")
#         results = self.retriever.search(question, k=k)
        
#         if not results:
#             return {
#                 "question": question,
#                 "answer": "No relevant information found.",
#                 "sources": [],
#                 "used_vision": False
#             }
        
#         # Step 2: Check for image chunks
#         image_chunks = [r for r in results if r.get("type") == "image" and r.get("image_path")]
        
#         # Step 3: Determine if this is a visual question
#         is_visual = self._is_visual_question(question)
        
#         # Step 4: Generate answer
#         if is_visual and image_chunks:
#             logger.info(f"Using VISION API - found {len(image_chunks)} relevant images")
#             answer = self._answer_with_vision(question, image_chunks)
#         elif image_chunks and not is_visual:
#             # Still pass image if user asks about it
#             logger.info("Question may need image, using vision API")
#             answer = self._answer_with_vision(question, image_chunks)
#         else:
#             logger.info("Using TEXT API")
#             answer = self.llm.generate_with_tables_and_chunks(question, results)
        
#         # Step 5: Prepare sources
#         sources = []
#         for result in results[:3]:
#             source = {
#                 "type": result.get("type", "text"),
#                 "page": result.get("page_num"),
#                 "similarity": result.get("similarity_score"),
#                 "content_preview": result.get("content", "")[:200]
#             }
#             if result.get("type") == "image" and result.get("image_path"):
#                 source["image_path"] = result["image_path"]
#             sources.append(source)
        
#         return {
#             "question": question,
#             "answer": answer,
#             "sources": sources,
#             "used_vision": is_visual or len(image_chunks) > 0
#         }
    
#     def _is_visual_question(self, question: str) -> bool:
#         """
#         Detect if a question requires understanding a chart/graph.
#         """
#         visual_keywords = [
#             "chart", "graph", "plot", "figure", "trend", "trajectory",
#             "line", "curve", "peak", "valley", "intersect", "cross",
#             "y-axis", "x-axis", "axis", "scale", "visual", "look at",
#             "compare the", "does the drop", "correspond", "physical intersect",
#             "left y-axis", "right y-axis", "maximum value printed"
#         ]
        
#         question_lower = question.lower()
#         return any(keyword in question_lower for keyword in visual_keywords)
    
#     def _answer_with_vision(self, question: str, image_chunks: List[Dict]) -> str:
#         """
#         Answer using Gemini Vision API on the retrieved image.
#         """
#         # Get the best matching image (highest similarity)
#         best_image = max(image_chunks, key=lambda x: x.get("similarity_score", 0))
#         image_path = best_image.get("image_path")
        
#         if not image_path or not Path(image_path).exists():
#             # Try to find image in the auto/images folder
#             base_name = Path(image_path).name if image_path else ""
#             alt_path = Path("outputs/sample_digital1/auto/images") / base_name
#             if alt_path.exists():
#                 image_path = str(alt_path)
#             else:
#                 logger.error(f"Image not found: {image_path}")
#                 return "Error: Could not locate the chart image file."
        
#         # Build a prompt that asks for visual analysis
#         prompt = f"""Analyze this chart from the annual report carefully.

# QUESTION: {question}

# INSTRUCTIONS:
# - Look at the visual elements: lines, axes, labels, scales
# - Describe the trajectory, trends, or patterns you see
# - Answer specific questions about intersections, drops, or correlations
# - Be precise about months, values, or relationships visible

# ANSWER based ONLY on what you see in this chart:"""

#         logger.info(f"Sending image to Gemini Vision: {image_path}")
#         return self.llm.generate_with_image(prompt, image_path)


# def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
#     """Test the RAG chain with image support."""
    
#     print("Loading vector store...")
#     vector_store = VectorStore()
#     vector_store.load(store_dir)
    
#     print("Creating retriever...")
#     retriever = EnhancedRetriever(vector_store, chunks_file)
    
#     # List all available images
#     print("\nAvailable images in chunks:")
#     image_paths = retriever.get_image_paths()
#     for path in image_paths:
#         exists = "✓" if Path(path).exists() else "✗"
#         print(f"  {exists} {path}")
    
#     print("\nInitializing RAG chain with Gemini...")
#     rag = RAGChain(retriever)
    
#     print(f"\nQuestion: {question}")
#     print("-" * 60)
    
#     result = rag.query(question)
    
#     print(f"\nUSED VISION: {result['used_vision']}")
#     print(f"\nANSWER:\n{result['answer']}")
#     print(f"\nSOURCES:")
#     for i, source in enumerate(result['sources']):
#         print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f})")
#         if source.get('image_path'):
#             print(f"     Image: {source['image_path']}")
    
#     return result


# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) > 1:
#         question = sys.argv[1]
#         chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
#         store_dir = sys.argv[3] if len(sys.argv) > 3 else "vector_store"
        
#         test_rag(question, chunks_file, store_dir)
#     else:
#         print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir]")

"""
RAG chain with auto-image attachment.
Automatically finds and attaches images referenced in retrieved chunks.
"""

# import sys
# from pathlib import Path
# from typing import List, Dict, Optional
# import logging
# from PIL import Image

# sys.path.append(str(Path(__file__).parent))

# from gemini_client import GeminiClient
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever
# from image_finder import ImageFinder

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class RAGChain:
#     """
#     RAG chain that automatically attaches images referenced in text chunks.
#     """
    
#     def __init__(self, retriever, images_folder: str = "outputs/sample_digital1/auto/images", api_key: Optional[str] = None):
#         self.retriever = retriever
#         self.llm = GeminiClient(api_key=api_key)
#         self.image_finder = ImageFinder(images_folder)
    
#     # def query(self, question: str, k: int = 5) -> Dict:
#     #     """
#     #     Process a question with auto-image attachment.
#     #     """
#     #     # Step 1: Retrieve chunks
#     #     logger.info(f"Retrieving for: {question}")
#     #     results = self.retriever.search(question, k=k)
        
#     #     if not results:
#     #         return {
#     #             "question": question,
#     #             "answer": "No relevant information found.",
#     #             "sources": [],
#     #             "images_attached": []
#     #         }
        
#     #     # Step 2: Auto-find images from the retrieved chunks
#     #     logger.info("Scanning chunks for image references...")
#     #     attached_images = self.image_finder.get_images_for_question(question, results)
#     #     logger.info(f"Attaching {len(attached_images)} images to prompt")
        
#     #     # Step 3: Build context from text chunks
#     #     context = self._build_context(results)
        
#     #     # Step 4: Generate answer
#     #     if attached_images:
#     #         logger.info("Using VISION API with attached images")
#     #         answer = self._answer_with_images(question, context, attached_images)
#     #     else:
#     #         logger.info("Using TEXT API (no images found)")
#     #         answer = self.llm.generate(self._build_prompt(question, context))
        
#     #     # Step 5: Prepare sources
#     #     sources = []
#     #     for result in results[:3]:
#     #         sources.append({
#     #             "type": result.get("type", "text"),
#     #             "page": result.get("page_num"),
#     #             "similarity": result.get("similarity_score"),
#     #             "content_preview": result.get("content", "")[:200]
#     #         })
        
#     #     return {
#     #         "question": question,
#     #         "answer": answer,
#     #         "sources": sources,
#     #         "images_attached": [str(p) for p in attached_images],
#     #         "used_vision": len(attached_images) > 0
#     #     }
#     def query(self, question: str, k: int = 5) -> Dict:
#         """
#         Process a question with anchor-based image extraction.
#         """
#         # Step 1: Retrieve chunks
#         logger.info(f"Retrieving for: {question}")
#         results = self.retriever.search(question, k=k)
        
#         if not results:
#             return {
#                 "question": question,
#                 "answer": "No relevant information found.",
#                 "sources": [],
#                 "images_attached": []
#             }
        
#         # Step 2: Extract images DIRECTLY from chunks using markdown parsing
#         logger.info("Scanning chunks for markdown image references...")
#         attached_images = self.image_finder.get_images_for_question(question, results)
        
#         # Step 3: Build context from text chunks (excluding image syntax for clarity)
#         context = self._build_context(results)
        
#         # Step 4: Generate answer
#         if attached_images:
#             logger.info(f"🎯 Using VISION API with {len(attached_images)} anchor-matched images")
#             answer = self._answer_with_images(question, context, attached_images)
#         else:
#             logger.info("Using TEXT API (no image anchors found in chunks)")
#             answer = self.llm.generate(self._build_prompt(question, context))
        
#         # Step 5: Prepare sources
#         sources = []
#         for result in results[:3]:
#             sources.append({
#                 "type": result.get("type", "text"),
#                 "page": result.get("page_num"),
#                 "similarity": result.get("similarity_score"),
#                 "content_preview": result.get("content", "")[:200]
#             })
        
#         return {
#             "question": question,
#             "answer": answer,
#             "sources": sources,
#             "images_attached": [str(p) for p in attached_images],
#             "used_vision": len(attached_images) > 0
#         }

#     def _build_context(self, chunks: List[Dict]) -> str:
#         """Build text context from chunks."""
#         context_parts = []
#         for i, chunk in enumerate(chunks[:5]):
#             content = chunk.get("formatted_content", chunk.get("content", ""))
#             chunk_type = chunk.get("type", "text")
#             page = chunk.get("page_num", "?")
#             context_parts.append(f"\n[Source {i+1} - Type: {chunk_type}, Page: {page}]\n{content[:1000]}")
#         return "\n".join(context_parts)
    
#     def _build_prompt(self, question: str, context: str) -> str:
#         """Build text-only prompt."""
#         return f"""You are a financial analyst. Answer based ONLY on the context.

# CONTEXT:
# {context}

# QUESTION: {question}

# ANSWER concisely and cite specific numbers from the context:"""

#     def _answer_with_images(self, question: str, context: str, image_paths: List[Path]) -> str:
#         """
#         Answer using Gemini Vision with attached images.
#         """
#         # Filter out non-image files and validate
#         valid_images = []
#         for img_path in image_paths:
#             # Skip .gitkeep and other non-image files
#             if img_path.name == '.gitkeep':
#                 continue
#             if img_path.suffix.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
#                 continue
#             if not img_path.exists():
#                 continue
#             valid_images.append(img_path)
        
#         if not valid_images:
#             logger.warning("No valid images found after filtering")
#             return self.llm.generate(self._build_prompt(question, context))
        
#         logger.info(f"Using {len(valid_images)} valid images for vision")
        
#         # Build prompt that asks for visual analysis
#         prompt = f"""Analyze the attached chart(s) from the annual report carefully.

#     QUESTION: {question}

#     INSTRUCTIONS for the chart(s) attached:
#     - Look at the visual elements: lines, axes, labels, scales
#     - Describe the trajectory, trends, or patterns you see
#     - Answer specific questions about intersections, drops, or correlations
#     - Be precise about months, values, or relationships visible

#     ANSWER based on what you SEE in the chart(s):"""

#         # Send first valid image to Gemini
#         return self.llm.generate_with_image(prompt, str(valid_images[0])) 
    
# #     def _answer_with_images(self, question: str, context: str, image_paths: List[Path]) -> str:
# #         """
# #         Answer using Gemini Vision with attached images.
# #         """
# #         # Build prompt that asks for visual analysis
# #         prompt = f"""Analyze the attached chart(s) from the annual report carefully.

# # CONTEXT TEXT (for reference):
# # {context[:1500]}

# # QUESTION: {question}

# # INSTRUCTIONS for the chart(s) attached:
# # - Look at the visual elements: lines, axes, labels, scales
# # - Describe the trajectory, trends, or patterns you see
# # - Answer specific questions about intersections, drops, or correlations
# # - Be precise about months, values, or relationships visible

# # ANSWER based on what you SEE in the chart(s):"""

# #         # Send first image to Gemini (simplest approach for now)
# #         # For multiple images, you'd need to iterate or send as list
# #         if image_paths:
# #             return self.llm.generate_with_image(prompt, str(image_paths[0]))
        
# #         return self.llm.generate(self._build_prompt(question, context))


# def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store", images_folder: str = "outputs/sample_digital1/auto/images"):
#     """Test the RAG chain with auto-image attachment."""
    
#     print("Loading vector store...")
#     vector_store = VectorStore()
#     vector_store.load(store_dir)
    
#     print("Creating retriever...")
#     retriever = EnhancedRetriever(vector_store, chunks_file)
    
#     print(f"Images folder: {images_folder}")
#     print(f"Folder exists: {Path(images_folder).exists()}")
    
#     print("\nInitializing RAG chain with auto-image attachment...")
#     rag = RAGChain(retriever, images_folder=images_folder)
    
#     print(f"\nQuestion: {question}")
#     print("-" * 60)
    
#     result = rag.query(question)
    
#     print(f"\nUSED VISION: {result['used_vision']}")
#     print(f"IMAGES ATTACHED: {len(result['images_attached'])}")
#     for img in result['images_attached']:
#         print(f"  - {img}")
    
#     print(f"\nANSWER:\n{result['answer']}")
#     print(f"\nSOURCES:")
#     for i, source in enumerate(result['sources']):
#         print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f})")
    
#     return result


# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) > 1:
#         question = sys.argv[1]
#         chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
#         store_dir = sys.argv[3] if len(sys.argv) > 3 else "vector_store"
#         images_folder = sys.argv[4] if len(sys.argv) > 4 else "outputs/sample_digital1/auto/images"
        
#         test_rag(question, chunks_file, store_dir, images_folder)
#     else:
#         print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir] [images_folder]")

"""
RAG chain with document map for accurate image retrieval.
"""

# import sys
# from pathlib import Path
# from typing import List, Dict, Optional
# import logging

# sys.path.append(str(Path(__file__).parent))

# from gemini_client import GeminiClient
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever
# from document_map import DocumentMap

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class RAGChain:
#     """
#     RAG chain that uses document map to find correct images.
#     """
    
#     def __init__(self, retriever, document_map: DocumentMap, api_key: Optional[str] = None):
#         self.retriever = retriever
#         self.doc_map = document_map
#         self.llm = GeminiClient(api_key=api_key)
    
#     def query(self, question: str, k: int = 5) -> Dict:
#         """
#         Process a question with document-map-based image retrieval.
#         """
#         # Step 1: Retrieve relevant chunks
#         logger.info(f"Retrieving for: {question}")
#         results = self.retriever.search(question, k=k)
        
#         if not results:
#             return {
#                 "question": question,
#                 "answer": "No relevant information found.",
#                 "sources": [],
#                 "images_attached": []
#             }
        
#         # Step 2: Use document map to find relevant images
#         logger.info("Finding images using document map...")
#         relevant_images = self.doc_map.find_images_for_query(question, results)
#         logger.info(f"Found {len(relevant_images)} relevant images via document map")
        
#         # Step 3: Build context from text chunks
#         context = self._build_context(results)
        
#         # Step 4: Generate answer
#         if relevant_images:
#             logger.info("Using VISION API with mapped images")
#             answer = self._answer_with_images(question, context, relevant_images)
#         else:
#             logger.info("Using TEXT API (no relevant images found)")
#             answer = self.llm.generate(self._build_prompt(question, context))
        
#         # Step 5: Prepare sources
#         sources = []
#         for result in results[:3]:
#             sources.append({
#                 "type": result.get("type", "text"),
#                 "page": result.get("page_num"),
#                 "similarity": result.get("similarity_score"),
#                 "content_preview": result.get("content", "")[:200]
#             })
        
#         return {
#             "question": question,
#             "answer": answer,
#             "sources": sources,
#             "images_attached": relevant_images,
#             "used_vision": len(relevant_images) > 0
#         }
    
#     def _build_context(self, chunks: List[Dict]) -> str:
#         """Build text context from chunks."""
#         context_parts = []
#         for i, chunk in enumerate(chunks[:5]):
#             content = chunk.get("formatted_content", chunk.get("content", ""))
#             chunk_type = chunk.get("type", "text")
#             page = chunk.get("page_num", "?")
#             context_parts.append(f"\n[Source {i+1} - Type: {chunk_type}, Page: {page}]\n{content[:800]}")
#         return "\n".join(context_parts)
    
#     def _build_prompt(self, question: str, context: str) -> str:
#         """Build text-only prompt."""
#         return f"""You are a financial analyst. Answer based ONLY on the context.

# CONTEXT:
# {context}

# QUESTION: {question}

# ANSWER concisely and cite specific numbers from the context:"""
    
#     def _answer_with_images(self, question: str, context: str, image_paths: List[str]) -> str:
#         """
#         Answer using Gemini Vision with relevant images.
#         """
#         if not image_paths:
#             return self.llm.generate(self._build_prompt(question, context))
        
#         # Verify images exist
#         valid_images = [p for p in image_paths if Path(p).exists()]
        
#         if not valid_images:
#             logger.warning("No valid images found")
#             return self.llm.generate(self._build_prompt(question, context))
        
#         # Build prompt that includes context and asks for visual analysis
#         prompt = f"""Analyze the attached chart(s) from the annual report.

# CONTEXT TEXT (for reference):
# {context[:1000]}

# QUESTION: {question}

# INSTRUCTIONS:
# - Look at the visual elements in the attached chart: lines, axes, labels, scales
# - Describe the trajectory, trends, or patterns
# - Answer specific questions about intersections, drops, or correlations
# - If the chart shows AIL vs SENSEX, identify where they intersect

# ANSWER based on what you SEE in the chart:"""

#         # Use first valid image
#         logger.info(f"Sending image to Gemini: {Path(valid_images[0]).name}")
#         return self.llm.generate_with_image(prompt, valid_images[0])


# def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store", map_path: str = "outputs/document_map.json"):
#     """Test the RAG chain with document map."""
    
#     print("Loading vector store...")
#     vector_store = VectorStore()
#     vector_store.load(store_dir)
    
#     print("Creating retriever...")
#     retriever = EnhancedRetriever(vector_store, chunks_file)
    
#     print("Loading document map...")
#     doc_map = DocumentMap.load(map_path, "outputs/sample_digital1/auto/images")
    
#     print("\nInitializing RAG chain...")
#     rag = RAGChain(retriever, doc_map)
    
#     print(f"\nQuestion: {question}")
#     print("-" * 60)
    
#     result = rag.query(question)
    
#     print(f"\nUSED VISION: {result['used_vision']}")
#     print(f"IMAGES ATTACHED: {len(result['images_attached'])}")
#     for img in result['images_attached']:
#         print(f"  - {Path(img).name}")
    
#     print(f"\nANSWER:\n{result['answer']}")
#     print(f"\nSOURCES:")
#     for i, source in enumerate(result['sources']):
#         print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f})")
    
#     return result


# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) > 1:
#         question = sys.argv[1]
#         chunks_file = sys.argv[2] if len(sys.argv) > 2 else "outputs/sample_digital1_chunks.json"
#         store_dir = sys.argv[3] if len(sys.argv) > 3 else "vector_store"
#         map_path = sys.argv[4] if len(sys.argv) > 4 else "outputs/document_map.json"
        
#         test_rag(question, chunks_file, store_dir, map_path)
#     else:
#         print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir] [map_path]")

"""
RAG chain with lightweight image linking.
No heavy parsing - uses markdown scanning.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging

sys.path.append(str(Path(__file__).parent))

from gemini_client import GeminiClient
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever
from image_linker import ImageLinker

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGChain:
    """
    RAG chain with lightweight image linking for charts.
    """
    
    def __init__(self, retriever, image_linker: Optional[ImageLinker] = None):
        self.retriever = retriever
        self.image_linker = image_linker
        self.llm = GeminiClient()
    
    def query(self, question: str, k: int = 5) -> Dict:
        """
        Process question - automatically finds images for chart queries.
        """
        # Step 1: Retrieve relevant chunks
        logger.info(f"Retrieving for: {question}")
        results = self.retriever.search(question, k=k)
        
        if not results:
            return {
                "question": question,
                "answer": "No relevant information found.",
                "sources": [],
                "images_attached": []
            }
        
        # Step 2: Check if this is a visual question
        is_visual = self._is_visual_question(question)
        
        # Step 3: Find images using the linker (if available)
        attached_images = []
        if self.image_linker and is_visual:
            logger.info("Searching for relevant images...")
            attached_images = self.image_linker.find_images_for_query(question)
            logger.info(f"Found {len(attached_images)} images for query")
        
        # Step 4: Build context
        context = self._build_context(results)
        
        # Step 5: Generate answer
        if attached_images:
            logger.info("Using VISION API with attached images")
            answer = self._answer_with_images(question, context, attached_images)
        else:
            logger.info("Using TEXT API")
            answer = self.llm.generate(self._build_prompt(question, context))
        
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
            "images_attached": attached_images,
            "used_vision": len(attached_images) > 0
        }
    
    def _is_visual_question(self, question: str) -> bool:
        """Detect if question requires chart understanding."""
        visual_keywords = [
            "chart", "graph", "plot", "figure", "trajectory",
            "intersect", "line", "trend", "visual", "look at",
            "performance", "comparison", "broad based indices"
        ]
        return any(kw in question.lower() for kw in visual_keywords)
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context from chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):
            content = chunk.get("content", "")[:800]
            chunk_type = chunk.get("type", "text")
            context_parts.append(f"[{i+1}] ({chunk_type}): {content}")
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build text prompt."""
        return f"""Answer based ONLY on the context below.

CONTEXT:
{context}

QUESTION: {question}

ANSWER concisely with specific numbers:"""
    
    def _answer_with_images(self, question: str, context: str, image_paths: List[str]) -> str:
        """Answer using Gemini Vision."""
        if not image_paths:
            return self.llm.generate(self._build_prompt(question, context))
        
        # Use first valid image
        first_image = image_paths[0]
        
        prompt = f"""Analyze the attached chart from the annual report.

QUESTION: {question}

INSTRUCTIONS:
- Look at the visual elements: lines, axes, labels
- Describe trajectory, trends, and intersections
- Answer based on what you SEE in the chart

ANSWER:"""

        logger.info(f"Sending image to Gemini: {Path(first_image).name}")
        return self.llm.generate_with_image(prompt, first_image)


def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
    """Test the RAG chain."""
    
    # Load components
    print("Loading vector store...")
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    print("Creating retriever...")
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    # Load image linker
    markdown_path = Path("outputs/sample_digital1/auto/sample_digital1.md")
    if not markdown_path.exists():
        markdown_path = Path("outputs/sample_digital1/auto/content.md")
    
    images_folder = "outputs/sample_digital1/auto/images"
    
    if markdown_path.exists() and Path(images_folder).exists():
        print("Loading image linker...")
        image_linker = ImageLinker(str(markdown_path), images_folder)
    else:
        print("Image linker not available (markdown or images folder missing)")
        image_linker = None
    
    print("Initializing RAG chain...")
    rag = RAGChain(retriever, image_linker)
    
    print(f"\nQuestion: {question}")
    print("-" * 60)
    
    result = rag.query(question)
    
    print(f"\nUSED VISION: {result['used_vision']}")
    print(f"IMAGES ATTACHED: {len(result['images_attached'])}")
    for img in result['images_attached'][:3]:
        print(f"  - {Path(img).name}")
    
    print(f"\nANSWER:\n{result['answer']}")
    
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