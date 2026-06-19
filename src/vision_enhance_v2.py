

"""
Complete vision enhancement for both tables and plots.
- Processes ALL images in the images folder
- Traces each image back to its position in the markdown file
- Inserts detailed descriptions using Qwen2.5VL Vision model
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import time
import ollama
import sys
import io

# Force UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class VisionEnhancerV2:
    """
    Enhanced vision processor using Qwen2.5VL.
    """
    
    def __init__(self, vision_model: str = "qwen2.5vl:3b", batch_size: int = 5):
        self.vision_model = vision_model
        self.batch_size = batch_size
        self._check_ollama()
    
    def _check_ollama(self):
        """Check if Ollama is running and model is available."""
        try:
            models = ollama.list()
            model_names = [m.get('model', '') for m in models.get('models', [])]
            logger.info(f"Available models: {model_names}")
            
            if self.vision_model not in model_names:
                logger.info(f"Pulling model: {self.vision_model}...")
                ollama.pull(self.vision_model)
                logger.info(f"Model pulled: {self.vision_model}")
            else:
                logger.info(f"Vision model ready: {self.vision_model}")
        except Exception as e:
            logger.error(f"Ollama not running: {e}")
            logger.info("Please start Ollama: ollama serve")
    
    def find_images_and_positions(self, doc_dir: Path) -> Tuple[List[Path], Dict[str, str]]:
        """Find all images in the images folder."""
        # Find images folder
        images_folders = list(doc_dir.rglob("images"))
        if not images_folders:
            logger.warning(f"No images folder found in {doc_dir}")
            return [], {}
        
        images_folder = images_folders[0]
        logger.info(f"Images folder: {images_folder}")
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}
        images = [f for f in images_folder.iterdir() if f.suffix.lower() in image_extensions]
        logger.info(f"Found {len(images)} images")
        
        # Find markdown file
        md_files = list(doc_dir.rglob("*.md"))
        if not md_files:
            logger.warning(f"No markdown file found in {doc_dir}")
            return images, {}
        
        # Use the largest markdown as main
        main_md = max(md_files, key=lambda x: x.stat().st_size)
        logger.info(f"Main markdown: {main_md}")
        
        # Read markdown content
        with open(main_md, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Map images to their positions in markdown
        image_positions = {}
        
        for img in images:
            img_name = img.name
            img_rel_path = f"images/{img_name}"
            
            if img_rel_path in content:
                image_positions[img_rel_path] = {
                    'markdown_path': str(main_md),
                    'image_path': str(img),
                    'image_name': img_name,
                    'found_in_content': True
                }
            elif img_name in content:
                image_positions[img_name] = {
                    'markdown_path': str(main_md),
                    'image_path': str(img),
                    'image_name': img_name,
                    'found_in_content': True
                }
            else:
                image_positions[img_name] = {
                    'markdown_path': str(main_md),
                    'image_path': str(img),
                    'image_name': img_name,
                    'found_in_content': False
                }
        
        return images, image_positions
    
#     def describe_image(self, image_path: str, context: str = "") -> str:
#         """Get detailed description from Qwen2.5VL Vision model."""
#         try:
#             prompt = f"""You are analyzing an image from a financial annual report.

# CONTEXT: {context[:300]}

# This image is either a TABLE or a CHART/GRAPH.

# If TABLE: Extract EVERY row and column. List all headers and cell values.
# If CHART: Identify the chart type, axes labels, all data points, percentages, and trends.

# Be extremely precise with ALL numbers. Output as plain text.

# DESCRIPTION:"""
            
#             response = ollama.generate(
#                 model=self.vision_model,
#                 prompt=prompt,
#                 images=[image_path]
#             )
            
#             description = response['response'].strip()
#             logger.info(f"✓ Described: {Path(image_path).name} ({len(description)} chars)")
#             return description
            
#         except Exception as e:
#             logger.error(f"Vision model failed for {image_path}: {e}")
#             return f"[Image could not be processed: {Path(image_path).name}]"
    def describe_image(self, image_path: str, context: str = "") -> str:
        """
        Get detailed description from Vision model using proper Ollama API.
        """
        try:
            # Read image as base64
            import base64
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            
            prompt = f"""You are analyzing an image from a financial annual report.

    This image is either a TABLE or a CHART/GRAPH.

    If it's a TABLE:
    - Extract EVERY row and column
    - List all headers and cell values
    - Be extremely precise with all numbers

    If it's a CHART/GRAPH:
    - Identify the chart type (bar, line, pie, etc.)
    - List all axes labels and scales
    - Extract ALL data points, percentages, and values
    - Describe trends and patterns

    DESCRIPTION:"""

            # Use the ollama client with proper image format
            response = ollama.chat(
                model=self.vision_model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_data]
                }]
            )
            
            description = response['message']['content'].strip()
            logger.info(f"✓ Described: {Path(image_path).name} ({len(description)} chars)")
            return description
            
        except Exception as e:
            logger.error(f"Vision model failed for {image_path}: {e}")
            return f"[Image could not be processed: {Path(image_path).name}]"

    def enhance_document(self, doc_dir: Path) -> Optional[Path]:
        """Main method: Enhance all images with vision descriptions."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Enhancing document: {doc_dir.name}")
        logger.info(f"{'='*60}")
        
        # Find images and positions
        images, image_positions = self.find_images_and_positions(doc_dir)
        
        if not images:
            logger.warning("No images found to process")
            return None
        
        # Read the current markdown content
        main_md_path = None
        for pos_data in image_positions.values():
            if pos_data.get('markdown_path'):
                main_md_path = pos_data['markdown_path']
                break
        
        if not main_md_path:
            logger.error("No markdown file found")
            return None
        
        with open(main_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Process each image
        total = len(images)
        processed = 0
        
        for img in images:
            processed += 1
            logger.info(f"Processing {processed}/{total}: {img.name}")
            
            # Get description
            description = self.describe_image(str(img))
            
            if description:
                # Insert description into markdown
                img_name = img.name
                replacement = f"\n\n<!-- Image: {img_name} -->\n[VISION DESCRIPTION: {description}]\n\n"
                
                # Try different patterns
                inserted = False
                for pattern in [f"images/{img_name}", img_name]:
                    if pattern in content:
                        content = content.replace(pattern, pattern + replacement)
                        inserted = True
                        logger.info(f"  Inserted description for: {img_name}")
                        break
                
                if not inserted:
                    content += replacement
                    logger.info(f"  Appended description for: {img_name}")
            
            # Add delay to avoid overwhelming Ollama
            if processed % self.batch_size == 0:
                logger.info(f"Batch {processed//self.batch_size} complete. Pausing...")
                time.sleep(2)
        
        # Save enhanced markdown
        enhanced_path = doc_dir / f"{doc_dir.name}_enhanced.md"
        with open(enhanced_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"\n Enhanced markdown saved: {enhanced_path}")
        logger.info(f"   Total descriptions inserted: {len(images)}")
        
        return enhanced_path
    
    def process_all_documents(self, base_dir: str = "processed_docs") -> List[Path]:
        """Process all documents in the processed_docs directory."""
        base_path = Path(base_dir)
        
        if not base_path.exists():
            logger.error(f"Directory not found: {base_dir}")
            return []
        
        enhanced_files = []
        
        for doc_dir in base_path.iterdir():
            if doc_dir.is_dir():
                try:
                    enhanced = self.enhance_document(doc_dir)
                    if enhanced:
                        enhanced_files.append(enhanced)
                except Exception as e:
                    logger.error(f"Failed to process {doc_dir.name}: {e}")
        
        logger.info(f"\n Enhanced {len(enhanced_files)} documents")
        return enhanced_files


if __name__ == "__main__":
    import sys
    
    # Initialize with qwen2.5vl:3b
    enhancer = VisionEnhancerV2(vision_model="qwen2.5vl:3b")
    
    if len(sys.argv) > 1:
        # Process specific document
        doc_id = sys.argv[1]
        doc_dir = Path("processed_docs") / doc_id
        if doc_dir.exists():
            enhanced = enhancer.enhance_document(doc_dir)
            if enhanced:
                print(f"\n Done! Enhanced markdown: {enhanced}")
        else:
            print(f"Document not found: {doc_id}")
            print("Available documents:")
            for d in Path("processed_docs").iterdir():
                if d.is_dir():
                    print(f"  - {d.name}")
    else:
        # Process all documents
        print("Processing all documents...")
        enhanced_files = enhancer.process_all_documents("processed_docs")
        print(f"\nDone! Processed {len(enhanced_files)} documents")