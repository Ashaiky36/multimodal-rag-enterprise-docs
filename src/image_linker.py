"""
Lightweight image linker for MinerU outputs.
Maps images to their descriptive text without heavy parsing.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageLinker:
    """
    Links images to their descriptive text by scanning markdown linearly.
    Memory-efficient - processes line by line.
    """
    
    def __init__(self, markdown_path: str, images_folder: str):
        """
        Args:
            markdown_path: Path to MinerU's .md file
            images_folder: Path to images folder
        """
        self.markdown_path = Path(markdown_path)
        self.images_folder = Path(images_folder)
        self.image_to_heading = {}  # image_filename -> heading text
        self.heading_to_images = {}  # heading_text -> list of image filenames
        
        self._build_mapping()
    
    def _build_mapping(self):
        """Build mapping by scanning markdown line by line."""
        if not self.markdown_path.exists():
            logger.error(f"Markdown not found: {self.markdown_path}")
            return
        
        if not self.images_folder.exists():
            logger.warning(f"Images folder not found: {self.images_folder}")
        
        current_heading = "Root"
        
        with open(self.markdown_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in lines:
            line = line.rstrip('\n')
            
            # Detect headings (# Heading or ## Heading)
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                current_heading = heading_match.group(2).strip()
                continue
            
            # Detect images in markdown: ![alt](path)
            image_matches = re.findall(r'!\[.*?\]\((.*?)\)', line)
            
            for img_ref in image_matches:
                img_filename = Path(img_ref).name
                img_path = self.images_folder / img_filename
                
                # Also try with images/ prefix
                if not img_path.exists() and img_ref.startswith('images/'):
                    img_path = self.images_folder / img_ref.replace('images/', '')
                
                if img_path.exists():
                    if img_filename not in self.image_to_heading:
                        self.image_to_heading[img_filename] = current_heading
                        self.heading_to_images.setdefault(current_heading, []).append(img_filename)
                        logger.debug(f"Linked image {img_filename[:20]}... -> '{current_heading[:40]}'")
            
            # Also detect hash-based image names directly
            hash_matches = re.findall(r'([a-f0-9]{64}\.jpg)', line, re.IGNORECASE)
            for img_filename in hash_matches:
                img_path = self.images_folder / img_filename
                if img_path.exists() and img_filename not in self.image_to_heading:
                    self.image_to_heading[img_filename] = current_heading
                    self.heading_to_images.setdefault(current_heading, []).append(img_filename)
        
        logger.info(f"Built mapping: {len(self.image_to_heading)} images, {len(self.heading_to_images)} headings")
    
    def find_images_for_heading(self, heading_keywords: List[str]) -> List[str]:
        """
        Find images whose heading contains any of the keywords.
        
        Args:
            heading_keywords: Keywords to match against heading text
        
        Returns:
            List of image paths
        """
        matched_images = []
        
        for heading, images in self.heading_to_images.items():
            heading_lower = heading.lower()
            if any(keyword.lower() in heading_lower for keyword in heading_keywords):
                for img_filename in images:
                    img_path = self.images_folder / img_filename
                    if img_path.exists():
                        matched_images.append(str(img_path))
        
        return matched_images
    
    def find_images_for_query(self, query: str) -> List[str]:
        """
        Extract relevant keywords from query and find matching images.
        """
        keywords = []
        
        # Pattern 1: Roman numeral headings (viii), (xii), etc.
        roman_pattern = r'\([ivx]+\)\s*([^.\n]+)'
        roman_matches = re.findall(roman_pattern, query, re.IGNORECASE)
        for match in roman_matches:
            keywords.extend(match.strip().split()[:3])
        
        # Pattern 2: Key phrases
        phrases = [
            "Performance", "comparison", "broad based", "indices",
            "Shareholding", "Distribution", "Market Price", "Liquidity",
            "chart", "graph", "plot", "figure"
        ]
        keywords.extend([p for p in phrases if p.lower() in query.lower()])
        
        # Pattern 3: Any capitalized words (potential section titles)
        cap_words = re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', query)
        keywords.extend(cap_words)
        
        keywords = list(set(keywords))
        logger.debug(f"Extracted keywords: {keywords[:5]}")
        
        return self.find_images_for_heading(keywords)
    
    def get_image_path(self, image_filename: str) -> Optional[str]:
        """Get full path for an image filename."""
        img_path = self.images_folder / image_filename
        return str(img_path) if img_path.exists() else None
    
    def get_all_headings(self) -> List[str]:
        """Get all headings that have images."""
        return list(self.heading_to_images.keys())


if __name__ == "__main__":
    # Test the image linker
    markdown_path = "outputs/sample_digital1/auto/sample_digital1.md"
    images_folder = "outputs/sample_digital1/auto/images"
    
    if not Path(markdown_path).exists():
        markdown_path = "outputs/sample_digital1/auto/content.md"
    
    if Path(markdown_path).exists():
        linker = ImageLinker(markdown_path, images_folder)
        
        print("\n=== IMAGE LINKER TEST ===")
        print(f"Total images linked: {len(linker.image_to_heading)}")
        
        print("\nHeadings with images:")
        for heading, images in linker.heading_to_images.items():
            print(f"  {heading[:60]}... -> {len(images)} image(s)")
            for img in images[:2]:
                print(f"      {img}")
    else:
        print(f"Markdown not found: {markdown_path}")