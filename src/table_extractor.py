"""
Table extraction module for PDFs.
Extracts tables as Pandas DataFrames using camelot-py.
Supports both bordered (lattice) and borderless (stream) tables.
"""

import camelot
import pandas as pd
import json
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def extract_tables_lattice(pdf_path: str, pages: str = 'all', flavor: str = 'lattice') -> Optional[List[pd.DataFrame]]:
    """
    Extract tables with visible borders using lattice method.
    
    Args:
        pdf_path: Path to PDF file
        pages: Page numbers ('all', '1', '1-3', etc.)
        flavor: 'lattice' for bordered tables
    
    Returns:
        List of DataFrames or None if no tables found
    """
    try:
        logger.info(f"Extracting tables using {flavor} method from {pdf_path}, pages: {pages}")
        tables = camelot.read_pdf(pdf_path, pages=pages, flavor=flavor)
        
        if len(tables) == 0:
            logger.warning(f"No tables found with {flavor} method")
            return None
        
        logger.info(f"Found {len(tables)} tables")
        
        # Convert to DataFrames
        dfs = []
        for i, table in enumerate(tables):
            df = table.df
            # Clean column names (remove newlines, extra spaces)
            if len(df.columns) > 0:
                df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
            dfs.append(df)
            logger.info(f"Table {i+1}: {df.shape[0]} rows x {df.shape[1]} columns")
        
        return dfs
    
    except Exception as e:
        logger.error(f"Lattice extraction failed: {e}")
        return None


def extract_tables_stream(pdf_path: str, pages: str = 'all') -> Optional[List[pd.DataFrame]]:
    """
    Extract borderless tables using stream method.
    
    Args:
        pdf_path: Path to PDF file
        pages: Page numbers ('all', '1', '1-3', etc.)
    
    Returns:
        List of DataFrames or None if no tables found
    """
    try:
        logger.info(f"Extracting tables using stream method from {pdf_path}, pages: {pages}")
        tables = camelot.read_pdf(pdf_path, pages=pages, flavor='stream')
        
        if len(tables) == 0:
            logger.warning(f"No tables found with stream method")
            return None
        
        logger.info(f"Found {len(tables)} tables")
        
        # Convert to DataFrames
        dfs = []
        for i, table in enumerate(tables):
            df = table.df
            if len(df.columns) > 0:
                df.columns = [str(col).replace('\n', ' ').strip() for col in df.columns]
            dfs.append(df)
            logger.info(f"Table {i+1}: {df.shape[0]} rows x {df.shape[1]} columns")
        
        return dfs
    
    except Exception as e:
        logger.error(f"Stream extraction failed: {e}")
        return None


def extract_all_tables(pdf_path: str, pages: str = 'all') -> Dict[str, List[pd.DataFrame]]:
    """
    Attempt both lattice and stream methods, return whichever finds tables.
    
    Args:
        pdf_path: Path to PDF file
        pages: Page numbers to process
    
    Returns:
        Dictionary with 'tables' key containing list of DataFrames and 'method' key
    """
    logger.info(f"Extracting all tables from: {pdf_path}")
    
    # Try lattice first (bordered tables)
    tables = extract_tables_lattice(pdf_path, pages)
    if tables and len(tables) > 0:
        return {'tables': tables, 'method': 'lattice', 'count': len(tables)}
    
    # Fall back to stream (borderless tables)
    tables = extract_tables_stream(pdf_path, pages)
    if tables and len(tables) > 0:
        return {'tables': tables, 'method': 'stream', 'count': len(tables)}
    
    logger.warning("No tables found with either lattice or stream methods")
    return {'tables': [], 'method': None, 'count': 0}


def tables_to_dict(dfs: List[pd.DataFrame]) -> List[Dict]:
    """
    Convert list of DataFrames to list of dictionaries for JSON serialization.
    
    Args:
        dfs: List of pandas DataFrames
    
    Returns:
        List of dictionaries with table data and metadata
    """
    tables_data = []
    for i, df in enumerate(dfs):
        # Convert DataFrame to dict with proper handling of NaN values
        table_dict = {
            'table_index': i + 1,
            'shape': {'rows': df.shape[0], 'columns': df.shape[1]},
            'columns': df.columns.tolist(),
            'data': df.fillna('').to_dict(orient='records')
        }
        tables_data.append(table_dict)
    return tables_data


def save_tables_to_json(tables_data: List[Dict], output_path: str) -> None:
    """
    Save extracted tables to JSON file.
    
    Args:
        tables_data: List of table dictionaries
        output_path: Path to save JSON file
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(tables_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Tables saved to {output_path}")
    except Exception as e:
        logger.error(f"Failed to save tables: {e}")


def extract_and_save_tables(pdf_path: str, output_dir: str, pages: str = 'all') -> Dict:
    """
    Main function: extract tables and save to JSON.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save output JSON
        pages: Pages to process
    
    Returns:
        Dictionary containing extraction results
    """
    # Extract tables
    result = extract_all_tables(pdf_path, pages)
    
    if result['count'] == 0:
        logger.warning("No tables found in document")
        return {'status': 'no_tables', 'tables': [], 'method': None}
    
    # Convert to serializable format
    tables_data = tables_to_dict(result['tables'])
    
    # Save to JSON
    output_path = Path(output_dir) / f"{Path(pdf_path).stem}_tables.json"
    save_tables_to_json(tables_data, output_path)
    
    return {
        'status': 'success',
        'tables': tables_data,
        'method': result['method'],
        'count': result['count'],
        'output_file': str(output_path)
    }


# Quick test if run directly
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else 'outputs'
        
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        result = extract_and_save_tables(pdf_file, output_dir)
        
        print("\n===== EXTRACTION RESULTS =====")
        print(f"Status: {result['status']}")
        print(f"Tables found: {result['count']}")
        print(f"Method used: {result['method']}")
        
        if result['count'] > 0:
            print("\nFirst table preview:")
            print(pd.DataFrame(result['tables'][0]['data']).head())
    else:
        print("Usage: python table_extractor.py <path_to_pdf> [output_dir]")