"""
Test Gemini's vision capability on extracted charts.
"""

import os
from pathlib import Path
import sys

# Add src to path
sys.path.append(str(Path(__file__).parent))

from gemini_client import GeminiClient


def test_chart_understanding(image_path: str, question: str):
    """
    Test Gemini's ability to understand a chart image.
    """
    client = GeminiClient()
    
    # Load image as bytes
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    # Import PIL for image handling
    from PIL import Image
    import io
    
    image = Image.open(io.BytesIO(image_bytes))
    
    # Prepare prompt
    prompt = f"""Analyze this chart from a company annual report and answer the following question:

QUESTION: {question}

Provide specific numbers, trends, or insights visible in the chart. Be precise."""

    print(f"Analyzing: {Path(image_path).name}")
    print(f"Question: {question}")
    print("-" * 50)
    
    # Generate response with image
    response = client.generate_with_image(prompt, image_path)
    
    print(f"\nANSWER:\n{response}")
    return response


def list_available_images(images_folder: str = "outputs/sample_digital1/auto/images"):
    """List all extracted images."""
    images_path = Path(images_folder)
    
    if not images_path.exists():
        print(f"Images folder not found: {images_path}")
        return []
    
    images = list(images_path.glob("*.jpg")) + list(images_path.glob("*.png"))
    
    print(f"\nAvailable images ({len(images)}):")
    for img in images:
        size = img.stat().st_size / 1024  # KB
        print(f"  - {img.name} ({size:.1f} KB)")
    
    return images


if __name__ == "__main__":
    # List all available images
    images = list_available_images()
    
    if images:
        # Test on first image
        test_image = images[0]
        test_question = "What does this chart show? Describe the main trend or key insights."
        
        test_chart_understanding(str(test_image), test_question)
    else:
        print("No images found. Run MinerU extraction first.")