"""
Memory-efficient chunk optimizer.
Processes content in streaming mode to avoid RAM spikes.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Generator
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def stream_markdown_in_chunks(md_path: str, chunk_size: int = 50000):
    """
    Stream markdown file in small memory chunks.
    """
    with open(md_path, 'r', encoding='utf-8') as f:
        buffer = ""
        while True:
            chunk = f.read(chunk_size)
            if not chunk and not buffer:
                break
            
            buffer += chunk
            
            # Process complete sections (split by double newline)
            while '\n\n' in buffer:
                section_end = buffer.find('\n\n')
                if section_end == -1:
                    break
                
                section = buffer[:section_end]
                buffer = buffer[section_end + 2:]
                
                if section.strip():
                    yield section
            
            if not chunk and buffer:
                yield buffer
                buffer = ""


def extract_tables_preserve(content: str) -> List[str]:
    """
    Extract tables while preserving their structure.
    Returns list of text segments with tables kept intact.
    """
    segments = []
    
    # Find all table boundaries
    table_pattern = r'(<table.*??</table>|<div class="table".*?</div>)'
    
    last_end = 0
    
    for match in re.finditer(table_pattern, content, re.DOTALL | re.IGNORECASE):
        # Add text before table
        if match.start() > last_end:
            text_before = content[last_end:match.start()]
            if text_before.strip():
                segments.append(('text', text_before))
        
        # Add the table
        table_content = match.group()
        if table_content.strip():
            segments.append(('table', table_content))
        
        last_end = match.end()
    
    # Add remaining text
    if last_end < len(content):
        remaining = content[last_end:]
        if remaining.strip():
            segments.append(('text', remaining))
    
    return segments


def create_overlapping_chunks(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Create overlapping chunks from text.
    Memory efficient - processes one chunk at a time.
    """
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = min(start + chunk_size, len(text))
        
        # Try to break at sentence boundary
        if end < len(text):
            for sep in ['. ', '? ', '! ', '\n\n', '\n']:
                last_sep = text.rfind(sep, start, end)
                if last_sep > start:
                    end = last_sep + len(sep)
                    break
        
        chunks.append(text[start:end])
        start = end - overlap
    
    return chunks


def process_markdown_efficiently(
    md_path: str,
    output_chunks_path: str,
    chunk_size: int = 1000,
    overlap: int = 200
) -> List[Dict]:
    """
    Process markdown file efficiently without loading everything into RAM.
    """
    all_chunks = []
    chunk_id = 0
    
    logger.info(f"Processing {md_path} in streaming mode...")
    
    # Stream through the markdown file
    for section in stream_markdown_in_chunks(md_path, chunk_size=50000):
        # Split into segments (preserving tables)
        segments = extract_tables_preserve(section)
        
        for seg_type, seg_content in segments:
            if seg_type == 'table':
                # Keep entire table as one chunk
                all_chunks.append({
                    "chunk_id": chunk_id,
                    "type": "table",
                    "content": seg_content,
                    "content_length": len(seg_content)
                })
                chunk_id += 1
                logger.debug(f"Table chunk {chunk_id}: {len(seg_content)} chars")
            
            else:  # text
                # Split text into overlapping chunks
                text_chunks = create_overlapping_chunks(seg_content, chunk_size, overlap)
                for text_chunk in text_chunks:
                    if text_chunk.strip():
                        all_chunks.append({
                            "chunk_id": chunk_id,
                            "type": "text",
                            "content": text_chunk,
                            "content_length": len(text_chunk)
                        })
                        chunk_id += 1
        
        # Log progress
        logger.info(f"Processed section, total chunks so far: {chunk_id}")
    
    # Merge adjacent table chunks that might have been split
    all_chunks = merge_adjacent_tables(all_chunks)
    
    # Save to JSON
    with open(output_chunks_path, 'w', encoding='utf-8') as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved {len(all_chunks)} chunks to {output_chunks_path}")
    
    # Print statistics
    print(f"\n=== CHUNKING STATISTICS ===")
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Text chunks: {len([c for c in all_chunks if c['type'] == 'text'])}")
    print(f"Table chunks: {len([c for c in all_chunks if c['type'] == 'table'])}")
    
    return all_chunks


def merge_adjacent_tables(chunks: List[Dict]) -> List[Dict]:
    """
    Merge adjacent table chunks that might be split.
    """
    if not chunks:
        return chunks
    
    merged = []
    i = 0
    
    while i < len(chunks):
        current = chunks[i]
        
        if current['type'] != 'table':
            merged.append(current)
            i += 1
            continue
        
        # Current is table - check if next chunks continue the same table
        table_content = current['content']
        j = i + 1
        
        while j < len(chunks) and chunks[j]['type'] == 'table':
            # Merge
            table_content += "\n" + chunks[j]['content']
            logger.debug(f"Merged table chunks {i} and {j}")
            j += 1
        
        merged.append({
            "chunk_id": current['chunk_id'],
            "type": "table",
            "content": table_content,
            "content_length": len(table_content)
        })
        
        i = j
    
    # Re-number chunk IDs
    for idx, chunk in enumerate(merged):
        chunk['chunk_id'] = idx
    
    return merged


def verify_shareholding_table(chunks_path: str) -> bool:
    """
    Verify that Shareholding Pattern table is intact in the chunks.
    """
    with open(chunks_path, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    for chunk in chunks:
        content = chunk.get("content", "")
        
        if "Shareholding Pattern" in content:
            if "Mutual Funds" in content:
                print(f"\n✅ Shareholding Pattern table found intact")
                
                # Try to extract Mutual Funds data
                import re
                # Look for Mutual Funds row
                lines = content.split('\n')
                for line in lines:
                    if 'Mutual Funds' in line:
                        print(f"   Found: {line[:200]}")
                        return True
            else:
                print(f"\n⚠️ Shareholding Pattern found but Mutual Funds row missing")
                print(f"   Content preview: {content[:300]}")
    
    print(f"\n❌ Shareholding Pattern table not found intact")
    return False


if __name__ == "__main__":
    import sys
    
    # Paths
    md_path = "outputs/sample_digital1/auto/sample_digital1.md"
    output_chunks = "outputs/sample_digital1_chunks_optimized.json"
    
    # Check if markdown exists
    if not Path(md_path).exists():
        # Try alternative paths
        alternatives = [
            "outputs/sample_digital1/auto/content.md",
            "outputs/sample_digital1/auto/sample_digital1.md",
            "outputs/sample_digital1/auto/sample_digital1_v2.md",
        ]
        
        for alt in alternatives:
            if Path(alt).exists():
                md_path = alt
                print(f"Found markdown at: {md_path}")
                break
        else:
            print(f"Error: Could not find MinerU markdown file")
            print("Please check that MinerU has been run on your PDF")
            sys.exit(1)
    
    # Process efficiently
    try:
        chunks = process_markdown_efficiently(
            md_path,
            output_chunks,
            chunk_size=1000,
            overlap=200
        )
        
        # Verify
        verify_shareholding_table(output_chunks)
        
        print(f"\n✅ Optimized chunks saved to: {output_chunks}")
        print(f"\nNow rebuild vector store with:")
        print(f"  python src/vector_store.py {output_chunks} vector_store_optimized")
        
    except MemoryError:
        print("\n❌ Memory error - reducing chunk size...")
        # Try with smaller chunks
        chunks = process_markdown_efficiently(
            md_path,
            output_chunks,
            chunk_size=800,
            overlap=150
        )
        verify_shareholding_table(output_chunks)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")