"""
Document extraction using Docling.
Unified extraction for text, tables, and layout from complex PDFs.
"""

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions, 
    TableStructureOptions,
    TableFormerMode,
    EasyOcrOptions
)
from docling.datamodel.document import ConversionResult
import pandas as pd
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def configure_pipeline_options(
    do_ocr: bool = True,
    table_mode: str = "accurate",
    num_threads: int = 2
) -> PdfPipelineOptions:
    """
    Configure Docling pipeline options optimized for CPU.
    
    Args:
        do_ocr: Enable OCR for scanned documents
        table_mode: "accurate" or "fast" (accurate handles complex tables better)
        num_threads: CPU threads to use (keep low for 8GB RAM)
    
    Returns:
        Configured PdfPipelineOptions
    """
    pipeline_options = PdfPipelineOptions()
    
    # Core extraction features
    pipeline_options.do_ocr = do_ocr
    pipeline_options.do_table_structure = True
    pipeline_options.table_structure_options = TableStructureOptions(
        mode=TableFormerMode.ACCURATE if table_mode == "accurate" else TableFormerMode.FAST
    )
    
    # OCR configuration for scanned/handwritten content
    if do_ocr:
        pipeline_options.ocr_options = EasyOcrOptions(
            lang=["en"]  # Add more languages if needed
        )
    
    # Limit resources for 8GB RAM
    pipeline_options.accelerator_options.num_threads = num_threads
    
    return pipeline_options


def extract_document(
    pdf_path: str,
    output_dir: Optional[str] = None,
    do_ocr: bool = True,
    table_mode: str = "accurate"
) -> Dict[str, Any]:
    """
    Extract all content from a PDF using Docling.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save outputs (optional)
        do_ocr: Enable OCR for scanned content
        table_mode: "accurate" or "fast"
    
    Returns:
        Dictionary containing extracted text, tables, and metadata
    """
    logger.info(f"Processing document: {pdf_path}")
    
    # Configure pipeline
    pipeline_options = configure_pipeline_options(do_ocr=do_ocr, table_mode=table_mode)
    
    # Create converter
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: pipeline_options
        }
    )
    
    # Convert document
    result = converter.convert(pdf_path)
    
    # Extract content
    extracted = {
        "source": pdf_path,
        "text": extract_text_from_result(result),
        "tables": extract_tables_from_result(result),
        "markdown": result.document.export_to_markdown(),
        "pages": len(result.document.pages) if result.document.pages else 0
    }
    
    # Save outputs if directory provided
    if output_dir:
        save_extraction_results(extracted, output_dir, Path(pdf_path).stem)
    
    logger.info(f"Extraction complete: {len(extracted['tables'])} tables found")
    return extracted


def extract_text_from_result(result: ConversionResult) -> str:
    """
    Extract plain text from Docling conversion result.
    """
    try:
        return result.document.export_to_text()
    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return ""


def extract_tables_from_result(result: ConversionResult) -> List[Dict]:
    """
    Extract tables as structured dictionaries from Docling result.
    
    Each table includes:
    - DataFrame representation
    - HTML/Markdown versions
    - Page number and cell-level metadata
    """
    tables_data = []
    
    try:
        for table_idx, table in enumerate(result.document.tables):
            # Convert to DataFrame (best for structured data)
            df = table.export_to_dataframe()
            
            # Get markdown representation (good for RAG context)
            markdown = table.export_to_markdown()
            
            # Get HTML (preserves complex structure)
            html = table.export_to_html()
            
            tables_data.append({
                "table_index": table_idx + 1,
                "shape": {"rows": df.shape[0], "columns": df.shape[1]},
                "dataframe": df.fillna("").to_dict(orient="records"),
                "columns": df.columns.tolist(),
                "markdown": markdown,
                "html": html,
                "page_number": getattr(table, "page_num", None)
            })
            
            logger.info(f"Table {table_idx+1}: {df.shape[0]} rows x {df.shape[1]} columns")
    
    except Exception as e:
        logger.error(f"Table extraction failed: {e}")
    
    return tables_data


def save_extraction_results(extracted: Dict, output_dir: str, base_name: str) -> None:
    """
    Save extracted results to files.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save text
    text_path = output_path / f"{base_name}_text.txt"
    text_path.write_text(extracted["text"], encoding="utf-8")
    
    # Save markdown (preserves structure)
    md_path = output_path / f"{base_name}.md"
    md_path.write_text(extracted["markdown"], encoding="utf-8")
    
    # Save tables as JSON
    if extracted["tables"]:
        tables_json = output_path / f"{base_name}_tables.json"
        # Convert DataFrames to serializable format
        serializable_tables = []
        for t in extracted["tables"]:
            t_copy = t.copy()
            t_copy["dataframe"] = t_copy["dataframe"]  # Already serializable
            serializable_tables.append(t_copy)
        
        with open(tables_json, "w", encoding="utf-8") as f:
            json.dump(serializable_tables, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved outputs to {output_dir}")


# Quick test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
        
        result = extract_document(pdf_file, output_dir)
        
        print(f"\n===== EXTRACTION RESULTS =====")
        print(f"Pages: {result['pages']}")
        print(f"Text length: {len(result['text'])} characters")
        print(f"Tables found: {len(result['tables'])}")
        
        if result['tables']:
            print("\nFirst table preview:")
            print(pd.DataFrame(result['tables'][0]['dataframe']).head())
    else:
        print("Usage: python docling_extractor.py <path_to_pdf> [output_dir]")