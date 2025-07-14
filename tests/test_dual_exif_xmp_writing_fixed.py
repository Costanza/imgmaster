"""Test dual EXIF/XMP UUID writing functionality."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.rename_service import PhotoRenameService


class TestDualExifXmpWriting(unittest.TestCase):
    """Test dual EXIF and XMP UUID writing functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = PhotoRenameService()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.uuid = "test-uuid-12345"
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_to_jpeg_file_dual_writing(self, mock_xmp_write, mock_exif_write):
        """Test that JPEG files get both EXIF and XMP sidecar UUID writing."""
        # Setup mocks
        mock_exif_write.return_value = True
        mock_xmp_write.return_value = True

        # Create test JPEG file
        jpeg_path = self.temp_dir / "test.jpg"
        jpeg_path.write_bytes(b"fake jpeg data")

        # Execute
        result = self.service._write_uuid_to_file(jpeg_path, self.uuid)

        # Verify
        self.assertTrue(result)
        mock_exif_write.assert_called_once_with(jpeg_path, self.uuid)
        mock_xmp_write.assert_called_once_with(jpeg_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_to_raw_file_dual_writing(self, mock_xmp_write, mock_exif_write):
        """Test that RAW files get both EXIF and XMP sidecar UUID writing."""
        # Setup mocks
        mock_exif_write.return_value = True
        mock_xmp_write.return_value = True

        # Create test RAW file
        raw_path = self.temp_dir / "test.cr2"
        raw_path.write_bytes(b"fake raw data")

        # Execute
        result = self.service._write_uuid_to_file(raw_path, self.uuid)

        # Verify
        self.assertTrue(result)
        mock_exif_write.assert_called_once_with(raw_path, self.uuid)
        mock_xmp_write.assert_called_once_with(raw_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_to_heic_file_dual_writing(self, mock_xmp_write, mock_exif_write):
        """Test that HEIC files get both EXIF and XMP sidecar UUID writing."""
        # Setup mocks
        mock_exif_write.return_value = True
        mock_xmp_write.return_value = True

        # Create test HEIC file
        heic_path = self.temp_dir / "test.heic"
        heic_path.write_bytes(b"fake heic data")

        # Execute
        result = self.service._write_uuid_to_file(heic_path, self.uuid)

        # Verify
        self.assertTrue(result)
        mock_exif_write.assert_called_once_with(heic_path, self.uuid)
        mock_xmp_write.assert_called_once_with(heic_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_partial_success_still_returns_true(self, mock_xmp_write, mock_exif_write):
        """Test that if either EXIF or XMP writing succeeds, the operation is considered successful."""
        # Setup mocks - EXIF fails but XMP succeeds
        mock_exif_write.return_value = False
        mock_xmp_write.return_value = True

        # Create test file
        jpeg_path = self.temp_dir / "test.jpg"
        jpeg_path.write_bytes(b"fake jpeg data")

        # Execute
        result = self.service._write_uuid_to_file(jpeg_path, self.uuid)

        # Verify - should still return True because XMP succeeded
        self.assertTrue(result)
        mock_exif_write.assert_called_once_with(jpeg_path, self.uuid)
        mock_xmp_write.assert_called_once_with(jpeg_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_both_fail_returns_false(self, mock_xmp_write, mock_exif_write):
        """Test that if both EXIF and XMP writing fail, the operation returns False."""
        # Setup mocks - both fail
        mock_exif_write.return_value = False
        mock_xmp_write.return_value = False

        # Create test file
        jpeg_path = self.temp_dir / "test.jpg"
        jpeg_path.write_bytes(b"fake jpeg data")

        # Execute
        result = self.service._write_uuid_to_file(jpeg_path, self.uuid)

        # Verify - should return False because both failed
        self.assertFalse(result)
        mock_exif_write.assert_called_once_with(jpeg_path, self.uuid)
        mock_xmp_write.assert_called_once_with(jpeg_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_to_xmp_file_direct(self, mock_xmp_write):
        """Test that XMP files are handled directly without EXIF writing attempt."""
        # Setup mock
        mock_xmp_write.return_value = True

        # Create test XMP file
        xmp_path = self.temp_dir / "test.xmp"
        xmp_path.write_text("<?xml version='1.0'?><x:xmpmeta/>")

        # Execute
        result = self.service._write_uuid_to_file(xmp_path, self.uuid)

        # Verify
        self.assertTrue(result)
        mock_xmp_write.assert_called_once_with(xmp_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_unsupported_format_attempts_both_methods(self, mock_xmp_write, mock_exif_write):
        """Test that unsupported formats still attempt both EXIF and XMP writing for maximum compatibility."""
        # Setup mocks - both return False for unsupported format
        mock_exif_write.return_value = False
        mock_xmp_write.return_value = False

        # Create test file with unsupported format
        txt_path = self.temp_dir / "test.txt"
        txt_path.write_text("some text content")

        # Execute
        result = self.service._write_uuid_to_file(txt_path, self.uuid)

        # Verify - should return False but still attempt both methods for compatibility
        self.assertFalse(result)
        mock_exif_write.assert_called_once_with(txt_path, self.uuid)
        mock_xmp_write.assert_called_once_with(txt_path, self.uuid, [])

    @patch.object(PhotoRenameService, '_write_uuid_to_exif')
    @patch.object(PhotoRenameService, '_write_uuid_to_xmp_sidecar')
    def test_write_uuid_always_writes_xmp_for_compatibility(self, mock_xmp_write, mock_exif_write):
        """Test that XMP sidecar is always written for maximum compatibility."""
        # Setup mocks
        mock_exif_write.return_value = True
        mock_xmp_write.return_value = True

        # Create test file
        jpeg_path = self.temp_dir / "test.jpg"
        jpeg_path.write_bytes(b"fake jpeg data")

        # Execute
        result = self.service._write_uuid_to_file(jpeg_path, self.uuid)

        # Verify both methods were called even though EXIF succeeded
        self.assertTrue(result)
        mock_exif_write.assert_called_once_with(jpeg_path, self.uuid)
        mock_xmp_write.assert_called_once_with(jpeg_path, self.uuid, [])


if __name__ == '__main__':
    unittest.main()
