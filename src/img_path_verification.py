import json
from pathlib import Path  # Fixed: Added missing import to prevent NameError

# Fixed: Added encoding="utf-8" to handle advanced characters smoothly
with open("outputs/sample_digital1_chunks.json", 'r', encoding="utf-8") as f:
    chunks = json.load(f)

for chunk in chunks:
    if chunk.get("type") == "image":
        image_path = chunk.get('image_path', '')
        print(f"Chunk {chunk.get('chunk_id')}: {image_path}")
        print(f"   Exists: {Path(image_path).exists()}")