#!/usr/bin/env python3
"""
Test script to verify RAF metadata extraction is working.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from pathlib import Path
from models.metadata import MetadataExtractor

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_raf_extraction():
    """Test RAF file metadata extraction."""
    print("🧪 Testing RAF metadata extraction...")
    print("=" * 50)
    
    # Find a RAF file from the photo directory
    photo_dir = Path("/Users/chris/Pictures/Import/Process")
    raf_files = list(photo_dir.glob("*.RAF"))[:3]  # Test first 3 RAF files
    
    if not raf_files:
        print("❌ No RAF files found in the directory")
        return
    
    extractor = MetadataExtractor()
    
    for raf_file in raf_files:
        print(f"\n📸 Testing: {raf_file.name}")
        print("-" * 30)
        
        try:
            metadata = extractor.extract_from_photo(raf_file)
            
            print(f"🏷️  Camera: {metadata.camera.make} {metadata.camera.model}")
            print(f"📅 Date taken: {metadata.dates.date_taken}")
            print(f"🔧 ISO: {metadata.technical.iso}")
            print(f"📷 Aperture: f/{metadata.technical.aperture}" if metadata.technical.aperture else "📷 Aperture: None")
            print(f"🔍 Focal length: {metadata.technical.focal_length}mm" if metadata.technical.focal_length else "🔍 Focal length: None")
            print(f"🏷️  Keywords: {metadata.keywords.keywords}" if metadata.keywords.keywords else "🏷️  Keywords: None")
            print(f"📄 Source: {metadata.source_file}")
            
            if metadata.dates.date_taken:
                print("✅ Date extraction successful!")
            else:
                print("❌ Date extraction failed!")
                
        except Exception as e:
            print(f"❌ Error extracting metadata: {e}")
            logger.exception(f"Error processing {raf_file}")

if __name__ == "__main__":
    test_raf_extraction()
