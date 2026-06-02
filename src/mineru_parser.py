"""
Parse MinerU output for RAG ingestion.
Handles markdown text, HTML tables, and chart images.
MinerU stores outputs in: outputs/{pdf_name}/auto/
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def parse_mineru_output(pdf_path: str, output_dir: str = "outputs") -> Dict:
    """
    Parse MinerU-generated files into structured format for RAG.
    
    Args:
        pdf_path: Original PDF path (used to find output folder)
        output_dir: Directory containing MinerU outputs
    
    Returns:
        Dictionary with parsed content blocks
    """
    base_name = Path(pdf_path).stem
    # Correct path: outputs/{pdf_name}/auto/
    mineru_folder = Path(output_dir) / base_name / "auto"
    
    if not mineru_folder.exists():
        # Try alternative location (without auto subfolder)
        mineru_folder = Path(output_dir) / base_name
        if not mineru_folder.exists():
            raise FileNotFoundError(f"MinerU output folder not found: {mineru_folder}")
    
    logger.info(f"Reading MinerU output from: {mineru_folder}")
    
    result = {
        "source": pdf_path,
        "text_blocks": [],
        "table_blocks": [],
        "image_blocks": [],
        "full_markdown": "",
        "output_folder": str(mineru_folder)
    }
    
    # 1. Load markdown file (named as {pdf_name}.md)
    md_path = mineru_folder / f"{base_name}.md"
    if not md_path.exists():
        # Try alternative naming (content.md)
        md_path = mineru_folder / "content.md"
    
    if md_path.exists():
        markdown = md_path.read_text(encoding='utf-8')
        result["full_markdown"] = markdown
        result["text_blocks"] = extract_text_blocks(markdown)
        logger.info(f"Loaded markdown: {len(markdown)} characters, {len(result['text_blocks'])} text blocks")
    else:
        logger.warning(f"Markdown file not found: {md_path}")
    
    # 2. Load content JSON for tables and images
    json_path = mineru_folder / f"{base_name}.json"
    if not json_path.exists():
        json_path = mineru_folder / "content_list.json"
    
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        result["table_blocks"] = extract_table_blocks(content)
        result["image_blocks"] = extract_image_blocks(content, mineru_folder)
        logger.info(f"Found {len(result['table_blocks'])} tables, {len(result['image_blocks'])} images")
    else:
        logger.warning(f"JSON file not found: {json_path}")
    
    return result


def extract_text_blocks(markdown: str) -> List[Dict]:
    """
    Extract text blocks from markdown, preserving headers and paragraphs.
    """
    blocks = []
    lines = markdown.split('\n')
    current_block = []
    
    for line in lines:
        if line.strip():
            current_block.append(line)
        else:
            if current_block:
                block_text = '\n'.join(current_block)
                block_type = "header" if re.match(r'^#{1,6}\s', block_text) else "paragraph"
                blocks.append({
                    "type": block_type,
                    "content": block_text,
                    "length": len(block_text)
                })
                current_block = []
    
    # Add last block
    if current_block:
        block_text = '\n'.join(current_block)
        block_type = "header" if re.match(r'^#{1,6}\s', block_text) else "paragraph"
        blocks.append({
            "type": block_type,
            "content": block_text,
            "length": len(block_text)
        })
    
    return blocks


def extract_table_blocks(content: List) -> List[Dict]:
    """
    Extract tables from MinerU content JSON.
    Each table includes HTML and optional DataFrame.
    """
    tables = []
    
    for item in content:
        # Check different possible type identifiers
        item_type = item.get("type", "")
        
        if item_type == "table" or "table" in item_type.lower():
            table_html = item.get("text", "") or item.get("html", "")
            
            if not table_html:
                continue
            
            table_block = {
                "type": "table",
                "html": table_html,
                "page_num": item.get("page_num", item.get("page_idx", 0)) + 1,
                "caption": item.get("caption", "")
            }
            
            # Convert HTML to markdown table for RAG context
            table_block["markdown"] = html_table_to_markdown(table_html)
            
            tables.append(table_block)
            logger.info(f"Extracted table from page {table_block['page_num']}")
    
    return tables


def html_table_to_markdown(html: str) -> str:
    """
    Convert HTML table to markdown format for RAG context.
    """
    try:
        import pandas as pd
        dfs = pd.read_html(html)
        if dfs:
            return dfs[0].to_markdown()
    except Exception as e:
        logger.debug(f"Pandas HTML parsing failed: {e}")
    
    # Fallback: basic extraction
    rows = re.findall(r'<td>(.*?)</tr>', html, re.DOTALL)
    markdown_rows = []
    
    for row in rows:
        cells = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', row, re.DOTALL)
        clean_cells = [re.sub(r'<[^>]+>', '', cell).strip() for cell in cells]
        if clean_cells:
            markdown_rows.append('| ' + ' | '.join(clean_cells) + ' |')
    
    if markdown_rows:
        # Add separator row
        num_cols = markdown_rows[0].count('|') - 1
        if num_cols > 0:
            separator = '|' + '|'.join([' --- '] * num_cols) + '|'
            markdown_rows.insert(1, separator)
        return '\n'.join(markdown_rows)
    
    return html


def extract_image_blocks(content: List, mineru_folder: Path) -> List[Dict]:
    """
    Extract image references from MinerU content.
    Returns paths to extracted JPG images.
    """
    images = []
    images_folder = mineru_folder / "images"
    
    for item in content:
        item_type = item.get("type", "")
        
        if item_type == "image" or "figure" in item_type.lower():
            img_filename = item.get("text", "") or item.get("img_path", "")
            
            # Handle different path formats
            if img_filename:
                img_full_path = images_folder / Path(img_filename).name
                if not img_full_path.exists():
                    img_full_path = mineru_folder / img_filename
            else:
                img_full_path = None
            
            image_block = {
                "type": "image",
                "path": str(img_full_path) if img_full_path and img_full_path.exists() else None,
                "filename": img_filename,
                "page_num": item.get("page_num", item.get("page_idx", 0)) + 1,
                "caption": item.get("caption", "")
            }
            
            if image_block["path"]:
                images.append(image_block)
                logger.info(f"Extracted image from page {image_block['page_num']}: {img_filename}")
    
    return images


# def create_chunks_for_rag(parsed_content: Dict, chunk_size: int = 1000) -> List[Dict]:
#     """
#     Create RAG-ready chunks from parsed MinerU output.
#     Tables and images are preserved as whole chunks.
#     """
#     chunks = []
#     chunk_id = 0
    
#     # 1. Add text chunks (split by paragraphs/headers)
#     current_chunk = []
#     current_length = 0
    
#     for block in parsed_content["text_blocks"]:
#         block_length = block["length"]
        
#         if current_length + block_length > chunk_size and current_chunk:
#             chunks.append({
#                 "chunk_id": chunk_id,
#                 "type": "text",
#                 "content": "\n\n".join(current_chunk),
#                 "source": parsed_content["source"]
#             })
#             chunk_id += 1
#             current_chunk = []
#             current_length = 0
        
#         current_chunk.append(block["content"])
#         current_length += block_length
    
#     if current_chunk:
#         chunks.append({
#             "chunk_id": chunk_id,
#             "type": "text",
#             "content": "\n\n".join(current_chunk),
#             "source": parsed_content["source"]
#         })
#         chunk_id += 1
    
#     # 2. Add tables as individual chunks
#     for table in parsed_content["table_blocks"]:
#         chunks.append({
#             "chunk_id": chunk_id,
#             "type": "table",
#             "content": table["markdown"],
#             "html": table["html"],
#             "source": parsed_content["source"],
#             "page_num": table.get("page_num")
#         })
#         chunk_id += 1
    
#     # 3. Add images as individual chunks
#     for image in parsed_content["image_blocks"]:
#         image_desc = image.get("caption", f"Chart: {image['filename']}")
#         chunks.append({
#             "chunk_id": chunk_id,
#             "type": "image",
#             "content": image_desc,
#             "image_path": image["path"],
#             "source": parsed_content["source"],
#             "page_num": image.get("page_num")
#         })
#         chunk_id += 1
    
#     logger.info(f"Created {len(chunks)} RAG chunks")
#     return chunks

def create_chunks_for_rag(parsed_content: Dict, chunk_size: int = 1000) -> List[Dict]:
    """
    Create RAG-ready chunks with proper context for tables.
    """
    chunks = []
    chunk_id = 0
    
    # 1. Add text chunks
    current_chunk = []
    current_length = 0
    
    for block in parsed_content["text_blocks"]:
        block_length = block["length"]
        
        if current_length + block_length > chunk_size and current_chunk:
            chunks.append({
                "chunk_id": chunk_id,
                "type": "text",
                "content": "\n\n".join(current_chunk),
                "source": parsed_content["source"]
            })
            chunk_id += 1
            current_chunk = []
            current_length = 0
        
        current_chunk.append(block["content"])
        current_length += block_length
    
    if current_chunk:
        chunks.append({
            "chunk_id": chunk_id,
            "type": "text",
            "content": "\n\n".join(current_chunk),
            "source": parsed_content["source"]
        })
        chunk_id += 1
    
    # 2. Add tables with rich context
    for table in parsed_content["table_blocks"]:
        # Build rich content that includes context
        rich_content = f"{table.get('context_before', '')}\n\n"
        rich_content += f"TABLE DATA:\n{table['markdown']}\n\n"
        rich_content += f"Table description: {table.get('description', '')}\n\n"
        rich_content += f"Caption: {table.get('caption', '')}\n\n"
        rich_content += f"{table.get('context_after', '')}"
        
        chunks.append({
            "chunk_id": chunk_id,
            "type": "table",
            "content": rich_content,  # Rich content for embedding/search
            "content_for_llm": rich_content,  # Same for LLM
            "html": table["html"],  # Original HTML for precise rendering
            "markdown": table["markdown"],
            "description": table.get("description", ""),
            "source": parsed_content["source"],
            "page_num": table.get("page_num")
        })
        chunk_id += 1
    
    # 3. Add images
    for image in parsed_content["image_blocks"]:
        image_desc = image.get("caption", f"Chart: {image['filename']}")
        chunks.append({
            "chunk_id": chunk_id,
            "type": "image",
            "content": image_desc,
            "image_path": image["path"],
            "source": parsed_content["source"],
            "page_num": image.get("page_num")
        })
        chunk_id += 1
    
    logger.info(f"Created {len(chunks)} RAG chunks")
    return chunks
# def list_mineru_outputs(output_dir: str = "outputs") -> List[Dict]:
#     """
#     List all MinerU-processed documents in the output directory.
#     """
#     output_path = Path(output_dir)
#     results = []
    
#     for pdf_folder in output_path.iterdir():
#         if pdf_folder.is_dir():
#             auto_folder = pdf_folder / "auto"
#             if auto_folder.exists():
#                 md_file = auto_folder / f"{pdf_folder.name}.md"
#                 if not md_file.exists():
#                     md_file = auto_folder / "content.md"
                
#                 results.append({
#                     "document_name": pdf_folder.name,
#                     "folder": str(auto_folder),
#                     "has_markdown": md_file.exists(),
#                     "has_json": (auto_folder / f"{pdf_folder.name}.json").exists() or (auto_folder / "content_list.json").exists(),
#                     "images_folder": (auto_folder / "images").exists()
#                 })
    
#     return results
def list_mineru_outputs(output_dir: str = "outputs") -> List[Dict]:
    """
    List all MinerU-processed documents in the output directory.
    """
    output_path = Path(output_dir)
    results = []
    
    for pdf_folder in output_path.iterdir():
        if pdf_folder.is_dir():
            auto_folder = pdf_folder / "auto"
            if auto_folder.exists():
                md_file = auto_folder / f"{pdf_folder.name}.md"
                if not md_file.exists():
                    md_file = auto_folder / "content.md"
                
                results.append({
                    "document_name": pdf_folder.name,
                    "folder": str(auto_folder),
                    "has_markdown": md_file.exists(),
                    "has_json": (auto_folder / f"{pdf_folder.name}.json").exists() or (auto_folder / "content_list.json").exists(),
                    "has_images": (auto_folder / "images").exists()  # Add this missing key
                })
    
    return results

def extract_tables_with_context(content: List, markdown: str) -> List[Dict]:
    """
    Extract tables with their surrounding context (headings, captions).
    """
    tables = []
    markdown_lines = markdown.split('\n')
    
    for i, item in enumerate(content):
        if item.get("type") == "table":
            table_html = item.get("text", "")
            page_num = item.get("page_num", 0)
            
            # Find surrounding context from markdown
            context_before = ""
            context_after = ""
            
            # Look for heading/caption in markdown near this table
            # Tables in MinerU markdown are represented as HTML blocks
            for j, line in enumerate(markdown_lines):
                if '<table' in line or '<table>' in line:
                    # Found table in markdown, look backwards for headings
                    for k in range(max(0, j-10), j):
                        prev_line = markdown_lines[k].strip()
                        if prev_line.startswith('#') or 'caption' in prev_line.lower():
                            context_before = prev_line
                            break
                    
                    # Look forward for caption
                    for k in range(j+1, min(len(markdown_lines), j+5)):
                        next_line = markdown_lines[k].strip()
                        if 'caption' in next_line.lower() or next_line:
                            context_after = next_line
                            break
                    break
            
            table_block = {
                "type": "table",
                "html": table_html,
                "page_num": page_num,
                "context_before": context_before,
                "context_after": context_after,
                "caption": item.get("caption", context_before or context_after),
                "markdown": html_table_to_markdown(table_html),
                "description": generate_table_description(table_html, context_before)
            }
            
            tables.append(table_block)
    
    return tables


def generate_table_description(html: str, context: str) -> str:
    """
    Generate a natural language description of the table.
    This helps the LLM understand what the table contains.
    """
    try:
        import pandas as pd
        dfs = pd.read_html(html)
        if dfs:
            df = dfs[0]
            description = f"Table with {df.shape[0]} rows and {df.shape[1]} columns. "
            description += f"Columns: {', '.join(df.columns.astype(str)[:10])}. "
            
            # Add context if available
            if context:
                description += f"This table is about: {context[:200]}. "
            
            # Add data summary for numeric columns
            numeric_cols = df.select_dtypes(include=['number']).columns
            if len(numeric_cols) > 0:
                description += f"Numeric columns: {', '.join(numeric_cols[:5])}. "
            
            return description
    except:
        pass
    
    return f"HTML table with context: {context[:100]}" if context else "HTML table extracted from document"


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
        
        # First, list available MinerU outputs
        print("\n===== AVAILABLE MINERU OUTPUTS =====")
        outputs = list_mineru_outputs(output_dir)
        for out in outputs:
            print(f"\nDocument: {out['document_name']}")
            print(f"  Folder: {out['folder']}")
            print(f"  Markdown: {out['has_markdown']}")
            print(f"  JSON: {out['has_json']}")
            print(f"  Images: {out['has_images']}")
        
        # Parse the specific PDF
        print(f"\n===== PARSING: {pdf_file} =====")
        parsed = parse_mineru_output(pdf_file, output_dir)
        
        print(f"\n===== PARSED CONTENT =====")
        print(f"Output folder: {parsed['output_folder']}")
        print(f"Text blocks: {len(parsed['text_blocks'])}")
        print(f"Table blocks: {len(parsed['table_blocks'])}")
        print(f"Image blocks: {len(parsed['image_blocks'])}")
        print(f"Markdown length: {len(parsed['full_markdown'])} chars")
        
        # Create RAG chunks
        chunks = create_chunks_for_rag(parsed)
        
        print(f"\n===== RAG CHUNKS =====")
        print(f"Total chunks: {len(chunks)}")
        
        # Show chunk types
        chunk_types = {}
        for chunk in chunks:
            chunk_types[chunk['type']] = chunk_types.get(chunk['type'], 0) + 1
        print(f"Chunk types: {chunk_types}")
        
        # Show first few chunks
        for chunk in chunks[:3]:
            print(f"\nChunk {chunk['chunk_id']} ({chunk['type']}):")
            print(f"  Content preview: {chunk['content'][:150]}...")
        
        # Save chunks to file
        chunks_path = Path(output_dir) / f"{Path(pdf_file).stem}_chunks.json"
        with open(chunks_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        print(f"\nChunks saved to: {chunks_path}")
        
        # Also save parsed content summary
        summary_path = Path(output_dir) / f"{Path(pdf_file).stem}_summary.json"
        summary = {
            "source": parsed["source"],
            "output_folder": parsed["output_folder"],
            "text_blocks_count": len(parsed["text_blocks"]),
            "table_blocks_count": len(parsed["table_blocks"]),
            "image_blocks_count": len(parsed["image_blocks"]),
            "markdown_length": len(parsed["full_markdown"]),
            "rag_chunks_count": len(chunks),
            "rag_chunks_by_type": chunk_types
        }
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved to: {summary_path}")
        
    else:
        print("Usage: python mineru_parser.py <path_to_pdf> [output_dir]")