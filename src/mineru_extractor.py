"""
MinerU document extractor for enterprise RAG system.
Optimized for CPU with 8GB RAM.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def extract_with_mineru(
    pdf_path: str, 
    output_dir: str = "outputs",
    backend: str = "pipeline"
) -> Dict:
    """
    Extract content from PDF using MinerU.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory for outputs
        backend: 'pipeline' (CPU) or 'vlm' (GPU required)
    
    Returns:
        Dictionary with extracted content
    """
    from magic_pdf.pipe.UNIPipe import UNIPipe
    from magic_pdf.rw.DiskReaderWriter import DiskReaderWriter
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Read PDF
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
    
    # Create output writer
    local_writer = DiskReaderWriter(str(output_path))
    
    # Initialize MinerU pipe
    pipe = UNIPipe(
        pdf_bytes,
        local_writer,
        {
            "model-dir": str(output_path / "models"),
            "device": "cpu",  # Force CPU for 8GB RAM
            "backend": backend,
            "table_enable": True,
            "formula_enable": True,
        }
    )
    
    # Parse document
    logger.info(f"Processing: {pdf_path}")
    pipe.pipe_classify()
    pipe.pipe_parse()
    
    # Get results
    md_content = pipe.get_markdown()
    content_list = pipe.get_content_list()
    
    # Extract tables
    tables = extract_tables_from_mineru(content_list)
    
    # Save outputs
    base_name = Path(pdf_path).stem
    md_path = output_path / f"{base_name}.md"
    md_path.write_text(md_content, encoding='utf-8')
    
    json_path = output_path / f"{base_name}.json"
    json_path.write_text(json.dumps(content_list, ensure_ascii=False, indent=2), encoding='utf-8')
    
    logger.info(f"Markdown saved to: {md_path}")
    logger.info(f"Tables found: {len(tables)}")
    
    return {
        "markdown": md_content,
        "tables": tables,
        "content_list": content_list,
        "output_files": {
            "markdown": str(md_path),
            "json": str(json_path)
        }
    }


def extract_tables_from_mineru(content_list: List) -> List[Dict]:
    """
    Extract table data from MinerU content list.
    """
    tables = []
    
    for item in content_list:
        if item.get("type") == "table":
            table_data = {
                "page_num": item.get("page_num"),
                "html": item.get("text", ""),  # Tables in HTML format
                "caption": item.get("caption", "")
            }
            
            # Try to parse HTML to pandas DataFrame
            try:
                import pandas as pd
                dfs = pd.read_html(table_data["html"])
                if dfs:
                    table_data["dataframe"] = dfs[0].to_dict(orient="records")
                    table_data["shape"] = list(dfs[0].shape)
            except:
                table_data["dataframe"] = None
                table_data["shape"] = None
            
            tables.append(table_data)
            logger.info(f"Table on page {table_data['page_num']}: {table_data['shape']}")
    
    return tables


def extract_with_mineru_cli(pdf_path: str, output_dir: str = "outputs"):
    """
    Alternative: Use subprocess to call MinerU CLI.
    More stable on Windows.
    """
    import subprocess
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    cmd = [
        "mineru",
        "-p", pdf_path,
        "-o", str(output_path),
        "-b", "pipeline"
    ]
    
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        logger.info("Extraction successful")
        # MinerU creates a folder with PDF name
        pdf_name = Path(pdf_path).stem
        md_path = output_path / pdf_name / f"{pdf_name}.md"
        
        if md_path.exists():
            return {
                "success": True,
                "markdown_path": str(md_path),
                "markdown": md_path.read_text(encoding='utf-8')
            }
    
    logger.error(f"Extraction failed: {result.stderr}")
    return {"success": False, "error": result.stderr}


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
        
        # Try CLI method first (more reliable on Windows)
        result = extract_with_mineru_cli(pdf_file, output_dir)
        
        if result["success"]:
            print(f"\n===== EXTRACTION SUCCESS =====")
            print(f"Markdown saved to: {result['markdown_path']}")
            print(f"Markdown length: {len(result['markdown'])} characters")
        else:
            print(f"\n===== EXTRACTION FAILED =====")
            print(f"Error: {result.get('error', 'Unknown error')}")
    else:
        print("Usage: python mineru_extractor.py <path_to_pdf> [output_dir]")