# find_outputs.py
import os
from pathlib import Path

# Check all possible output locations
print("Checking for MinerU outputs...")

# Check current outputs folder
outputs_dir = Path("outputs")
if outputs_dir.exists():
    print(f"\nContents of 'outputs/':")
    for item in outputs_dir.iterdir():
        if item.is_dir():
            print(f"  Folder: {item.name}/")
            for subitem in item.iterdir():
                print(f"    - {subitem.name}")
        else:
            print(f"  File: {item.name}")

# Also check for magic-pdf default folders
magic_dir = Path("magic-pdf")
if magic_dir.exists():
    print(f"\nContents of 'magic-pdf/':")
    for item in magic_dir.iterdir():
        print(f"  {item.name}")

# Check current directory for any markdown files
print(f"\nMarkdown files in current directory:")
for md in Path(".").glob("*.md"):
    print(f"  {md.name}")