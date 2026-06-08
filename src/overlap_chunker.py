# # # """
# # # Lightweight overlap chunker - no merging, just overlapping chunks.
# # # Memory efficient for 8GB RAM.
# # # """

# # # import re
# # # from pathlib import Path
# # # from typing import List, Dict
# # # import logging

# # # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # # logger = logging.getLogger(__name__)


# # # class OverlapChunker:
# # #     """
# # #     Simple overlapping chunker.
# # #     Creates overlapping chunks to preserve context across boundaries.
# # #     No heavy merging - just overlap.
# # #     """
    
# # #     def __init__(self, chunk_size: int = 1000, overlap: int = 200):
# # #         """
# # #         Args:
# # #             chunk_size: Characters per chunk
# # #             overlap: Characters to overlap (keeps heading with its table)
# # #         """
# # #         self.chunk_size = chunk_size
# # #         self.overlap = overlap
# # #         logger.info(f"OverlapChunker: size={chunk_size}, overlap={overlap}")
    
# # #     def chunk_markdown(self, markdown_path: str, output_path: str) -> List[Dict]:
# # #         """
# # #         Create overlapping chunks from markdown file.
# # #         """
# # #         with open(markdown_path, 'r', encoding='utf-8') as f:
# # #             content = f.read()
        
# # #         # Split by double newlines first (paragraph boundaries)
# # #         paragraphs = re.split(r'\n\s*\n', content)
        
# # #         chunks = []
# # #         current_chunk = ""
# # #         chunk_id = 0
        
# # #         for para in paragraphs:
# # #             para = para.strip()
# # #             if not para:
# # #                 continue
            
# # #             # If adding this paragraph exceeds chunk size, save current chunk
# # #             if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
# # #                 chunks.append({
# # #                     "chunk_id": chunk_id,
# # #                     "type": "text",
# # #                     "content": current_chunk.strip(),
# # #                     "source": markdown_path
# # #                 })
# # #                 chunk_id += 1
                
# # #                 # Keep overlap from previous chunk
# # #                 if self.overlap > 0 and len(current_chunk) > self.overlap:
# # #                     # Take last N characters as overlap
# # #                     overlap_text = current_chunk[-self.overlap:]
# # #                     current_chunk = overlap_text + "\n" + para
# # #                 else:
# # #                     current_chunk = para
# # #             else:
# # #                 if current_chunk:
# # #                     current_chunk += "\n\n" + para
# # #                 else:
# # #                     current_chunk = para
        
# # #         # Add last chunk
# # #         if current_chunk:
# # #             chunks.append({
# # #                 "chunk_id": chunk_id,
# # #                 "type": "text",
# # #                 "content": current_chunk.strip(),
# # #                 "source": markdown_path
# # #             })
        
# # #         # Save to JSON
# # #         import json
# # #         with open(output_path, 'w', encoding='utf-8') as f:
# # #             json.dump(chunks, f, indent=2, ensure_ascii=False)
        
# # #         logger.info(f"Created {len(chunks)} overlapping chunks")
# # #         return chunks


# # # def create_overlapping_chunks_from_mineru(
# # #     markdown_path: str,
# # #     output_path: str,
# # #     chunk_size: int = 1000,
# # #     overlap: int = 200
# # # ) -> List[Dict]:
# # #     """
# # #     Create overlapping chunks from MinerU markdown.
    
# # #     Args:
# # #         markdown_path: Path to MinerU's .md file
# # #         output_path: Where to save chunks
# # #         chunk_size: Characters per chunk
# # #         overlap: Overlap characters (200-300 recommended)
# # #     """
# # #     chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
# # #     chunks = chunker.chunk_markdown(markdown_path, output_path)
    
# # #     # Verify Shareholding Pattern
# # #     verify_chunks(chunks)
    
# # #     return chunks


# # # def verify_chunks(chunks: List[Dict]):
# # #     """
# # #     Verify that Shareholding Pattern heading and table are in same chunk.
# # #     """
# # #     for chunk in chunks:
# # #         content = chunk["content"]
# # #         if "Shareholding Pattern" in content:
# # #             if "Mutual Funds" in content:
# # #                 print(f"\n✅ Chunk {chunk['chunk_id']}: Shareholding Pattern + table intact")
# # #                 # Extract Mutual Funds info
# # #                 import re
# # #                 mutual_match = re.search(r'Mutual Funds\s+([\d,]+)\s+([\d.]+)', content)
# # #                 if mutual_match:
# # #                     print(f"   Mutual Funds: {mutual_match.group(1)} shares ({mutual_match.group(2)}%)")
# # #                 return True
# # #             else:
# # #                 print(f"\n❌ Chunk {chunk['chunk_id']}: Shareholding Pattern heading found but table missing")
# # #                 print(f"   Preview: {content[:200]}...")
# # #                 return False
    
# # #     print("\n❌ Shareholding Pattern not found in any chunk")
# # #     return False


# # # if __name__ == "__main__":
# # #     import sys
    
# # #     # Paths
# # #     markdown_path = "outputs/sample_digital1/auto/sample_digital1.md"
# # #     if not Path(markdown_path).exists():
# # #         markdown_path = "outputs/sample_digital1/auto/content.md"
    
# # #     output_path = "outputs/sample_digital1_chunks_overlap.json"
    
# # #     if Path(markdown_path).exists():
# # #         # Create overlapping chunks
# # #         chunks = create_overlapping_chunks_from_mineru(
# # #             markdown_path,
# # #             output_path,
# # #             chunk_size=1000,
# # #             overlap=250  # 250 character overlap
# # #         )
        
# # #         print(f"\nChunks saved to: {output_path}")
# # #     else:
# # #         print(f"Markdown not found: {markdown_path}")

# # """
# # Lightweight overlap chunker - no merging, just overlapping chunks.
# # Memory efficient for 8GB RAM.
# # """

# # import re
# # import json
# # from pathlib import Path
# # from typing import List, Dict
# # import logging

# # logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# # logger = logging.getLogger(__name__)


# # class OverlapChunker:
# #     """
# #     Simple overlapping chunker.
# #     Creates overlapping chunks to preserve context across boundaries.
# #     """
    
# #     def __init__(self, chunk_size: int = 1000, overlap: int = 250):
# #         self.chunk_size = chunk_size
# #         self.overlap = overlap
# #         logger.info(f"OverlapChunker: size={chunk_size}, overlap={overlap}")
    
# #     def chunk_markdown(self, markdown_path: str, output_path: str) -> List[Dict]:
# #         """Create overlapping chunks from markdown file."""
        
# #         markdown_file = Path(markdown_path)
# #         if not markdown_file.exists():
# #             logger.error(f"Markdown file not found: {markdown_path}")
# #             return []
        
# #         with open(markdown_file, 'r', encoding='utf-8') as f:
# #             content = f.read()
        
# #         if not content.strip():
# #             logger.error("Markdown file is empty")
# #             return []
        
# #         # Split by double newlines (paragraph boundaries)
# #         paragraphs = re.split(r'\n\s*\n', content)
        
# #         chunks = []
# #         current_chunk = ""
# #         chunk_id = 0
        
# #         for para in paragraphs:
# #             para = para.strip()
# #             if not para:
# #                 continue
            
# #             # If adding this paragraph exceeds chunk size, save current chunk
# #             if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
# #                 chunks.append({
# #                     "chunk_id": chunk_id,
# #                     "type": "text",
# #                     "content": current_chunk.strip(),
# #                     "source": str(markdown_file)
# #                 })
# #                 chunk_id += 1
                
# #                 # Keep overlap from previous chunk
# #                 if self.overlap > 0 and len(current_chunk) > self.overlap:
# #                     overlap_text = current_chunk[-self.overlap:]
# #                     current_chunk = overlap_text + "\n\n" + para
# #                 else:
# #                     current_chunk = para
# #             else:
# #                 if current_chunk:
# #                     current_chunk += "\n\n" + para
# #                 else:
# #                     current_chunk = para
        
# #         # Add last chunk
# #         if current_chunk:
# #             chunks.append({
# #                 "chunk_id": chunk_id,
# #                 "type": "text",
# #                 "content": current_chunk.strip(),
# #                 "source": str(markdown_file)
# #             })
        
# #         # Save to JSON
# #         output_file = Path(output_path)
# #         output_file.parent.mkdir(parents=True, exist_ok=True)
        
# #         with open(output_file, 'w', encoding='utf-8') as f:
# #             json.dump(chunks, f, indent=2, ensure_ascii=False)
        
# #         logger.info(f"Created {len(chunks)} overlapping chunks, saved to {output_path}")
# #         return chunks


# # # def create_overlapping_chunks_from_mineru(
# # #     markdown_path: str,
# # #     output_path: str,
# # #     chunk_size: int = 1000,
# # #     overlap: int = 250
# # # ) -> List[Dict]:
# # #     """Create overlapping chunks from MinerU markdown."""
    
# # #     chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
# # #     chunks = chunker.chunk_markdown(markdown_path, output_path)
    
# # #     # Verify if Shareholding Pattern is intact
# # #     for chunk in chunks:
# # #         content = chunk["content"]
# # #         if "Shareholding Pattern" in content:
# # #             if "Mutual Funds" in content:
# # #                 logger.info(f"✅ Chunk {chunk['chunk_id']}: Shareholding Pattern + table intact")
# # #             else:
# # #                 logger.warning(f"⚠️ Chunk {chunk['chunk_id']}: Shareholding Pattern heading without table")
    
# # #     return chunks
# # def create_overlapping_chunks_from_mineru(
# #     markdown_path: str,
# #     output_path: str,
# #     chunk_size: int = 1000,
# #     overlap: int = 250
# # ) -> List[Dict]:
# #     """Create overlapping chunks from MinerU markdown."""
# #     chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
# #     return chunker.chunk_markdown(markdown_path, output_path)


# # if __name__ == "__main__":
# #     # Find markdown file
# #     markdown_paths = [
# #         "outputs/sample_digital1/auto/sample_digital1.md",
# #         "outputs/sample_digital1/auto/content.md",
# #     ]
    
# #     markdown_path = None
# #     for path in markdown_paths:
# #         if Path(path).exists():
# #             markdown_path = path
# #             break
    
# #     if markdown_path:
# #         output_path = "outputs/sample_digital1_chunks_overlap.json"
# #         chunks = create_overlapping_chunks_from_mineru(markdown_path, output_path)
# #         print(f"\nCreated {len(chunks)} chunks")
# #     else:
# #         print("No markdown file found. Run MinerU first.")

# """
# Lightweight overlap chunker - no merging, just overlapping chunks.
# Memory efficient for 8GB RAM.
# DYNAMIC VERSION - works with any filename.
# """

# import re
# import json
# from pathlib import Path
# from typing import List, Dict
# import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class OverlapChunker:
#     """
#     Simple overlapping chunker.
#     Creates overlapping chunks to preserve context across boundaries.
#     """
    
#     def __init__(self, chunk_size: int = 1000, overlap: int = 250):
#         self.chunk_size = chunk_size
#         self.overlap = overlap
#         logger.info(f"OverlapChunker: size={chunk_size}, overlap={overlap}")
    
#     def chunk_markdown(self, markdown_path: str, output_path: str) -> List[Dict]:
#         """Create overlapping chunks from markdown file."""
        
#         markdown_file = Path(markdown_path)
#         if not markdown_file.exists():
#             logger.error(f"Markdown file not found: {markdown_path}")
#             return []
        
#         with open(markdown_file, 'r', encoding='utf-8') as f:
#             content = f.read()
        
#         if not content.strip():
#             logger.error("Markdown file is empty")
#             return []
        
#         # Split by double newlines (paragraph boundaries)
#         paragraphs = re.split(r'\n\s*\n', content)
        
#         chunks = []
#         current_chunk = ""
#         chunk_id = 0
        
#         for para in paragraphs:
#             para = para.strip()
#             if not para:
#                 continue
            
#             # If adding this paragraph exceeds chunk size, save current chunk
#             if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
#                 chunks.append({
#                     "chunk_id": chunk_id,
#                     "type": "text",
#                     "content": current_chunk.strip(),
#                     "source": str(markdown_file)
#                 })
#                 chunk_id += 1
                
#                 # Keep overlap from previous chunk
#                 if self.overlap > 0 and len(current_chunk) > self.overlap:
#                     overlap_text = current_chunk[-self.overlap:]
#                     current_chunk = overlap_text + "\n\n" + para
#                 else:
#                     current_chunk = para
#             else:
#                 if current_chunk:
#                     current_chunk += "\n\n" + para
#                 else:
#                     current_chunk = para
        
#         # Add last chunk
#         if current_chunk:
#             chunks.append({
#                 "chunk_id": chunk_id,
#                 "type": "text",
#                 "content": current_chunk.strip(),
#                 "source": str(markdown_file)
#             })
        
#         # Save to JSON
#         output_file = Path(output_path)
#         output_file.parent.mkdir(parents=True, exist_ok=True)
        
#         with open(output_file, 'w', encoding='utf-8') as f:
#             json.dump(chunks, f, indent=2, ensure_ascii=False)
        
#         logger.info(f"Created {len(chunks)} overlapping chunks, saved to {output_path}")
#         return chunks


# def create_overlapping_chunks_from_mineru(
#     markdown_path: str,
#     output_path: str,
#     chunk_size: int = 1000,
#     overlap: int = 250
# ) -> List[Dict]:
#     """
#     Create overlapping chunks from MinerU markdown.
#     NO HARDCODED FILENAMES - uses the provided path directly.
#     """
#     chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
#     chunks = chunker.chunk_markdown(markdown_path, output_path)
    
#     # Verify if Shareholding Pattern is intact (only for info, not required)
#     for chunk in chunks:
#         content = chunk["content"]
#         if "Shareholding Pattern" in content:
#             if "Mutual Funds" in content:
#                 logger.info(f"✅ Chunk {chunk['chunk_id']}: Shareholding Pattern + table intact")
#             else:
#                 logger.debug(f"Chunk {chunk['chunk_id']}: Shareholding Pattern heading without table")
    
#     return chunks


# def find_markdown_file(directory: Path) -> Path:
#     """
#     DYNAMIC FUNCTION: Find any markdown file in the directory tree.
#     This is the key fix - no hardcoded filenames!
#     """
#     if not directory.exists():
#         raise FileNotFoundError(f"Directory not found: {directory}")
    
#     # Search for any .md file
#     md_files = list(directory.rglob("*.md"))
    
#     if not md_files:
#         raise FileNotFoundError(f"No markdown file found in {directory}")
    
#     # Return the largest one (likely the main content)
#     largest = max(md_files, key=lambda x: x.stat().st_size)
#     logger.info(f"Found markdown file: {largest}")
#     return largest


# if __name__ == "__main__":
#     import sys
    
#     # Dynamic discovery - don't hardcode!
#     base_dir = Path("processed_docs")
    
#     # Find the most recent document directory
#     doc_dirs = [d for d in base_dir.iterdir() if d.is_dir()]
    
#     if not doc_dirs:
#         print("No processed documents found")
#         sys.exit(1)
    
#     # Get the most recent directory
#     latest_doc = max(doc_dirs, key=lambda x: x.stat().st_mtime)
#     print(f"Latest document: {latest_doc.name}")
    
#     # Dynamically find the markdown file
#     try:
#         markdown_file = find_markdown_file(latest_doc)
#         print(f"Found: {markdown_file}")
        
#         output_path = latest_doc / f"{latest_doc.name}_chunks.json"
#         chunks = create_overlapping_chunks_from_mineru(str(markdown_file), str(output_path))
        
#         print(f"\nCreated {len(chunks)} chunks")
#         print(f"Saved to: {output_path}")
        
#     except FileNotFoundError as e:
#         print(f"Error: {e}")

"""
Lightweight overlap chunker - no merging, just overlapping chunks.
Memory efficient for 8GB RAM.
NO HARDCODED PATHS - purely functional.
"""

import re
import json
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class OverlapChunker:
    """
    Simple overlapping chunker.
    Creates overlapping chunks to preserve context across boundaries.
    """
    
    def __init__(self, chunk_size: int = 1000, overlap: int = 250):
        self.chunk_size = chunk_size
        self.overlap = overlap
        logger.info(f"OverlapChunker: size={chunk_size}, overlap={overlap}")
    
    def chunk_markdown(self, markdown_path: str, output_path: str) -> List[Dict]:
        """Create overlapping chunks from markdown file."""
        
        markdown_file = Path(markdown_path)
        if not markdown_file.exists():
            logger.error(f"Markdown file not found: {markdown_path}")
            return []
        
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if not content.strip():
            logger.error("Markdown file is empty")
            return []
        
        # Split by double newlines (paragraph boundaries)
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        current_chunk = ""
        chunk_id = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # If adding this paragraph exceeds chunk size, save current chunk
            if len(current_chunk) + len(para) > self.chunk_size and current_chunk:
                chunks.append({
                    "chunk_id": chunk_id,
                    "type": "text",
                    "content": current_chunk.strip(),
                    "source": str(markdown_file)
                })
                chunk_id += 1
                
                # Keep overlap from previous chunk
                if self.overlap > 0 and len(current_chunk) > self.overlap:
                    overlap_text = current_chunk[-self.overlap:]
                    current_chunk = overlap_text + "\n\n" + para
                else:
                    current_chunk = para
            else:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add last chunk
        if current_chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "type": "text",
                "content": current_chunk.strip(),
                "source": str(markdown_file)
            })
        
        # Save to JSON
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created {len(chunks)} overlapping chunks, saved to {output_path}")
        return chunks


def create_overlapping_chunks_from_mineru(
    markdown_path: str,
    output_path: str,
    chunk_size: int = 1000,
    overlap: int = 250
) -> List[Dict]:
    """
    Create overlapping chunks from MinerU markdown.
    Uses the provided path directly - NO HARDCODING.
    """
    logger.info(f"Creating chunks from: {markdown_path}")
    chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
    return chunker.chunk_markdown(markdown_path, output_path)


# No __main__ block that could cause issues - remove it completely