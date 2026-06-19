# """
# Enhanced retriever that handles tables and images properly.
# """

# import json
# import base64
# from pathlib import Path
# from typing import List, Dict, Optional
# import logging

# import pandas as pd
# from bs4 import BeautifulSoup

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class EnhancedRetriever:
#     """
#     Retriever that formats tables and images for LLM consumption.
#     """
    
#     def __init__(self, vector_store, chunks_path: str):
#         """
#         Args:
#             vector_store: VectorStore instance
#             chunks_path: Path to chunks JSON (for accessing HTML/image paths)
#         """
#         self.vector_store = vector_store
#         self.chunks = self._load_chunks(chunks_path)
#         self.chunks_by_id = {c["chunk_id"]: c for c in self.chunks}
    
#     def _load_chunks(self, chunks_path: str) -> List[Dict]:
#         """Load chunks from JSON file."""
#         with open(chunks_path, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     def search(self, query: str, k: int = 5) -> List[Dict]:
#         """
#         Search and format results with proper table/image handling.
#         Now includes chunk_id for verification.
#         """
#         # Get search results
#         results = self.vector_store.search(query, k=k)
        
#         # Enhance each result with formatted content
#         for result in results:
#             chunk_id = result.get("chunk_id")
#             chunk_type = result.get("type", "text")
            
#             # Add chunk_id to result for easy reference
#             result["chunk_id"] = chunk_id
            
#             if chunk_type == "table" and result.get("html"):
#                 result["formatted_content"] = self._format_table(result["html"])
#                 result["content_for_llm"] = result["formatted_content"]
            
#             elif chunk_type == "image" and result.get("image_path"):
#                 result["formatted_content"] = self._format_image(result)
#                 result["content_for_llm"] = result.get("caption", "Chart image")
#                 result["image_base64"] = self._encode_image(result.get("image_path"))
            
#             else:
#                 # Plain text
#                 result["formatted_content"] = result["content"]
#                 result["content_for_llm"] = result["content"]
        
#         return results
    
#     def _format_table(self, html: str) -> str:
#         """
#         Convert HTML table to readable markdown with natural language.
#         """
#         try:
#             # Parse HTML
#             soup = BeautifulSoup(html, 'html.parser')
#             table = soup.find('table')
            
#             if not table:
#                 return html
            
#             # Extract headers
#             headers = []
#             thead = table.find('thead')
#             if thead:
#                 headers = [th.get_text(strip=True) for th in thead.find_all('th')]
            
#             if not headers:
#                 # Try first row as headers
#                 first_row = table.find('tr')
#                 if first_row:
#                     headers = [td.get_text(strip=True) for td in first_row.find_all(['td', 'th'])]
            
#             # Extract data rows
#             data_rows = []
#             for tr in table.find_all('tr')[1:]:  # Skip header row
#                 row = [td.get_text(strip=True) for td in tr.find_all('td')]
#                 if row and any(row):  # Non-empty row
#                     data_rows.append(row)
            
#             # Convert to markdown table
#             if headers and data_rows:
#                 markdown = "| " + " | ".join(headers) + " |\n"
#                 markdown += "|" + "|".join([" --- " for _ in headers]) + "|\n"
#                 for row in data_rows[:10]:  # Limit to 10 rows for LLM context
#                     # Pad row to match header length
#                     padded_row = row + [""] * (len(headers) - len(row))
#                     markdown += "| " + " | ".join(padded_row) + " |\n"
                
#                 # Add natural language summary
#                 summary = f"\nTable with {len(data_rows)} rows and {len(headers)} columns.\n"
#                 summary += f"Columns: {', '.join(headers)}\n"
#                 summary += f"First few rows: {data_rows[:3] if data_rows else 'No data'}\n"
                
#                 return summary + "\n" + markdown
            
#             return html
        
#         except Exception as e:
#             logger.error(f"Table formatting failed: {e}")
#             return html
  
#     def _format_image(self, chunk: Dict) -> str:
#         """
#         Format image chunk for LLM consumption.
#         Returns a descriptive string that helps retrieval.
#         """
#         caption = chunk.get("caption", chunk.get("content", "Chart from document"))
#         path = chunk.get("image_path", "")
#         page_num = chunk.get("page_num", "unknown")
        
#         # Create a rich description for vector search
#         description = f"[CHART] {caption} from page {page_num}. This is a visual chart/graph from the annual report. The image file is located at: {path}"
        
#         # Store the actual path for later vision processing
#         chunk["image_path_for_vision"] = path
        
#         return description


#     def _encode_image(self, image_path: Optional[str]) -> Optional[str]:
#         """
#         Encode image to base64 for Gemini vision.
#         """
#         if not image_path or not Path(image_path).exists():
#             return None
        
#         try:
#             with open(image_path, "rb") as f:
#                 return base64.b64encode(f.read()).decode('utf-8')
#         except Exception as e:
#             logger.error(f"Image encoding failed: {e}")
#             return None
        
#     def get_image_paths(self) -> List[str]:
#         """
#         Get all image paths from chunks (public method).
#         """
#         image_paths = []
#         for chunk in self.chunks:
#             if chunk.get("type") == "image" and chunk.get("image_path"):
#                 image_paths.append(chunk["image_path"])
#         return image_paths    


# def create_context_from_results(results: List[Dict], max_tokens: int = 2000) -> str:
#     """
#     Create a context string from search results for LLM prompt.
#     """
#     context_parts = []
#     current_length = 0
    
#     for i, result in enumerate(results):
#         content = result.get("formatted_content", result.get("content", ""))
#         chunk_type = result.get("type", "text")
#         page_num = result.get("page_num", "?")
        
#         # Add header
#         part = f"\n[Source {i+1} - Type: {chunk_type}, Page: {page_num}]\n"
#         part += content
#         part += "\n" + "-" * 50
        
#         # Check token budget (rough estimate: 1 token ~ 4 chars)
#         if current_length + len(part) > max_tokens * 4:
#             break
        
#         context_parts.append(part)
#         current_length += len(part)
    
#     return "\n".join(context_parts)



# if __name__ == "__main__":
#     import sys
#     sys.path.append('src')
    
#     from vector_store import VectorStore
    
#     if len(sys.argv) > 1:
#         chunks_file = sys.argv[1]
#         store_dir = sys.argv[2] if len(sys.argv) > 2 else "vector_store"
        
#         # Load vector store
#         print(f"Loading vector store from: {store_dir}")
#         vector_store = VectorStore()
#         vector_store.load(store_dir)
        
#         # Create enhanced retriever
#         retriever = EnhancedRetriever(vector_store, chunks_file)
        
#         # Test search
#         print("\n===== ENHANCED RETRIEVER TEST =====")
#         test_query = input("Enter test query: ").strip()
        
#         if test_query:
#             results = retriever.search(test_query, k=3)
            
#             print(f"\nSearch results for: '{test_query}'")
#             for i, result in enumerate(results):
#                 print(f"\n{i+1}. Type: {result['type']} (Score: {result['similarity_score']:.3f})")
#                 print(f"   Page: {result.get('page_num', '?')}")
#                 print(f"   Formatted content preview: {result['formatted_content'][:300]}...")
            
#             # Create context for LLM
#             context = create_context_from_results(results)
#             print(f"\n===== CONTEXT FOR LLM =====")
#             print(context[:1000])
#     else:
#         print("Usage: python enhanced_retriever.py <chunks_json_path> [store_dir]")

"""
Enhanced retriever that handles tables and images properly.
Now with image attachment and HTML table cleaning.
"""

import json
import base64
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import pandas as pd
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class EnhancedRetriever:
    """
    Retriever that formats tables and images for LLM consumption.
    Now includes image loading and table cleaning.
    """
    
    def __init__(self, vector_store, chunks_path: str, processed_docs_base: str = "processed_docs"):
        """
        Args:
            vector_store: VectorStore instance
            chunks_path: Path to chunks JSON
            processed_docs_base: Base directory for processed documents
        """
        self.vector_store = vector_store
        self.processed_docs_base = Path(processed_docs_base)
        self.chunks = self._load_chunks(chunks_path)
        self.chunks_by_id = {c["chunk_id"]: c for c in self.chunks}
    
    def _load_chunks(self, chunks_path: str) -> List[Dict]:
        """Load chunks from JSON file."""
        with open(chunks_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def search(self, query: str, k: int = 5) -> List[Dict]:
        """
        Search and format results with proper table/image handling.
        Now returns images as base64 for attachment.
        """
        results = self.vector_store.search(query, k=k)
        
        for result in results:
            chunk_id = result.get("chunk_id")
            chunk_type = result.get("type", "text")
            
            result["chunk_id"] = chunk_id
            
            if chunk_type == "table" and result.get("html"):
                # Clean HTML table to proper markdown
                clean_markdown = self._clean_html_table_to_markdown(result["html"])
                result["formatted_content"] = clean_markdown
                result["content_for_llm"] = clean_markdown
                result["cleaned_table"] = True
            
            elif chunk_type == "image" or self._contains_image_reference(result.get("content", "")):
                # Find and load the actual image
                image_data = self._extract_and_load_image(result)
                if image_data:
                    result["image_base64"] = image_data["base64"]
                    result["image_path"] = image_data["path"]
                    result["content_for_llm"] = f"[IMAGE: {image_data['path'].name}]"
                    result["formatted_content"] = f"This chunk contains an image/chart. The image is attached separately."
                    result["has_image"] = True
                else:
                    result["formatted_content"] = result.get("content", "")
                    result["content_for_llm"] = result.get("content", "")
            
            else:
                result["formatted_content"] = result.get("content", "")
                result["content_for_llm"] = result.get("content", "")
        
        return results
    
    def _clean_html_table_to_markdown(self, html: str) -> str:
        """
        Convert complex HTML table (with rowspan/colspan) to clean markdown.
        Uses pandas to flatten the table structure.
        """
        try:
            # Use pandas to read HTML and flatten the structure
            dfs = pd.read_html(html)
            if dfs:
                df = dfs[0]
                
                # Clean column names
                df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
                
                # Convert to markdown
                markdown = df.to_markdown()
                
                # Add summary
                summary = f"Table with {df.shape[0]} rows and {df.shape[1]} columns.\n"
                summary += f"Columns: {', '.join(df.columns.astype(str)[:10])}\n\n"
                
                return summary + markdown
            
            return html
            
        except Exception as e:
            logger.warning(f"Table cleaning failed: {e}")
            return html
    
    def _contains_image_reference(self, content: str) -> bool:
        """Check if content contains an image reference."""
        patterns = [
            r'!\[.*?\]\(.*?\.(jpg|jpeg|png|gif)\)',
            r'<img[^>]+src=["\'].*?\.(jpg|jpeg|png|gif)',
            r'\.\./images/[\w\d]+\.jpg',
            r'images/[\w\d]+\.jpg',
        ]
        for pattern in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def _extract_and_load_image(self, chunk: Dict) -> Optional[Dict]:
        """
        Extract image path from chunk and load as base64.
        """
        content = chunk.get("content", "")
        
        # Try to get image path from chunk metadata first
        image_path = chunk.get("image_path")
        
        # If not, extract from content
        if not image_path:
            patterns = [
                r'!\[.*?\]\((.*?\.(jpg|jpeg|png|gif))\)',
                r'src=["\'](.*?\.(jpg|jpeg|png|gif))',
                r'(images/[\w\d]+\.jpg)',
                r'(\.\./images/[\w\d]+\.jpg)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    image_path = match.group(1)
                    break
        
        if not image_path:
            return None
        
        # Resolve full path
        full_path = self._resolve_image_path(image_path, chunk.get("source", ""))
        
        if full_path and full_path.exists():
            try:
                with open(full_path, 'rb') as f:
                    image_base64 = base64.b64encode(f.read()).decode('utf-8')
                return {
                    "base64": image_base64,
                    "path": full_path,
                    "mime": f"image/{full_path.suffix[1:]}"
                }
            except Exception as e:
                logger.error(f"Failed to load image {full_path}: {e}")
        
        return None
    
    def _resolve_image_path(self, image_path: str, source_path: str) -> Optional[Path]:
        """
        Resolve image path to actual file location.
        """
        # Try different resolution strategies
        
        # Strategy 1: Direct path
        direct = Path(image_path)
        if direct.exists():
            return direct
        
        # Strategy 2: Relative to processed_docs
        # Extract doc_id from source path
        source_parts = Path(source_path).parts
        if "processed_docs" in source_parts:
            doc_idx = source_parts.index("processed_docs")
            if doc_idx + 1 < len(source_parts):
                doc_id = source_parts[doc_idx + 1]
                doc_dir = self.processed_docs_base / doc_id
                
                # Search for images folder
                for images_dir in doc_dir.rglob("images"):
                    candidate = images_dir / Path(image_path).name
                    if candidate.exists():
                        return candidate
        
        # Strategy 3: Search recursively in processed_docs
        for images_dir in self.processed_docs_base.rglob("images"):
            candidate = images_dir / Path(image_path).name
            if candidate.exists():
                return candidate
        
        return None
    
    def get_images_for_results(self, results: List[Dict]) -> List[Dict]:
        """
        Extract all images from results for multi-modal attachment.
        """
        images = []
        for result in results:
            if result.get("has_image") and result.get("image_base64"):
                images.append({
                    "base64": result["image_base64"],
                    "path": result.get("image_path"),
                    "mime": "image/jpeg"
                })
        return images


# Helper function for testing
def test_enhanced_retriever(chunks_file: str, store_dir: str = "vector_store"):
    """Test the enhanced retriever."""
    from vector_store import VectorStore
    
    vector_store = VectorStore()
    vector_store.load(store_dir)
    
    retriever = EnhancedRetriever(vector_store, chunks_file)
    
    test_query = "What is the shareholding pattern?"
    results = retriever.search(test_query, k=3)
    
    print(f"Results for '{test_query}':")
    for r in results:
        print(f"  - Type: {r.get('type', 'text')}, Score: {r['similarity_score']:.3f}")
        print(f"    Has image: {r.get('has_image', False)}")
        print(f"    Preview: {r.get('formatted_content', '')[:100]}...")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        chunks_file = sys.argv[1]
        store_dir = sys.argv[2] if len(sys.argv) > 2 else "vector_store"
        test_enhanced_retriever(chunks_file, store_dir)