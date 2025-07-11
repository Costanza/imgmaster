#!/usr/bin/env python3
"""
Demo script for testing the imgmaster build functionality.

This script creates a sample directory structure with various photo types
and demonstrates the build command functionality.
"""

import os
import tempfile
import shutil
from pathlib import Path

# Sample photo file extensions and content
SAMPLE_FILES = [
    # RAW + JPEG pairs
    ("vacation_001.cr2", "Canon RAW"),
    ("vacation_001.jpg", "JPEG version"),
    ("vacation_001.xmp", "XMP sidecar"),
    
    ("vacation_002.nef", "Nikon RAW"),
    ("vacation_002.jpg", "JPEG version"),
    
    # HEIC + Live Photo
    ("portrait.heic", "HEIC photo"),
    ("portrait.mov", "Live photo video"),
    
    # Single files
    ("landscape.png", "PNG image"),
    ("screenshot.gif", "GIF image"),
    ("scan.tiff", "TIFF scan"),
    
    # Subdirectory with more photos
    ("family/wedding.arw", "Sony RAW"),
    ("family/wedding.jpg", "JPEG version"),
    ("family/group_photo.heic", "HEIC group photo"),
    
    # Nested subdirectory
    ("family/kids/birthday.cr3", "Canon CR3 RAW"),
    ("family/kids/birthday.jpg", "JPEG version"),
    ("family/kids/playground.png", "PNG photo"),
    
    # Non-photo files (should be ignored)
    ("readme.txt", "Text file"),
    ("video.mp4", "Video file"),
    ("family/notes.doc", "Document file"),
]


def create_demo_directory(base_path: Path) -> None:
    """Create a demo directory structure with sample photos."""
    print(f"Creating demo directory structure in: {base_path}")
    
    for filepath, content in SAMPLE_FILES:
        full_path = base_path / filepath
        
        # Create parent directories if needed
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file
        with open(full_path, 'w') as f:
            f.write(content)
    
    print(f"Created {len(SAMPLE_FILES)} sample files")


def main():
    """Main demo function."""
    print("🚀 ImgMaster Build Command Demo")
    print("=" * 40)
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        demo_dir = Path(temp_dir) / "demo_photos"
        demo_dir.mkdir()
        
        # Create sample files
        create_demo_directory(demo_dir)
        
        print(f"\n📁 Demo directory created at: {demo_dir}")
        print("\nDirectory structure:")
        
        # Show directory structure
        for root, dirs, files in os.walk(demo_dir):
            level = root.replace(str(demo_dir), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in sorted(files):
                print(f"{subindent}{file}")
        
        print(f"\n🔧 To test the build command, run:")
        print(f"python main.py build \"{demo_dir}\" --output demo_database.json --verbose")
        
        print(f"\n📊 Expected results:")
        print(f"  - Should find photo files and group them by basename")
        print(f"  - vacation_001: 3 files (.cr2, .jpg, .xmp)")
        print(f"  - vacation_002: 2 files (.nef, .jpg)")
        print(f"  - portrait: 2 files (.heic, .mov)")
        print(f"  - And several other groups")
        print(f"  - Non-photo files should be ignored")
        
        # Wait for user to test
        input(f"\nPress Enter to clean up the demo directory...")
    
    print("✅ Demo completed!")


if __name__ == "__main__":
    main()
