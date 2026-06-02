"""
Docling API client using correct request format.
Requires docling-serve server running.
"""

import requests
import base64
import json
from pathlib import Path
import sys

def convert_pdf_via_api(pdf_path: str, output_dir: str = "outputs", base_url: str = "http://localhost:5001"):
    """
    Convert PDF using Docling Serve API with proper base64 encoding.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save outputs
        base_url: Docling server URL
    """
    # Check if server is running
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code != 200:
            print(f"Server not ready. Status: {response.status_code}")
            return None
        print(f"Server status: {response.json()}")
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect to Docling server.")
        print("Start the server first in another terminal:")
        print("  venv\\Scripts\\activate")
        print("  docling-serve run --enable-ui")
        return None
    
    # Read and encode PDF as base64
    with open(pdf_path, 'rb') as f:
        pdf_bytes = f.read()
        base64_string = base64.b64encode(pdf_bytes).decode('utf-8')
    
    # Prepare request according to API schema
    request_body = {
        "sources": [
            {
                "base64_string": base64_string,
                "filename": Path(pdf_path).name
            }
        ],
        "options": {
            "from_formats": ["pdf"],
            "to_formats": ["markdown", "json"]
        }
    }
    
    # Send conversion request
    try:
        print(f"Converting: {pdf_path}")
        response = requests.post(
            f"{base_url}/v1/convert",
            json=request_body,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            # Save outputs
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            base_name = Path(pdf_path).stem
            
            # Extract and save markdown
            if 'content' in result and 'markdown' in result['content']:
                md_path = Path(output_dir) / f"{base_name}_api.md"
                md_path.write_text(result['content']['markdown'], encoding="utf-8")
                print(f"Saved markdown to: {md_path}")
                print(f"Markdown length: {len(result['content']['markdown'])} characters")
            
            # Extract and save JSON
            if 'content' in result and 'json' in result['content']:
                json_path = Path(output_dir) / f"{base_name}_api.json"
                json_path.write_text(json.dumps(result['content']['json'], indent=2), encoding="utf-8")
                print(f"Saved JSON to: {json_path}")
            
            # Extract table information
            if 'content' in result and 'json' in result['content']:
                doc_json = result['content']['json']
                if 'tables' in doc_json:
                    print(f"\nTables found: {len(doc_json['tables'])}")
                    for i, table in enumerate(doc_json['tables'][:3]):  # Show first 3
                        print(f"  Table {i+1}: {table.get('num_rows', '?')}x{table.get('num_cols', '?')}")
            
            return result
        else:
            print(f"Conversion failed: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "outputs"
        result = convert_pdf_via_api(pdf_file, output_dir)
        
        if result:
            print("\n===== EXTRACTION COMPLETE =====")
        else:
            print("\n===== EXTRACTION FAILED =====")
    else:
        print("Usage: python docling_api.py <path_to_pdf> [output_dir]")