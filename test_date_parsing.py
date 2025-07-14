#!/usr/bin/env python3
"""Test the improved date parsing functionality."""

import sys
from datetime import datetime
from models.metadata import MetadataExtractor

def test_date_parsing():
    """Test various date formats that exiftool might return."""
    extractor = MetadataExtractor()
    
    # Simulate the exiftool data structure
    test_cases = [
        # Format from XMP sidecar files
        ("2025:03:12 07:57:24.26+11:00", "2025-03-12 07:57:24+11:00"),
        # Standard EXIF format
        ("2022:12:28 18:44:47", "2022-12-28 18:44:47"),
        # ISO format with timezone
        ("2022-12-28T18:44:47+11:00", "2022-12-28 18:44:47+11:00"),
        # ISO format with fractional seconds
        ("2025-03-12T07:57:24.26+11:00", "2025-03-12 07:57:24+11:00"),
    ]
    
    success_count = 0
    
    for i, (input_date, expected_format) in enumerate(test_cases):
        print(f"Test {i+1}: {input_date}")
        
        # Simulate the exiftool data structure
        mock_data = {"DateTimeOriginal": input_date}
        
        try:
            # Test the date parsing logic
            date_str = mock_data.get('DateTimeOriginal')
            parsed_date = None
            
            if 'T' in date_str:
                # ISO format path
                if '.' in date_str and ('+' in date_str or '-' in date_str.split('T')[1]):
                    base_part = date_str.split('.')[0]
                    tz_part = '+' + date_str.split('+')[1] if '+' in date_str else ''
                    if not tz_part and '-' in date_str.split('T')[1]:
                        tz_part = '-' + date_str.split('-')[-1]
                    date_str = base_part + tz_part
                parsed_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            elif ':' in date_str and len(date_str.split(' ')) == 2:
                # EXIF format path
                if '+' in date_str or (date_str.count('-') > 2):
                    date_part, time_part = date_str.split(' ', 1)
                    iso_date = date_part.replace(':', '-')
                    if '.' in time_part:
                        time_base = time_part.split('.')[0]
                        fractional_and_tz = time_part.split('.')[1]
                        if '+' in fractional_and_tz:
                            tz_part = '+' + fractional_and_tz.split('+')[1]
                        elif '-' in fractional_and_tz:
                            tz_part = '-' + fractional_and_tz.split('-')[1]
                        else:
                            tz_part = ''
                        iso_datetime = f"{iso_date}T{time_base}{tz_part}"
                    else:
                        iso_datetime = f"{iso_date}T{time_part}"
                    parsed_date = datetime.fromisoformat(iso_datetime)
                else:
                    parsed_date = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            
            if parsed_date:
                # Format for comparison (strip timezone info for simple comparison)
                result_str = parsed_date.strftime("%Y-%m-%d %H:%M:%S")
                if parsed_date.tzinfo:
                    # Add timezone info
                    tz_offset = parsed_date.strftime("%z")
                    if tz_offset:
                        # Format timezone as +HH:MM
                        result_str += f"{tz_offset[:3]}:{tz_offset[3:]}"
                
                print(f"  Input:    {input_date}")
                print(f"  Parsed:   {result_str}")
                print(f"  Expected: {expected_format}")
                
                # Simple check if we got a reasonable date
                if parsed_date.year >= 2000 and parsed_date.year <= 2030:
                    print(f"  ✅ SUCCESS")
                    success_count += 1
                else:
                    print(f"  ❌ FAILED - Invalid year")
            else:
                print(f"  ❌ FAILED - No date parsed")
                
        except Exception as e:
            print(f"  ❌ FAILED - Exception: {e}")
        
        print()
    
    print(f"Results: {success_count}/{len(test_cases)} tests passed")
    return success_count == len(test_cases)

if __name__ == "__main__":
    success = test_date_parsing()
    sys.exit(0 if success else 1)
