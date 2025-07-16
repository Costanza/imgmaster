#!/usr/bin/env python3
"""
Debug script to examine HEIC EXIF data structure.
"""

from pathlib import Path
from PIL import Image
import pillow_heif

# Register HEIF support
pillow_heif.register_heif_opener()

def debug_heic_exif():
    """Debug HEIC EXIF data structure."""
    photo_dir = Path("/Users/chris/Pictures/Import/Process")
    heic_file = next(photo_dir.glob("*.heic"), None)
    
    if not heic_file:
        print("❌ No HEIC files found")
        return
    
    print(f"🔍 Debugging EXIF data for: {heic_file.name}")
    print("=" * 60)
    
    with Image.open(heic_file) as img:
        exif_data = img.getexif()
        
        print(f"📊 Total EXIF tags found: {len(exif_data)}")
        print("\n🏷️  All EXIF tags:")
        print("-" * 30)
        
        for tag_id, value in exif_data.items():
            try:
                tag_name = Image.ExifTags.TAGS.get(tag_id, f"Unknown_{tag_id}")
                print(f"{tag_id:5d} ({tag_name:20s}): {repr(value)}")
            except Exception as e:
                print(f"{tag_id:5d} (Error reading tag): {e}")
        
        # Check for sub-IFDs
        print(f"\n📷 Looking for DateTimeOriginal (tag 36868)...")
        date_original = exif_data.get(36868)
        print(f"   DateTimeOriginal: {date_original}")
        
        # Check standard DateTime tag (306)
        date_time = exif_data.get(306)
        print(f"   DateTime: {date_time}")
        
        # Try to get EXIF sub-directory
        print(f"\n🔍 Checking for EXIF Sub-IFD...")
        exif_ifd_tag = exif_data.get(34665)  # ExifIFD pointer
        print(f"   ExifIFD pointer: {exif_ifd_tag}")
        
        if hasattr(exif_data, 'get_ifd'):
            try:
                exif_sub = exif_data.get_ifd(34665)
                print(f"   EXIF Sub-IFD tags: {len(exif_sub)}")
                
                for tag_id, value in exif_sub.items():
                    tag_name = Image.ExifTags.TAGS.get(tag_id, f"Unknown_{tag_id}")
                    if 'date' in tag_name.lower() or tag_id in [36867, 36868, 306]:
                        print(f"   {tag_id:5d} ({tag_name:20s}): {repr(value)}")
                        
                # Look specifically for DateTimeOriginal in sub-IFD
                date_original_sub = exif_sub.get(36868)
                print(f"\n📅 DateTimeOriginal in sub-IFD: {date_original_sub}")
                
            except Exception as e:
                print(f"   Error reading EXIF Sub-IFD: {e}")

if __name__ == "__main__":
    debug_heic_exif()
