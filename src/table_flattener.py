"""
Table processor - Keeps HTML tables intact instead of flattening.
HTML tables preserve column relationships better than flattened text.
"""

import re
from pathlib import Path
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def process_tables_in_markdown(
    enhanced_md_path: str, 
    output_path: str,
    add_headers: bool = True
):
    """
    Process markdown: Keep HTML tables intact, add descriptive headers.
    """
    with open(enhanced_md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all HTML tables
    table_pattern = r'<table.*?</table>'
    tables = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
    
    logger.info(f"Found {len(tables)} HTML tables")
    
    # For each table, add a descriptive header above it
    for i, html_table in enumerate(tables):
        # Add a header that describes the table context
        header = f"\n\n<!-- Table {i+1}: Financial Data -->\n## Table {i+1}: Financial Summary\n\n"
        
        # Replace the table with header + table
        content = content.replace(html_table, header + html_table)
        logger.info(f"Added header to table {i+1}")
    
    # Save processed markdown
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    logger.info(f"Processed markdown saved: {output_path}")
    return output_path


# def create_chunks_from_markdown(
#     markdown_path: str,
#     output_chunks_path: str,
#     chunk_size: int = 2000,
#     overlap: int = 300
# ) -> List[Dict]:
#     """
#     Create chunks from markdown, keeping tables whole.
#     Uses larger chunk size to ensure tables fit.
#     """
#     from overlap_chunker import OverlapChunker
    
#     # Use a custom chunker with larger size
#     chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
#     chunks = chunker.chunk_markdown(markdown_path, output_chunks_path)
    
#     # Verify tables are intact
#     for chunk in chunks:
#         if "<table" in chunk["content"] and "</table" in chunk["content"]:
#             # Check if the table is complete
#             if chunk["content"].count("<table") == chunk["content"].count("</table"):
#                 chunk["type"] = "table"
#                 logger.info(f"Chunk {chunk['chunk_id']}: Complete HTML table preserved")
    
#     logger.info(f"Created {len(chunks)} chunks with HTML tables preserved")
#     return chunks

def create_chunks_from_markdown(
    markdown_path: str,
    output_chunks_path: str,
    chunk_size: int = 2000,
    overlap: int = 300
) -> List[Dict]:
    """
    Create chunks with tables as unbreakable units.
    """
    from overlap_chunker import OverlapChunker
    
    # Use a custom chunker with larger size
    chunker = OverlapChunker(chunk_size=chunk_size, overlap=overlap)
    
    # Read markdown
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Identify table boundaries
    table_pattern = r'<table.*?</table>'
    table_matches = list(re.finditer(table_pattern, content, re.DOTALL | re.IGNORECASE))
    
    # Create segments that don't split tables
    segments = []
    last_end = 0
    
    for match in table_matches:
        # Add text before table
        if match.start() > last_end:
            segments.append(content[last_end:match.start()])
        # Add table as a whole segment
        segments.append(match.group())
        last_end = match.end()
    
    # Add remaining text
    if last_end < len(content):
        segments.append(content[last_end:])
    
    # Chunk each segment, but keep tables whole
    chunks = []
    chunk_id = 0
    
    for segment in segments:
        if segment.startswith('<table'):
            # Table segment - keep as one chunk
            chunks.append({
                "chunk_id": chunk_id,
                "type": "table",
                "content": segment,
                "source": markdown_path
            })
            chunk_id += 1
        else:
            # Text segment - apply normal chunking
            text_chunks = chunker.chunk_markdown(segment, None)
            for tc in text_chunks:
                tc["chunk_id"] = chunk_id
                chunk_id += 1
                chunks.append(tc)
    
    # Save chunks
    with open(output_chunks_path, 'w', encoding='utf-8') as f:
        json.dump(chunks, f, indent=2)
    
    logger.info(f"Created {len(chunks)} chunks with unbroken tables")
    return chunks


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python table_flattener.py <doc_name>")
        print("Example: python table_flattener.py sample2")
        sys.exit(1)
    
    doc_name = sys.argv[1]
    
    enhanced_md = f"processed_docs/{doc_name}/{doc_name}_enhanced.md"
    output_md = f"processed_docs/{doc_name}/{doc_name}_final.md"
    output_chunks = f"processed_docs/{doc_name}/{doc_name}_chunks_final.json"
    
    # Check if enhanced markdown exists
    if not Path(enhanced_md).exists():
        print(f"Error: Enhanced markdown not found: {enhanced_md}")
        sys.exit(1)
    
    print(f"Processing: {doc_name}")
    print(f"Enhanced markdown: {enhanced_md}")
    
    # Step 1: Process tables (add headers, keep HTML intact)
    process_tables_in_markdown(enhanced_md, output_md)
    
    # Step 2: Create chunks with larger size to keep tables whole
    chunks = create_chunks_from_markdown(
        output_md, 
        output_chunks,
        chunk_size=2000,  # Larger to fit tables
        overlap=300
    )
    
    print(f"\n✅ Created {len(chunks)} chunks")
    print(f"Chunks saved to: {output_chunks}")