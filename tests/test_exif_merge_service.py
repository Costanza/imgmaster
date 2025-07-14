import unittest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, call

from services.exif_merge_service import ExifMergeService


class TestExifMergeService(unittest.TestCase):
    """Test cases for the ExifMergeService."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.service = ExifMergeService()
        self.test_uuid = "test-uuid-12345"
        
    def tearDown(self):
        """Clean up after each test method."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_file(self, filename: str, content: bytes = b"fake image data") -> Path:
        """Create a test file and return its path."""
        file_path = Path(self.temp_dir) / filename
        with open(file_path, 'wb') as f:
            f.write(content)
        return file_path
    
    @patch('services.exif_merge_service.piexif')
    def test_merge_uuid_into_jpeg_success(self, mock_piexif):
        """Test successful UUID merge into JPEG file."""
        # Setup mock
        mock_exif_dict = {
            'Exif': {},
            '0th': {},
            '1st': {},
            'thumbnail': None,
            'GPS': {}
        }
        mock_piexif.load.return_value = mock_exif_dict
        mock_piexif.ExifIFD.UserComment = 37510
        mock_piexif.dump.return_value = b"mock_exif_bytes"
        
        # Create test file
        test_file = self.create_test_file("test.jpg")
        
        # Execute
        result = self.service.merge_uuid_into_jpeg(test_file, self.test_uuid)
        
        # Verify
        self.assertTrue(result)
        mock_piexif.load.assert_called_once_with(str(test_file))
        
        # Check that UUID was added to EXIF dict
        expected_comment = f"UUID:{self.test_uuid}".encode('utf-8')
        self.assertEqual(mock_exif_dict['Exif'][37510], expected_comment)
        
        mock_piexif.dump.assert_called_once_with(mock_exif_dict)
        mock_piexif.insert.assert_called_once_with(b"mock_exif_bytes", str(test_file))
    
    @patch('services.exif_merge_service.piexif')
    def test_merge_uuid_into_jpeg_failure(self, mock_piexif):
        """Test UUID merge failure for JPEG file."""
        # Setup mock to raise exception
        mock_piexif.load.side_effect = Exception("Failed to load EXIF")
        
        # Create test file
        test_file = self.create_test_file("test.jpg")
        
        # Execute
        result = self.service.merge_uuid_into_jpeg(test_file, self.test_uuid)
        
        # Verify
        self.assertFalse(result)
        mock_piexif.load.assert_called_once_with(str(test_file))
    
    @patch('services.exif_merge_service.subprocess')
    def test_merge_uuid_into_raw_or_heic_success(self, mock_subprocess):
        """Test successful UUID merge into RAW/HEIC file."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_subprocess.run.return_value = mock_result
        
        # Create test file
        test_file = self.create_test_file("test.cr2")
        
        # Execute
        result = self.service.merge_uuid_into_raw_or_heic(test_file, self.test_uuid)
        
        # Verify
        self.assertTrue(result)
        mock_subprocess.run.assert_called_once_with([
            "exiftool",
            "-overwrite_original",
            f"-XMP:ImageUniqueID={self.test_uuid}",
            str(test_file)
        ], capture_output=True, text=True)
    
    @patch('services.exif_merge_service.subprocess')
    def test_merge_uuid_into_raw_or_heic_failure(self, mock_subprocess):
        """Test UUID merge failure for RAW/HEIC file."""
        # Setup mock to return error
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "ExifTool error message"
        mock_subprocess.run.return_value = mock_result
        
        # Create test file
        test_file = self.create_test_file("test.nef")
        
        # Execute
        result = self.service.merge_uuid_into_raw_or_heic(test_file, self.test_uuid)
        
        # Verify
        self.assertFalse(result)
        mock_subprocess.run.assert_called_once_with([
            "exiftool",
            "-overwrite_original",
            f"-XMP:ImageUniqueID={self.test_uuid}",
            str(test_file)
        ], capture_output=True, text=True)
    
    @patch('services.exif_merge_service.subprocess')
    def test_merge_uuid_into_raw_or_heic_exception(self, mock_subprocess):
        """Test UUID merge exception handling for RAW/HEIC file."""
        # Setup mock to raise exception
        mock_subprocess.run.side_effect = Exception("Subprocess failed")
        
        # Create test file
        test_file = self.create_test_file("test.arw")
        
        # Execute
        result = self.service.merge_uuid_into_raw_or_heic(test_file, self.test_uuid)
        
        # Verify
        self.assertFalse(result)
    
    @patch.object(ExifMergeService, 'merge_uuid_into_jpeg')
    def test_merge_uuid_jpeg_dispatch(self, mock_jpeg_merge):
        """Test that JPEG files are dispatched to JPEG merge method."""
        mock_jpeg_merge.return_value = True
        
        test_file = self.create_test_file("test.jpg")
        result = self.service.merge_uuid(test_file, self.test_uuid)
        
        self.assertTrue(result)
        mock_jpeg_merge.assert_called_once_with(test_file, self.test_uuid)
    
    @patch.object(ExifMergeService, 'merge_uuid_into_jpeg')
    def test_merge_uuid_jpeg_case_insensitive(self, mock_jpeg_merge):
        """Test that JPEG files with different cases are handled correctly."""
        mock_jpeg_merge.return_value = True
        
        # Test various cases
        test_cases = ["test.JPG", "test.jpeg", "test.JPEG"]
        for filename in test_cases:
            with self.subTest(filename=filename):
                test_file = self.create_test_file(filename)
                result = self.service.merge_uuid(test_file, self.test_uuid)
                self.assertTrue(result)
        
        # Should be called once for each test case
        self.assertEqual(mock_jpeg_merge.call_count, len(test_cases))
    
    @patch.object(ExifMergeService, 'merge_uuid_into_raw_or_heic')
    def test_merge_uuid_raw_formats_dispatch(self, mock_raw_merge):
        """Test that various RAW formats are dispatched to RAW merge method."""
        mock_raw_merge.return_value = True
        
        raw_formats = ['.cr2', '.nef', '.arw', '.dng', '.rw2', '.orf', '.raf', '.pef', '.srw']
        
        for ext in raw_formats:
            with self.subTest(extension=ext):
                test_file = self.create_test_file(f"test{ext}")
                result = self.service.merge_uuid(test_file, self.test_uuid)
                self.assertTrue(result)
        
        # Should be called once for each format
        self.assertEqual(mock_raw_merge.call_count, len(raw_formats))
    
    @patch.object(ExifMergeService, 'merge_uuid_into_raw_or_heic')
    def test_merge_uuid_heic_formats_dispatch(self, mock_raw_merge):
        """Test that HEIC formats are dispatched to RAW/HEIC merge method."""
        mock_raw_merge.return_value = True
        
        heic_formats = ['.heic', '.heif']
        
        for ext in heic_formats:
            with self.subTest(extension=ext):
                test_file = self.create_test_file(f"test{ext}")
                result = self.service.merge_uuid(test_file, self.test_uuid)
                self.assertTrue(result)
        
        # Should be called once for each format
        self.assertEqual(mock_raw_merge.call_count, len(heic_formats))
    
    def test_merge_uuid_unsupported_format(self):
        """Test that unsupported formats return False."""
        unsupported_formats = ['.png', '.gif', '.txt', '.mp4', '.pdf']
        
        for ext in unsupported_formats:
            with self.subTest(extension=ext):
                test_file = self.create_test_file(f"test{ext}")
                result = self.service.merge_uuid(test_file, self.test_uuid)
                self.assertFalse(result)
    
    @patch.object(ExifMergeService, 'merge_uuid_into_jpeg')
    @patch.object(ExifMergeService, 'merge_uuid_into_raw_or_heic')
    def test_merge_uuid_method_not_called_for_unsupported(self, mock_raw_merge, mock_jpeg_merge):
        """Test that merge methods are not called for unsupported formats."""
        test_file = self.create_test_file("test.png")
        result = self.service.merge_uuid(test_file, self.test_uuid)
        
        self.assertFalse(result)
        mock_jpeg_merge.assert_not_called()
        mock_raw_merge.assert_not_called()
    
    @patch('services.exif_merge_service.piexif')
    def test_merge_uuid_into_jpeg_preserves_existing_exif(self, mock_piexif):
        """Test that existing EXIF data is preserved when adding UUID."""
        # Setup mock with existing EXIF data
        existing_exif_dict = {
            'Exif': {
                36867: "2023:01:01 12:00:00",  # DateTimeOriginal
                34855: 100,  # ISO
            },
            '0th': {
                271: "Canon",  # Make
                272: "EOS R5",  # Model
            },
            '1st': {},
            'thumbnail': None,
            'GPS': {}
        }
        
        mock_piexif.load.return_value = existing_exif_dict
        mock_piexif.ExifIFD.UserComment = 37510
        mock_piexif.dump.return_value = b"mock_exif_bytes"
        
        # Create test file
        test_file = self.create_test_file("test.jpg")
        
        # Execute
        result = self.service.merge_uuid_into_jpeg(test_file, self.test_uuid)
        
        # Verify
        self.assertTrue(result)
        
        # Check that existing EXIF data is preserved
        self.assertEqual(existing_exif_dict['Exif'][36867], "2023:01:01 12:00:00")
        self.assertEqual(existing_exif_dict['Exif'][34855], 100)
        self.assertEqual(existing_exif_dict['0th'][271], "Canon")
        self.assertEqual(existing_exif_dict['0th'][272], "EOS R5")
        
        # Check that UUID was added
        expected_comment = f"UUID:{self.test_uuid}".encode('utf-8')
        self.assertEqual(existing_exif_dict['Exif'][37510], expected_comment)


if __name__ == '__main__':
    unittest.main()
