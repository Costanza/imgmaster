#!/usr/bin/env python3
"""Test script to verify RAW format detection and exiftool usage."""

import sys
from pathlib import Path
from models.metadata import MetadataExtractor

def test_raw_detection():
    """Test that RAW formats are properly detected."""
    extractor = MetadataExtractor()
    
    # Test various RAW formats
    test_files = [
        Path("test.raf"),  # Fujifilm
        Path("test.cr3"),  # Canon
        Path("test.cr2"),  # Canon
        Path("test.nef"),  # Nikon
        Path("test.arw"),  # Sony
        Path("test.jpg"),  # JPEG (should be False)
        Path("test.heic"), # HEIC (should be False for RAW check)
    ]
    
    expected_results = [
        True,   # RAF
        True,   # CR3
        True,   # CR2
        True,   # NEF
        True,   # ARW
        False,  # JPG
        False,  # HEIC
    ]
    
    for i, test_file in enumerate(test_files):
        result = extractor._is_raw_format(test_file)
        expected = expected_results[i]
        print(f"{test_file.suffix.upper():>5}: {result:>5} (expected: {expected})")
        
        if result != expected:
            print(f"ERROR: Expected {expected}, got {result} for {test_file}")
            return False
    
    print("✅ All RAW format detection tests passed!")
    return True

if __name__ == "__main__":
    success = test_raw_detection()
    sys.exit(0 if success else 1)
