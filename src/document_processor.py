"""
Document processing pipeline for new PDF uploads.
Handles extraction, chunking, and vector store creation.
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Process new PDF documents through the pipeline.
    """
    
    def __init__(self, output_base_dir: str = "processed_docs"):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    def _find_markdown_file(self, doc_output_dir: Path) -> Optional[Path]:
        """
        Dynamically find the markdown file created by MinerU.
        Searches recursively for any .md file.
        """
        logger.info(f"Searching for markdown file in: {doc_output_dir}")
        
        if not doc_output_dir.exists():
            logger.error(f"Directory does not exist: {doc_output_dir}")
            return None
        
        # Recursively find all .md files
        all_md_files = list(doc_output_dir.rglob("*.md"))
        
        if not all_md_files:
            logger.error(f"No .md files found in {doc_output_dir}")
            # List directory contents for debugging
            logger.info(f"Directory contents: {list(doc_output_dir.iterdir())}")
            for subdir in doc_output_dir.iterdir():
                if subdir.is_dir():
                    logger.info(f"  Subdir {subdir.name}: {list(subdir.glob('*'))}")
            return None
        
        # Filter out small files (likely not the main content)
        # Main markdown file is usually > 10KB
        large_md = [f for f in all_md_files if f.stat().st_size > 10000]
        
        if large_md:
            # Return the largest one
            largest = max(large_md, key=lambda x: x.stat().st_size)
            logger.info(f"Found markdown file: {largest} ({largest.stat().st_size} bytes)")
            return largest
        
        # If no large files, return the largest overall
        largest = max(all_md_files, key=lambda x: x.stat().st_size)
        logger.info(f"Found markdown file: {largest} ({largest.stat().st_size} bytes)")
        return largest
    
    def _find_images_folder(self, doc_output_dir: Path) -> Optional[Path]:
        """Dynamically find the images folder created by MinerU."""
        if not doc_output_dir.exists():
            return None
        
        # Recursively search for images folder
        for images_path in doc_output_dir.rglob("images"):
            if images_path.is_dir():
                logger.info(f"Found images folder: {images_path}")
                return images_path
        
        logger.warning(f"No images folder found in {doc_output_dir}")
        return None
    
    def process_document(self, pdf_path: str, doc_name: str = None) -> Dict:
        """
        Process a PDF document through the complete pipeline.
        """
        if doc_name is None:
            doc_name = Path(pdf_path).stem
        
        result = {
            "success": False,
            "doc_name": doc_name,
            "doc_id": self._generate_doc_id(doc_name),
            "steps": []
        }
        
        # Create document output directory
        doc_output_dir = self.output_base_dir / result["doc_id"]
        doc_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Run MinerU extraction
        logger.info(f"Step 1: Running MinerU on {pdf_path}")
        mineru_success = self._run_mineru(pdf_path, str(doc_output_dir))
        result["steps"].append({
            "name": "mineru_extraction",
            "success": mineru_success,
            "output_dir": str(doc_output_dir)
        })
        
        if not mineru_success:
            result["error"] = "MinerU extraction failed"
            return result
        
        # Step 2: Find the actual markdown file (dynamic discovery)
        logger.info("Step 2: Finding markdown file...")
        markdown_file = self._find_markdown_file(doc_output_dir)
        
        if not markdown_file:
            logger.error(f"Could not find markdown file in {doc_output_dir}")
            result["error"] = "Markdown file not found after MinerU extraction"
            return result
        
        logger.info(f"Found markdown file: {markdown_file}")
        
        # Step 3: Create overlapping chunks
        logger.info("Step 3: Creating overlapping chunks")
        chunks_file_path = doc_output_dir / f"{result['doc_id']}_chunks.json"
        chunks_success, chunks_file = self._create_overlapping_chunks(
            str(markdown_file),  # Pass the dynamically found path
            chunks_file_path
        )
        result["steps"].append({
            "name": "chunk_creation",
            "success": chunks_success,
            "chunks_file": str(chunks_file) if chunks_success else None
        })
        
        if not chunks_success:
            result["error"] = "Chunk creation failed"
            return result
        
        # Step 4: Build vector store
        logger.info("Step 4: Building vector store")
        store_dir = doc_output_dir / "vector_store"
        vector_success = self._build_vector_store(str(chunks_file), str(store_dir))
        result["steps"].append({
            "name": "vector_store",
            "success": vector_success,
            "store_dir": str(store_dir) if vector_success else None
        })
        
        if not vector_success:
            result["error"] = "Vector store creation failed"
            return result
        
        # Step 5: Create image linker (if images exist)
        images_folder = self._find_images_folder(doc_output_dir)
        
        if images_folder and markdown_file:
            try:
                from image_linker import ImageLinker
                image_linker = ImageLinker(str(markdown_file), str(images_folder))
                result["image_linker"] = image_linker
                result["steps"].append({
                    "name": "image_linker",
                    "success": True,
                    "images_mapped": len(image_linker.image_to_heading)
                })
                logger.info(f"Image linker created: {len(image_linker.image_to_heading)} images mapped")
            except Exception as e:
                logger.warning(f"Image linker creation failed: {e}")
        
        result["success"] = True
        result["chunks_file"] = str(chunks_file)
        result["store_dir"] = str(store_dir)
        result["output_dir"] = str(doc_output_dir)
        result["markdown_file"] = str(markdown_file)
        
        logger.info(f"Document processing complete: {doc_name}")
        return result
    
    def _generate_doc_id(self, doc_name: str) -> str:
        """Generate a unique document ID."""
        import hashlib
        import time
        unique_str = f"{doc_name}_{time.time()}"
        return hashlib.md5(unique_str.encode()).hexdigest()[:12]
    
    def _run_mineru(self, pdf_path: str, output_dir: str) -> bool:
        """Run MinerU on a PDF file."""
        try:
            cmd = [
                "mineru",
                "-p", pdf_path,
                "-o", output_dir,
                "-b", "pipeline"
            ]
            
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("MinerU extraction successful")
                return True
            else:
                logger.error(f"MinerU failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("MinerU timed out after 5 minutes")
            return False
        except Exception as e:
            logger.error(f"MinerU error: {e}")
            return False
    
    def _create_overlapping_chunks(self, markdown_path: str, output_path: Path) -> Tuple[bool, Optional[Path]]:
        """Create overlapping chunks from markdown."""
        try:
            from overlap_chunker import create_overlapping_chunks_from_mineru
            
            # Verify the markdown file exists
            if not Path(markdown_path).exists():
                logger.error(f"Markdown file does not exist: {markdown_path}")
                return False, None
            
            logger.info(f"Creating chunks from: {markdown_path}")
            
            chunks = create_overlapping_chunks_from_mineru(
                markdown_path,
                str(output_path),
                chunk_size=1000,
                overlap=250
            )
            
            if chunks and len(chunks) > 0:
                logger.info(f"Created {len(chunks)} chunks")
                return True, output_path
            else:
                logger.error("No chunks created")
                return False, None
            
        except Exception as e:
            logger.error(f"Chunk creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False, None
    
    def _build_vector_store(self, chunks_file: str, store_dir: str) -> bool:
        """Build vector store from chunks."""
        try:
            from vector_store import build_vector_store_from_chunks
            
            build_vector_store_from_chunks(chunks_file, store_dir)
            return True
            
        except Exception as e:
            logger.error(f"Vector store build failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def get_processed_documents(self) -> List[Dict]:
        """Get list of all processed documents (only valid ones)."""
        documents = []
        for doc_dir in self.output_base_dir.iterdir():
            if doc_dir.is_dir():
                chunks_file = doc_dir / f"{doc_dir.name}_chunks.json"
                store_dir = doc_dir / "vector_store"
                
                if chunks_file.exists() and store_dir.exists():
                    doc_info = {
                        "doc_id": doc_dir.name,
                        "has_chunks": True,
                        "has_vector_store": True,
                        "chunks_file": str(chunks_file),
                        "store_dir": str(store_dir),
                        "modified_time": doc_dir.stat().st_mtime
                    }
                    documents.append(doc_info)
                else:
                    if any(doc_dir.iterdir()):
                        logger.warning(f"Incomplete document: {doc_dir.name}")
        
        return sorted(documents, key=lambda x: x["modified_time"], reverse=True)
    
    def load_document(self, doc_id: str) -> Dict:
        """Load a previously processed document."""
        doc_dir = self.output_base_dir / doc_id
        
        if not doc_dir.exists():
            return {"success": False, "error": "Document not found"}
        
        chunks_file = doc_dir / f"{doc_id}_chunks.json"
        store_dir = doc_dir / "vector_store"
        
        if not chunks_file.exists() or not store_dir.exists():
            return {"success": False, "error": "Document data incomplete"}
        
        from vector_store import VectorStore
        from enhanced_retriever import EnhancedRetriever
        
        vector_store = VectorStore()
        vector_store.load(str(store_dir))
        retriever = EnhancedRetriever(vector_store, str(chunks_file))
        
        image_linker = None
        try:
            from image_linker import ImageLinker
            markdown_file = self._find_markdown_file(doc_dir)
            images_folder = self._find_images_folder(doc_dir)
            
            if markdown_file and images_folder:
                image_linker = ImageLinker(str(markdown_file), str(images_folder))
        except Exception as e:
            logger.warning(f"Could not load image linker: {e}")
        
        return {
            "success": True,
            "doc_id": doc_id,
            "retriever": retriever,
            "vector_store": vector_store,
            "image_linker": image_linker,
            "chunks_file": str(chunks_file),
            "store_dir": str(store_dir)
        }
    def cleanup_old_documents(self, max_docs: int = 5):
        """Keep only the most recent N documents."""
        docs = self.get_processed_documents()
        if len(docs) > max_docs:
            # Delete oldest documents
            for doc in docs[max_docs:]:
                doc_path = self.output_base_dir / doc["doc_id"]
                if doc_path.exists():
                    shutil.rmtree(doc_path)
                    logger.info(f"Cleaned up old document: {doc['doc_id']}")


if __name__ == "__main__":
    processor = DocumentProcessor()
    docs = processor.get_processed_documents()
    print("Processed documents:")
    for doc in docs:
        print(f"  - {doc['doc_id']}: {doc['chunks_file']}")