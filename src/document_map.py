"""
Builds a persistent map of images to their surrounding text context.
Uses MinerU's original JSON output to preserve document structure.
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Set
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DocumentMap:
    """
    Maps images to their descriptive text context using MinerU's layout.
    Persists across chunks for accurate image retrieval.
    """
    
    def __init__(self, mineru_json_path: str, images_folder: str):
        """
        Args:
            mineru_json_path: Path to MinerU's content_list.json or .json output
            images_folder: Path to the images folder
        """
        self.images_folder = Path(images_folder)
        self.image_map = defaultdict(list)  # heading -> list of image paths
        self.heading_map = {}  # image_path -> heading
        self.context_map = {}  # image_path -> surrounding text
        self.all_images = []
        
        self._load_and_parse(mineru_json_path)
    
    def _load_and_parse(self, json_path: str):
        """Load MinerU JSON and extract image-to-heading relationships."""
        
        json_file = Path(json_path)
        if not json_file.exists():
            logger.warning(f"MinerU JSON not found: {json_path}")
            return
        
        with open(json_file, 'r', encoding='utf-8') as f:
            content = json.load(f)
        
        current_heading = "Root"
        current_text = []
        
        # Handle both list format and dict format
        if isinstance(content, dict):
            # If it's a dict, look for the content list
            items = content.get("content_list", content.get("elements", []))
            if not items:
                items = [content]
        else:
            items = content
        
        for item in items:
            item_type = item.get("type", "")
            
            # Track headings (h1, h2, h3, etc.)
            if item_type == "heading":
                current_heading = self._clean_text(item.get("text", ""))
                current_text = []
                logger.debug(f"Heading: {current_heading}")
            
            # Track text blocks
            elif item_type == "text":
                text = self._clean_text(item.get("text", ""))
                if text:
                    current_text.append(text)
            
            # Track images
            elif item_type == "image" or "figure" in item_type.lower():
                img_path = item.get("text", "") or item.get("img_path", "") or item.get("src", "")
                
                # Resolve full image path
                full_img_path = self._resolve_image_path(img_path)
                
                if full_img_path and full_img_path.exists():
                    self.all_images.append(str(full_img_path))
                    
                    # Map heading to this image
                    self.image_map[current_heading].append(str(full_img_path))
                    self.heading_map[str(full_img_path)] = current_heading
                    
                    # Store surrounding context
                    context = " ".join(current_text[-5:])  # Last 5 text blocks
                    self.context_map[str(full_img_path)] = context[:500]
                    
                    logger.info(f"Mapped image to heading: '{current_heading[:50]}' -> {full_img_path.name}")
        
        logger.info(f"Document map built: {len(self.all_images)} images, {len(self.image_map)} headings")
    
    def _clean_text(self, text: str) -> str:
        """Clean text for matching."""
        if not text:
            return ""
        # Remove extra whitespace, newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _resolve_image_path(self, img_path: str) -> Optional[Path]:
        """Resolve image path from various formats."""
        if not img_path:
            return None
        
        # Extract filename
        filename = Path(img_path).name
        
        # Try different locations
        candidates = [
            self.images_folder / filename,
            self.images_folder / img_path,
            Path(img_path),
        ]
        
        # Also try with common prefixes
        if not filename.startswith('image_'):
            candidates.append(self.images_folder / f"image_{filename}")
        
        for candidate in candidates:
            if candidate and candidate.exists():
                return candidate
        
        return None
    
    def find_images_for_query(self, query: str, relevant_chunks: List[Dict]) -> List[str]:
        """
        Find images relevant to a query based on:
        1. Heading matching (from query)
        2. Context matching (from retrieved chunks)
        
        Args:
            query: User's question
            relevant_chunks: Retrieved chunks from vector store
        
        Returns:
            List of image paths that are relevant
        """
        matched_images = set()
        
        # Method 1: Extract potential heading from query
        # Look for patterns like "(viii) Performance" or similar
        heading_pattern = r'\([ivx]+\)\s+[^.\n]+'
        query_headings = re.findall(heading_pattern, query, re.IGNORECASE)
        
        for query_heading in query_headings:
            query_heading_clean = query_heading.strip().lower()
            for doc_heading, images in self.image_map.items():
                if query_heading_clean in doc_heading.lower():
                    matched_images.update(images)
                    logger.info(f"Matched heading: '{doc_heading[:50]}' -> {len(images)} images")
        
        # Method 2: Search through retrieved chunks for image references
        for chunk in relevant_chunks:
            chunk_content = chunk.get("content", "")
            
            # Look for markdown image syntax
            md_images = re.findall(r'!\[.*?\]\((.*?)\)', chunk_content)
            for img_ref in md_images:
                resolved = self._resolve_image_path(img_ref)
                if resolved and str(resolved) in self.heading_map:
                    matched_images.add(str(resolved))
            
            # Look for explicit image paths
            path_matches = re.findall(r'[\w\-\.]+\.(?:jpg|jpeg|png)', chunk_content)
            for img_name in path_matches:
                resolved = self._resolve_image_path(img_name)
                if resolved and str(resolved) in self.heading_map:
                    matched_images.add(str(resolved))
        
        return list(matched_images)[:3]  # Limit to 3 images
    
    def get_heading_for_image(self, image_path: str) -> Optional[str]:
        """Get the heading associated with an image."""
        return self.heading_map.get(image_path)
    
    def get_all_headings(self) -> List[str]:
        """Get all headings that have associated images."""
        return list(self.image_map.keys())
    
    def save(self, output_path: str):
        """Save the document map to disk for reuse."""
        # Convert defaultdict to regular dict for JSON serialization
        data = {
            "image_map": dict(self.image_map),
            "heading_map": self.heading_map,
            "context_map": self.context_map,
            "all_images": self.all_images
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Document map saved to {output_path}")
    
    @classmethod
    def load(cls, load_path: str, images_folder: str):
        """Load a saved document map."""
        instance = cls.__new__(cls)
        instance.images_folder = Path(images_folder)
        
        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        instance.image_map = defaultdict(list, data.get("image_map", {}))
        instance.heading_map = data.get("heading_map", {})
        instance.context_map = data.get("context_map", {})
        instance.all_images = data.get("all_images", [])
        
        logger.info(f"Document map loaded from {load_path}")
        return instance


def find_mineru_json(output_dir: str, pdf_name: str) -> Optional[Path]:
    """
    Find MinerU JSON file with various naming patterns.
    """
    auto_folder = Path(output_dir) / pdf_name / "auto"
    
    if not auto_folder.exists():
        auto_folder = Path(output_dir) / pdf_name
    
    if not auto_folder.exists():
        return None
    
    # Possible JSON file names
    patterns = [
        f"{pdf_name}.json",
        f"{pdf_name}_content_list.json",
        f"{pdf_name}_content_list_v2.json",
        "content_list.json",
        "content_list_v2.json",
        "results.json"
    ]
    
    for pattern in patterns:
        json_path = auto_folder / pattern
        if json_path.exists():
            logger.info(f"Found MinerU JSON: {json_path}")
            return json_path
    
    # Also search recursively
    for json_path in auto_folder.rglob("*.json"):
        if "content" in json_path.name.lower() or json_path.name == f"{pdf_name}.json":
            logger.info(f"Found MinerU JSON (recursive): {json_path}")
            return json_path
    
    return None


def build_document_map_from_mineru(
    pdf_path: str, 
    output_dir: str = "outputs",
    save_map_path: str = "outputs/document_map.json"
) -> DocumentMap:
    """
    Build document map from MinerU output.
    
    Args:
        pdf_path: Original PDF path
        output_dir: MinerU output directory
        save_map_path: Where to save the map
    """
    base_name = Path(pdf_path).stem
    
    # Find the MinerU JSON file
    mineru_json = find_mineru_json(output_dir, base_name)
    
    if not mineru_json:
        raise FileNotFoundError(f"MinerU JSON not found for {base_name} in {output_dir}")
    
    # Find images folder
    images_folder = Path(output_dir) / base_name / "auto" / "images"
    if not images_folder.exists():
        images_folder = Path(output_dir) / base_name / "images"
    
    if not images_folder.exists():
        logger.warning(f"Images folder not found, images will not be resolved")
    
    doc_map = DocumentMap(str(mineru_json), str(images_folder))
    doc_map.save(save_map_path)
    
    return doc_map


if __name__ == "__main__":
    import sys
    
    # Build document map for sample PDF
    pdf_file = sys.argv[1] if len(sys.argv) > 1 else "data/sample_digital1.pdf"
    
    print(f"Building document map for: {pdf_file}")
    
    try:
        doc_map = build_document_map_from_mineru(
            pdf_file,
            "outputs",
            "outputs/document_map.json"
        )
        
        print("\n===== DOCUMENT MAP SUMMARY =====")
        print(f"Total images: {len(doc_map.all_images)}")
        print(f"Headings with images: {len(doc_map.get_all_headings())}")
        
        print("\nHeadings found:")
        for heading in doc_map.get_all_headings()[:10]:
            print(f"  - {heading[:80]}...")
        
        print("\nImage mappings:")
        for heading, images in list(doc_map.image_map.items())[:5]:
            print(f"  {heading[:50]}... -> {len(images)} image(s)")
            for img in images[:2]:
                print(f"      {Path(img).name}")
    
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nPlease check that MinerU has been run on this PDF.")
        print("The output should be in: outputs/sample_digital1/auto/")
        print("Look for files like: sample_digital1_content_list.json or .json")