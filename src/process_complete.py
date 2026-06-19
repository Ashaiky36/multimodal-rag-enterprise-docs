"""
Complete pipeline: Process PDF -> Enhance with Vision -> Keep HTML Tables -> Chunks -> Vector Store
"""

import sys
import subprocess
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run a command and log output."""
    logger.info(f"Running: {description}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(f"Failed: {result.stderr}")
        return False
    logger.info("Success")
    return True


def process_document(pdf_path: str):
    """Complete pipeline for a document."""
    doc_name = Path(pdf_path).stem
    output_dir = f"processed_docs/{doc_name}"
    
    # Step 1: MinerU
    if not run_command(f"mineru -p {pdf_path} -o {output_dir} -b pipeline", "MinerU extraction"):
        return
    
    # Step 2: Vision Enhancement
    if not run_command(f"python src/vision_enhance_v2.py {doc_name}", "Vision enhancement"):
        return
    
    # Step 3: Process tables (keep HTML, add headers)
    if not run_command(f"python src/table_flattener.py {doc_name}", "Table processing"):
        return
    
    # Step 4: Build vector store
    chunks_path = f"processed_docs/{doc_name}/{doc_name}_chunks_final.json"
    store_dir = f"processed_docs/{doc_name}/vector_store_final"
    
    from vector_store import build_vector_store_from_chunks
    build_vector_store_from_chunks(chunks_path, store_dir)
    
    logger.info(f"✅ Document {doc_name} processed successfully!")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_document(sys.argv[1])
    else:
        print("Usage: python process_complete.py <pdf_path>")
        print("Example: python process_complete.py data/sample2.pdf")