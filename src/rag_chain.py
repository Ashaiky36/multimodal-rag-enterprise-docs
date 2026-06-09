
# """
# RAG chain with lightweight image linking.
# No heavy parsing - uses markdown scanning.
# """

# import sys
# from pathlib import Path
# from typing import List, Dict, Optional
# import logging

# sys.path.append(str(Path(__file__).parent))

# from gemini_client import GeminiClient
# from vector_store import VectorStore
# from enhanced_retriever import EnhancedRetriever
# from image_linker import ImageLinker

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class RAGChain:
#     """
#     RAG chain with lightweight image linking for charts.
#     """
    
#     def __init__(self, retriever, image_linker: Optional[ImageLinker] = None):
#         self.retriever = retriever
#         self.image_linker = image_linker
#         self.llm = GeminiClient()
    
#     def query(self, question: str, k: int = 5) -> Dict:
#         """
#         Process question - automatically finds images for chart queries.
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
        
#         # Step 2: Check if this is a visual question
#         is_visual = self._is_visual_question(question)
        
#         # Step 3: Find images using the linker (if available)
#         attached_images = []
#         if self.image_linker and is_visual:
#             logger.info("Searching for relevant images...")
#             attached_images = self.image_linker.find_images_for_query(question)
#             logger.info(f"Found {len(attached_images)} images for query")
        
#         # Step 4: Build context
#         context = self._build_context(results)
        
#         # Step 5: Generate answer
#         if attached_images:
#             logger.info("Using VISION API with attached images")
#             answer = self._answer_with_images(question, context, attached_images)
#         else:
#             logger.info("Using TEXT API")
#             answer = self.llm.generate(self._build_prompt(question, context))
        
#         # Step 6: Prepare sources
#         sources = []
#         for result in results[:3]:
#             sources.append({
#                 "type": result.get("type", "text"),
#                 "similarity": result.get("similarity_score"),
#                 "content_preview": result.get("content", "")[:200]
#             })
        
#         return {
#             "question": question,
#             "answer": answer,
#             "sources": sources,
#             "images_attached": attached_images,
#             "used_vision": len(attached_images) > 0
#         }
    
#     def _is_visual_question(self, question: str) -> bool:
#         """Detect if question requires chart understanding."""
#         visual_keywords = [
#             "chart", "graph", "plot", "figure", "trajectory",
#             "intersect", "line", "trend", "visual", "look at",
#             "performance", "comparison", "broad based indices"
#         ]
#         return any(kw in question.lower() for kw in visual_keywords)
    
#     def _build_context(self, chunks: List[Dict]) -> str:
#         """Build context from chunks."""
#         context_parts = []
#         for i, chunk in enumerate(chunks[:5]):
#             content = chunk.get("content", "")[:800]
#             chunk_type = chunk.get("type", "text")
#             context_parts.append(f"[{i+1}] ({chunk_type}): {content}")
#         return "\n\n".join(context_parts)
    
#     def _build_prompt(self, question: str, context: str) -> str:
#         """Build text prompt."""
#         return f"""Answer based ONLY on the context below.

# CONTEXT:
# {context}

# QUESTION: {question}

# ANSWER concisely with specific numbers:"""
    
#     def _answer_with_images(self, question: str, context: str, image_paths: List[str]) -> str:
#         """Answer using Gemini Vision."""
#         if not image_paths:
#             return self.llm.generate(self._build_prompt(question, context))
        
#         # Use first valid image
#         first_image = image_paths[0]
        
#         prompt = f"""Analyze the attached chart from the annual report.

# QUESTION: {question}

# INSTRUCTIONS:
# - Look at the visual elements: lines, axes, labels
# - Describe trajectory, trends, and intersections
# - Answer based on what you SEE in the chart

# ANSWER:"""

#         logger.info(f"Sending image to Gemini: {Path(first_image).name}")
#         return self.llm.generate_with_image(prompt, first_image)


# def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
#     """Test the RAG chain."""
    
#     # Load components
#     print("Loading vector store...")
#     vector_store = VectorStore()
#     vector_store.load(store_dir)
    
#     print("Creating retriever...")
#     retriever = EnhancedRetriever(vector_store, chunks_file)
    
#     # Load image linker
#     markdown_path = Path("outputs/sample_digital1/auto/sample_digital1.md")
#     if not markdown_path.exists():
#         markdown_path = Path("outputs/sample_digital1/auto/content.md")
    
#     images_folder = "outputs/sample_digital1/auto/images"
    
#     if markdown_path.exists() and Path(images_folder).exists():
#         print("Loading image linker...")
#         image_linker = ImageLinker(str(markdown_path), images_folder)
#     else:
#         print("Image linker not available (markdown or images folder missing)")
#         image_linker = None
    
#     print("Initializing RAG chain...")
#     rag = RAGChain(retriever, image_linker)
    
#     print(f"\nQuestion: {question}")
#     print("-" * 60)
    
#     result = rag.query(question)
    
#     print(f"\nUSED VISION: {result['used_vision']}")
#     print(f"IMAGES ATTACHED: {len(result['images_attached'])}")
#     for img in result['images_attached'][:3]:
#         print(f"  - {Path(img).name}")
    
#     print(f"\nANSWER:\n{result['answer']}")
    
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
RAG chain with proper multi-modal support.
Attaches images directly to Gemini API calls.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional
import logging
import base64

sys.path.append(str(Path(__file__).parent))

from gemini_client import GeminiClient
from vector_store import VectorStore
from enhanced_retriever import EnhancedRetriever

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RAGChain:
    """
    RAG chain that properly attaches images to multi-modal LLM calls.
    """
    
    def __init__(self, retriever: EnhancedRetriever):
        self.retriever = retriever
        self.llm = GeminiClient()
    
    def query(self, question: str, k: int = 5) -> Dict:
        """
        Process question - automatically attaches images for visual queries.
        """
        # Step 1: Retrieve chunks
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
        
        # Step 3: Extract images from results
        attached_images = []
        if is_visual:
            attached_images = self.retriever.get_images_for_results(results)
            logger.info(f"Found {len(attached_images)} images to attach")
        
        # Step 4: Build text context
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
                "content_preview": result.get("content", "")[:200],
                "has_image": result.get("has_image", False)
            })
        
        return {
            "question": question,
            "answer": answer,
            "sources": sources,
            "images_attached": len(attached_images),
            "used_vision": len(attached_images) > 0
        }
    
    def _is_visual_question(self, question: str) -> bool:
        """Detect if question requires chart/image understanding."""
        visual_keywords = [
            "chart", "graph", "plot", "figure", "trajectory",
            "pie", "bar", "line", "trend", "visual", "look at",
            "performance", "comparison", "broad based indices",
            "percentage of revenue", "pie chart"
        ]
        return any(kw in question.lower() for kw in visual_keywords)
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build text context from chunks."""
        context_parts = []
        for i, chunk in enumerate(chunks[:5]):
            content = chunk.get("formatted_content", chunk.get("content", ""))[:800]
            chunk_type = chunk.get("type", "text")
            has_img = chunk.get("has_image", False)
            
            img_indicator = " [IMAGE ATTACHED]" if has_img else ""
            context_parts.append(f"[{i+1}] ({chunk_type}{img_indicator}): {content}")
        
        return "\n\n".join(context_parts)
    
    def _build_prompt(self, question: str, context: str) -> str:
        """Build text-only prompt."""
        return f"""You are a financial analyst. Answer based ONLY on the context below.

CONTEXT:
{context}

QUESTION: {question}

INSTRUCTIONS:
- Extract exact numbers from tables
- If tables have rowspan/colspan, read the structure carefully
- Provide complete answers, not partial
- If you cannot find the exact answer, say so

ANSWER:"""
    
    def _answer_with_images(self, question: str, context: str, images: List[Dict]) -> str:
        """
        Answer using Gemini Vision with attached images.
        """
        if not images:
            return self.llm.generate(self._build_prompt(question, context))
        
        # Build prompt that includes context and asks for visual analysis
        prompt = f"""Analyze the attached image(s) from the annual report.

TEXT CONTEXT (for reference):
{context[:1500]}

QUESTION: {question}

INSTRUCTIONS:
- Look carefully at the attached image(s)
- If it's a chart, read the labels, percentages, and categories
- Extract specific numbers from pie charts, bar charts, or graphs
- Answer based on what you SEE in the image(s)

ANSWER:"""

        # Use the first image (Gemini can handle multiple but keep simple)
        first_image = images[0]
        
        # For Gemini, we need to send the image as part of the message
        # Since our gemini_client supports generate_with_image, use that
        # But we need to save the base64 to a temp file or use direct bytes
        
        # Save base64 to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{first_image['mime'].split('/')[-1]}") as tmp_file:
            tmp_file.write(base64.b64decode(first_image["base64"]))
            tmp_path = tmp_file.name
        
        try:
            answer = self.llm.generate_with_image(prompt, tmp_path)
            return answer
        finally:
            # Clean up temp file
            if Path(tmp_path).exists():
                Path(tmp_path).unlink()


def test_rag(question: str, chunks_file: str, store_dir: str = "vector_store"):
    """Test the RAG chain with image support."""
    
    print("Loading vector store...")
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    print("Creating enhanced retriever...")
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    print("Initializing RAG chain...")
    rag = RAGChain(retriever)
    
    print(f"\nQuestion: {question}")
    print("-" * 60)
    
    result = rag.query(question)
    
    print(f"\nUSED VISION: {result['used_vision']}")
    print(f"IMAGES ATTACHED: {result['images_attached']}")
    print(f"\nANSWER:\n{result['answer']}")
    print(f"\nSOURCES:")
    for i, source in enumerate(result['sources']):
        print(f"  {i+1}. {source['type']} (similarity: {source['similarity']:.3f}) - Has image: {source['has_image']}")
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        question = sys.argv[1]
        chunks_file = sys.argv[2] if len(sys.argv) > 2 else "processed_docs/453a25ab489a/453a25ab489a_chunks.json"
        store_dir = sys.argv[3] if len(sys.argv) > 3 else "processed_docs/453a25ab489a/vector_store"
        
        test_rag(question, chunks_file, store_dir)
    else:
        print("Usage: python rag_chain.py 'your question here' [chunks_json_path] [store_dir]")