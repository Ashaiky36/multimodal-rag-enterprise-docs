# """
# Auto-image attachment module.
# Scans text chunks for image references and locates the actual image files.
# """

# import re
# from pathlib import Path
# from typing import List, Dict, Optional, Tuple
# import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)


# class ImageFinder:
#     """
#     Finds and attaches images referenced in text chunks.
#     """
    
#     # def __init__(self, images_folder: str = "outputs/sample_digital1/auto/images"):
#     #     """
#     #     Args:
#     #         images_folder: Path to MinerU's extracted images folder
#     #     """
#     #     self.images_folder = Path(images_folder)
#     #     self.image_cache = {}  # Cache for fast lookup
        
#     #     # Pre-load all available images
#     #     if self.images_folder.exists():
#     #         self.available_images = list(self.images_folder.glob("*"))
#     #         logger.info(f"Found {len(self.available_images)} images in {images_folder}")
#     #         # Build cache by filename
#     #         for img_path in self.available_images:
#     #             self.image_cache[img_path.name.lower()] = img_path
#     #             # Also cache without extension for flexibility
#     #             self.image_cache[img_path.stem.lower()] = img_path
#     #     else:
#     #         self.available_images = []
#     #         logger.warning(f"Images folder not found: {images_folder}")
#     def __init__(self, images_folder: str = "outputs/sample_digital1/auto/images"):
#         """
#         Args:
#             images_folder: Path to MinerU's extracted images folder
#         """
#         self.images_folder = Path(images_folder)
#         self.image_cache = {}
        
#         # Allowed image extensions
#         self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
#         # Pre-load all available images
#         if self.images_folder.exists():
#             # Filter to only image files, exclude .gitkeep, .txt, etc.
#             self.available_images = [
#                 p for p in self.images_folder.iterdir() 
#                 if p.suffix.lower() in self.image_extensions and p.is_file()
#             ]
#             logger.info(f"Found {len(self.available_images)} images in {images_folder}")
            
#             # Build cache by filename
#             for img_path in self.available_images:
#                 self.image_cache[img_path.name.lower()] = img_path
#                 self.image_cache[img_path.stem.lower()] = img_path
#         else:
#             self.available_images = []
#             logger.warning(f"Images folder not found: {images_folder}")
    
#     # def extract_image_references(self, text: str) -> List[str]:
#     #     """
#     #     Extract image references from text using multiple patterns.
        
#     #     Patterns:
#     #     - Markdown: ![alt](path)
#     #     - HTML: <img src="path">
#     #     - Plain paths: images/filename.jpg, auto/images/name.png
#     #     - Figure references: Figure 1, Fig. 2, etc.
#     #     """
#     #     references = []
        
#     #     # Pattern 1: Markdown image syntax
#     #     md_pattern = r'!\[.*?\]\((.*?)\)'
#     #     references.extend(re.findall(md_pattern, text))
        
#     #     # Pattern 2: HTML img tags
#     #     html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
#     #     references.extend(re.findall(html_pattern, text))
        
#     #     # Pattern 3: Image file extensions in text
#     #     ext_pattern = r'[\w\-/]+\.(jpg|jpeg|png|gif|bmp|webp)'
#     #     references.extend(re.findall(ext_pattern, text))
        
#     #     # Pattern 4: Figure references (these need mapping)
#     #     # Look for "Figure X:", "Fig. X", etc.
#     #     figure_pattern = r'Figure\s+(\d+)|Fig\.?\s*(\d+)'
#     #     figure_matches = re.findall(figure_pattern, text, re.IGNORECASE)
#     #     for match in figure_matches:
#     #         fig_num = match[0] or match[1]
#     #         if fig_num:
#     #             references.append(f"figure_{fig_num}")
        
#     #     # Clean and deduplicate
#     #     unique_refs = []
#     #     for ref in references:
#     #         if isinstance(ref, tuple):
#     #             ref = ref[0] if ref[0] else ref[1]
#     #         if ref and ref not in unique_refs:
#     #             unique_refs.append(ref)
        
#     #     return unique_refs
#     def extract_image_references(self, text: str) -> List[str]:
#         """
#         Extract image references from text using multiple patterns.
#         """
#         references = []
        
#         # Pattern 1: Markdown image syntax
#         md_pattern = r'!\[.*?\]\((.*?)\)'
#         references.extend(re.findall(md_pattern, text))
        
#         # Pattern 2: HTML img tags
#         html_pattern = r'<img[^>]+src=["\']([^"\']+)["\']'
#         references.extend(re.findall(html_pattern, text))
        
#         # Pattern 3: Image file extensions (including hash names)
#         # Match: word chars, hyphens, underscores, dots, then extension
#         ext_pattern = r'[\w\-\.]+\.(jpg|jpeg|png|gif|bmp|webp)'
#         matches = re.findall(ext_pattern, text, re.IGNORECASE)
#         # The pattern returns the extension, we need the full match
#         full_matches = re.findall(r'[\w\-\.]+\.(?:jpg|jpeg|png|gif|bmp|webp)', text, re.IGNORECASE)
#         references.extend(full_matches)
        
#         # Pattern 4: MinerU's image references in markdown
#         # Often looks like: ![image](images/058ed5ed...jpg)
#         mineru_pattern = r'images\/[\w\d]+\.(jpg|png)'
#         references.extend(re.findall(mineru_pattern, text))
        
#         # Pattern 5: Figure references (these need mapping)
#         figure_pattern = r'Figure\s+(\d+)|Fig\.?\s*(\d+)'
#         figure_matches = re.findall(figure_pattern, text, re.IGNORECASE)
#         for match in figure_matches:
#             fig_num = match[0] or match[1]
#             if fig_num:
#                 references.append(f"figure_{fig_num}")
        
#         # Clean and deduplicate
#         unique_refs = []
#         for ref in references:
#             if isinstance(ref, tuple):
#                 ref = ref[0] if ref[0] else ref[1]
#             if ref and ref not in unique_refs:
#                 unique_refs.append(ref)
        
#         return unique_refs
    
#     def find_image_by_reference(self, reference: str) -> Optional[Path]:
#         """
#         Find an image file matching the reference.
#         """
#         if not reference:
#             return None
        
#         # Clean the reference
#         ref_clean = reference.strip().lower()
#         ref_clean = ref_clean.replace("\\", "/")
        
#         # Extract just the filename
#         ref_filename = Path(ref_clean).name
#         ref_stem = Path(ref_clean).stem
        
#         # Check cache first (by full name, stem, or reference)
#         if ref_clean in self.image_cache:
#             return self.image_cache[ref_clean]
#         if ref_filename in self.image_cache:
#             return self.image_cache[ref_filename]
#         if ref_stem in self.image_cache:
#             return self.image_cache[ref_stem]
        
#         # Try direct path resolution
#         possible_paths = [
#             self.images_folder / ref_filename,
#             self.images_folder / f"{ref_stem}.jpg",
#             self.images_folder / f"{ref_stem}.png",
#             self.images_folder / reference,
#             Path(reference),
#         ]
        
#         for path in possible_paths:
#             if path.exists():
#                 return path
        
#         return None
    
#     def find_images_in_chunks(self, chunks: List[Dict]) -> List[Path]:
#         """
#         Scan multiple chunks for image references and return found image paths.
#         """
#         found_images = []
#         all_references = []
        
#         # Step 1: Extract all references from all chunks
#         for chunk in chunks:
#             content = chunk.get("content", "") + chunk.get("formatted_content", "")
#             references = self.extract_image_references(content)
#             all_references.extend(references)
            
#             # Also check if chunk already has image_path
#             if chunk.get("image_path") and chunk.get("type") == "image":
#                 all_references.append(chunk["image_path"])
        
#         # Step 2: Try to find each reference
#         for ref in set(all_references):  # Deduplicate
#             img_path = self.find_image_by_reference(ref)
#             if img_path and img_path not in found_images:
#                 found_images.append(img_path)
#                 logger.info(f"Found image: {img_path.name} (from reference: {ref[:50]})")
        
#         return found_images
    
#     def get_images_for_question(self, question: str, chunks: List[Dict]) -> List[Path]:
#         """
#         Main method: get relevant images for a question based on chunks.
#         Also checks if question itself contains chart/graph keywords.
#         """
#         found_images = self.find_images_in_chunks(chunks)
        
#         # If no images found but question is about charts, try to return any chart image
#         if not found_images and self._is_chart_question(question):
#             logger.info("Question appears chart-related but no images found in chunks. Returning any available chart image.")
#             found_images = self._get_any_chart_image()
        
#         return found_images
    
#     def _is_chart_question(self, question: str) -> bool:
#         """Detect if question is about charts/graphs."""
#         keywords = ["chart", "graph", "plot", "figure", "trajectory", 
#                    "intersect", "y-axis", "x-axis", "line", "trend"]
#         q_lower = question.lower()
#         return any(kw in q_lower for kw in keywords)
    
#     # def _get_any_chart_image(self) -> List[Path]:
#     #     """Return any image from the folder as fallback."""
#     #     if self.available_images:
#     #         # Prefer files with 'chart', 'figure', 'plot' in name
#     #         chart_like = [p for p in self.available_images 
#     #                      if any(kw in p.name.lower() for kw in ['chart', 'figure', 'plot', 'graph'])]
#     #         if chart_like:
#     #             return chart_like[:2]
#     #         return self.available_images[:2]
#     #     return []
#     def _get_any_chart_image(self) -> List[Path]:
#         """Return any image from the folder as fallback, excluding non-image files."""
#         if self.available_images:
#             # Prefer files with 'chart', 'figure', 'plot' in name
#             chart_like = [p for p in self.available_images 
#                         if any(kw in p.name.lower() for kw in ['chart', 'figure', 'plot', 'graph'])]
#             if chart_like:
#                 return chart_like[:2]
#             # Return first 2 actual images (not .gitkeep)
#             return self.available_images[:2]
#         return []


# # Quick test
# if __name__ == "__main__":
#     finder = ImageFinder("outputs/sample_digital1/auto/images")
    
#     test_text = """
#     ![Performance Chart](auto/images/figure_1.jpg)
#     As shown in Figure 1, the AIL price trend...
#     <img src="outputs/sample_digital1/auto/images/chart.png">
#     """
    
#     refs = finder.extract_image_references(test_text)
#     print(f"References found: {refs}")
    
#     for ref in refs:
#         img = finder.find_image_by_reference(ref)
#         print(f"  {ref} -> {img}")

"""
Auto-image attachment module using markdown anchor linking.
Parses actual image references from text chunks.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ImageFinder:
    """
    Finds images by parsing markdown image tags from text chunks.
    Uses anchor linking: the image reference is literally in the chunk text.
    """
    
    def __init__(self, images_folder: str = "outputs/sample_digital1/auto/images"):
        """
        Args:
            images_folder: Path to MinerU's extracted images folder
        """
        self.images_folder = Path(images_folder)
        
        # Allowed image extensions
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
        
        # Pre-load all available images for lookup
        self.available_images = {}
        if self.images_folder.exists():
            for img_path in self.images_folder.iterdir():
                if img_path.suffix.lower() in self.image_extensions and img_path.is_file():
                    self.available_images[img_path.name] = img_path
                    self.available_images[img_path.stem] = img_path
            logger.info(f"Loaded {len([k for k in self.available_images if '.' in k])} images from {images_folder}")
        else:
            logger.warning(f"Images folder not found: {images_folder}")
    
    def extract_image_from_chunk(self, chunk: Dict) -> Optional[Path]:
        """
        Extract image reference directly from a chunk's content.
        Looks for markdown image syntax: ![alt](path)
        """
        content = chunk.get("content", "") + chunk.get("formatted_content", "")
        
        # Pattern 1: Markdown image syntax (most common in MinerU)
        md_pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(md_pattern, content)
        
        for match in matches:
            # Clean the path
            clean_path = match.strip()
            # Extract filename
            filename = Path(clean_path).name
            # Try to find the file
            img_path = self._find_image_file(filename)
            if img_path:
                logger.info(f"🎯 [ANCHOR MATCHED] Found image from markdown: {filename}")
                return img_path
        
        # Pattern 2: Direct image filename in text
        filename_pattern = r'([\w\d\-_]+\.(?:jpg|jpeg|png|gif))'
        matches = re.findall(filename_pattern, content, re.IGNORECASE)
        
        for match in matches:
            img_path = self._find_image_file(match)
            if img_path:
                logger.info(f"🎯 [ANCHOR MATCHED] Found image from filename: {match}")
                return img_path
        
        return None
    
    def extract_all_images_from_chunks(self, chunks: List[Dict]) -> List[Path]:
        """
        Extract all image references from multiple chunks.
        Returns unique image paths in order of appearance.
        """
        found_images = []
        seen_paths = set()
        
        for chunk in chunks:
            img_path = self.extract_image_from_chunk(chunk)
            if img_path and str(img_path) not in seen_paths:
                found_images.append(img_path)
                seen_paths.add(str(img_path))
                logger.info(f"📎 Attaching image: {img_path.name} (from chunk type: {chunk.get('type', 'unknown')})")
        
        return found_images
    
    def _find_image_file(self, reference: str) -> Optional[Path]:
        """
        Find an image file by name or partial name.
        """
        if not reference:
            return None
        
        # Clean the reference
        ref_clean = reference.strip().lower()
        ref_name = Path(ref_clean).name
        ref_stem = Path(ref_clean).stem
        
        # Direct match by full name
        if ref_name in self.available_images:
            return self.available_images[ref_name]
        
        # Match by stem (without extension)
        if ref_stem in self.available_images:
            return self.available_images[ref_stem]
        
        # Try to find by partial match (for hashed filenames)
        for key, path in self.available_images.items():
            if ref_stem in key or key in ref_stem:
                return path
        
        return None
    
    def get_images_for_question(self, question: str, chunks: List[Dict]) -> List[Path]:
        """
        Main method: extract images directly from the retrieved chunks.
        """
        # First priority: extract from chunks using markdown syntax
        images = self.extract_all_images_from_chunks(chunks)
        
        if images:
            logger.info(f"✅ Found {len(images)} images directly from chunk content")
            return images
        
        # Fallback: try to find any chart-related image
        logger.warning("No direct image references found in chunks. Checking for chart-related question...")
        if self._is_chart_question(question):
            fallback_images = self._get_chart_images_from_folder()
            if fallback_images:
                logger.info(f"⚠️ Using fallback images: {[p.name for p in fallback_images]}")
                return fallback_images
        
        return []
    
    def _is_chart_question(self, question: str) -> bool:
        """Detect if question is about charts/graphs."""
        keywords = [
            "chart", "graph", "plot", "figure", "trajectory", "trend",
            "intersect", "y-axis", "x-axis", "line", "performance",
            "comparison", "index", "sensex", "nifty", "broad based"
        ]
        q_lower = question.lower()
        return any(kw in q_lower for kw in keywords)
    
    def _get_chart_images_from_folder(self) -> List[Path]:
        """
        Fallback: return images that look like charts (not tables).
        """
        chart_keywords = ['chart', 'plot', 'graph', 'figure', 'performance', 'comparison']
        table_keywords = ['table', 'board', 'member', 'director', 'committee', 'governance']
        
        candidates = []
        for name, path in self.available_images.items():
            if '.' not in name:  # Skip stem-only entries
                continue
            
            name_lower = name.lower()
            
            # Check if it looks like a chart
            is_chart = any(kw in name_lower for kw in chart_keywords)
            is_table = any(kw in name_lower for kw in table_keywords)
            
            if is_chart and not is_table:
                candidates.append(path)
        
        # Return up to 2 candidates
        return candidates[:2]


if __name__ == "__main__":
    # Test with a sample chunk
    finder = ImageFinder("outputs/sample_digital1/auto/images")
    
    # Simulate a chunk containing markdown image syntax
    test_chunk = {
        "content": """
## (viii) Performance in comparison to broad based indices

The performance of the Company's equity shares relative to the BSE Sensex and NSE Nifty is tracked below:

![](auto/images/image_e76dba.png)

The following tables show the high and low prices...
        """,
        "type": "text"
    }
    
    img = finder.extract_image_from_chunk(test_chunk)
    print(f"Extracted image: {img}")