#!/usr/bin/env python3
"""
Simple test to verify keyword functionality is working.
"""
import sys
import os

# Add the parent directory to Python path
sys.path.insert(0, os.path.abspath('.'))

from models.metadata import MetadataExtractor, KeywordInfo
from pathlib import Path

def test_keyword_functionality():
    """Test that keyword extraction is working properly."""
    print("Testing keyword functionality...")
    
    # Test with a real HEIC file that has keywords
    heic_path = Path("/Users/chris/Pictures/Import/Completed/2022/20221228/20221228_0004.heic")
    
    if heic_path.exists():
        print(f"Testing with: {heic_path}")
        
        extractor = MetadataExtractor()
        metadata = extractor.extract_from_photo(heic_path)
        
        print(f"Keywords found: {metadata.keywords.keywords}")
        print(f"Keywords source: {metadata.source_file}")
        
        if metadata.keywords.keywords:
            print("✓ Keywords successfully extracted from HEIC file")
        else:
            print("✗ No keywords found in HEIC file")
            
        # Test empty keyword info
        keyword_info = KeywordInfo()
        print(f"Empty keywords: {keyword_info.keywords}")
        
    else:
        print(f"Test file not found: {heic_path}")
        
    print("Keyword functionality test complete.")

if __name__ == "__main__":
    test_keyword_functionality()
