#!/usr/bin/env python3
"""
Test script to verify HEIC metadata extraction is working.
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

def test_heic_extraction():
    """Test HEIC file metadata extraction."""
    print("🧪 Testing HEIC metadata extraction...")
    print("=" * 50)
    
    # Find a HEIC file from the photo directory
    photo_dir = Path("/Users/chris/Pictures/Import/Process")
    heic_files = list(photo_dir.glob("*.heic"))[:3]  # Test first 3 HEIC files
    
    if not heic_files:
        print("❌ No HEIC files found in the directory")
        return
    
    extractor = MetadataExtractor()
    
    for heic_file in heic_files:
        print(f"\n📸 Testing: {heic_file.name}")
        print("-" * 30)
        
        try:
            metadata = extractor.extract_from_photo(heic_file)
            
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
            logger.exception(f"Error processing {heic_file}")

if __name__ == "__main__":
    test_heic_extraction()
