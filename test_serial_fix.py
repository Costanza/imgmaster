#!/usr/bin/env python3
"""Test the serial number fix for integer serial numbers."""

import tempfile
import json
from pathlib import Path
from models.photo_group import PhotoGroupManager
from services.rename_service import PhotoRenameService

def test_serial_number_conversion():
    """Test that integer serial numbers are properly converted to strings."""
    
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a mock database with an integer serial number (like in your real data)
        mock_database = {
            "metadata": {
                "total_groups": 1,
                "total_valid_groups": 1,
                "total_invalid_groups": 0,
                "total_photos": 1,
                "created_by": "imgmaster",
                "version": "1.0"
            },
            "groups": {
                "test_group": {
                    "basename": "test_group",
                    "uuid": "test-uuid",
                    "count": 1,
                    "is_valid": True,
                    "has_only_supplementary_files": False,
                    "formats": {
                        "jpeg": False,
                        "raw": True,
                        "heic": False,
                        "live_photo": False,
                        "sidecar": False,
                        "other": False
                    },
                    "metadata": {
                        "camera": {
                            "make": "Canon",
                            "make_source": "test.cr2",
                            "model": "Canon EOS R6m2",
                            "model_source": "test.cr2",
                            "lens_model": None,
                            "lens_model_source": None,
                            "serial_number": 155021000129,  # INTEGER like in your data
                            "serial_number_source": "test.cr2"
                        },
                        "dates": {
                            "date_taken": "2024-04-03T00:32:22",
                            "date_taken_source": "test.cr2"
                        },
                        "technical": {
                            "iso": 800,
                            "iso_source": "test.cr2",
                            "aperture": 6.3,
                            "aperture_source": "test.cr2",
                            "shutter_speed": "1/1000",
                            "shutter_speed_source": "test.cr2",
                            "focal_length": 240.0,
                            "focal_length_source": "test.cr2",
                            "focal_length_35mm": None,
                            "focal_length_35mm_source": None,
                            "flash_fired": False,
                            "flash_fired_source": "test.cr2"
                        },
                        "keywords": {
                            "keywords": [],
                            "keywords_source": None
                        },
                        "source_file": "group:test_group"
                    },
                    "photos": [
                        {
                            "filename": "test.cr2",
                            "basename": "test_group",
                            "extension": ".cr2",
                            "absolute_path": str(temp_path / "test.cr2"),
                            "format_classification": "raw",
                            "size_bytes": 1000,
                            "size_mb": 0.001,
                            "history": []
                        }
                    ]
                }
            }
        }
        
        # Create the mock file
        test_file = temp_path / "test.cr2"
        test_file.write_bytes(b"mock CR2 data")
        
        # Save the mock database
        db_path = temp_path / "test_database.json"
        with open(db_path, 'w') as f:
            json.dump(mock_database, f)
        
        # Create destination directory
        dest_dir = temp_path / "output"
        dest_dir.mkdir()
        
        # Test the rename service
        rename_service = PhotoRenameService()
        
        try:
            # This should not raise an error about int vs string
            results = rename_service.rename_photos(
                database=db_path,
                destination=dest_dir,
                scheme="{date}_{camera_model}_{serial_number}",
                sequence_digits=3,
                dry_run=True,  # Don't actually move files
                copy=False,
                skip_invalid=True,
                write_uuid=False
            )
            
            print("✅ SUCCESS: Serial number conversion works correctly")
            print(f"   Results: {results.total_processed} groups processed")
            return True
            
        except Exception as e:
            print(f"❌ FAILED: {e}")
            return False

if __name__ == "__main__":
    success = test_serial_number_conversion()
    exit(0 if success else 1)
