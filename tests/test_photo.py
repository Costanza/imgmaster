import unittest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from models.photo import Photo


class TestPhoto(unittest.TestCase):
    """Test cases for the Photo model."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Clean up after each test method."""
        # Clean up temp files if they exist
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, filename: str) -> str:
        """Create a temporary file for testing."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write("test content")
        return file_path
    
    def test_format_classifications(self):
        """Test that format classifications are correctly defined."""
        # Test JPEG formats
        self.assertEqual(Photo.JPEG_FORMATS, {'.jpg', '.jpeg'})
        
        # Test that RAW formats include expected extensions
        self.assertIn('.cr2', Photo.RAW_FORMATS)  # Canon
        self.assertIn('.nef', Photo.RAW_FORMATS)  # Nikon
        self.assertIn('.arw', Photo.RAW_FORMATS)  # Sony
        self.assertIn('.dng', Photo.RAW_FORMATS)  # Adobe
        
        # Test HEIC formats
        self.assertEqual(Photo.HEIC_FORMATS, {'.heif', '.heic', '.hif'})
        
        # Test Live Photo formats
        self.assertEqual(Photo.LIVE_PHOTO_FORMATS, {'.mov'})
        
        # Test Sidecar formats
        self.assertIn('.xmp', Photo.SIDECAR_FORMATS)
        self.assertIn('.xml', Photo.SIDECAR_FORMATS)
        self.assertIn('.aae', Photo.SIDECAR_FORMATS)  # Apple adjustment data
        self.assertIn('.thm', Photo.SIDECAR_FORMATS)
        
        # Test Other formats
        self.assertIn('.png', Photo.OTHER_PHOTO_FORMATS)
        self.assertIn('.gif', Photo.OTHER_PHOTO_FORMATS)
        self.assertIn('.svg', Photo.OTHER_PHOTO_FORMATS)
    
    def test_get_all_supported_formats(self):
        """Test that get_all_supported_formats returns all format sets combined."""
        all_formats = Photo.get_all_supported_formats()
        
        # Check that all format categories are included
        self.assertTrue(Photo.JPEG_FORMATS.issubset(all_formats))
        self.assertTrue(Photo.RAW_FORMATS.issubset(all_formats))
        self.assertTrue(Photo.LIVE_PHOTO_FORMATS.issubset(all_formats))
        self.assertTrue(Photo.HEIC_FORMATS.issubset(all_formats))
        self.assertTrue(Photo.SIDECAR_FORMATS.issubset(all_formats))
        self.assertTrue(Photo.OTHER_PHOTO_FORMATS.issubset(all_formats))
        
        # Verify specific formats are present
        self.assertIn('.jpg', all_formats)
        self.assertIn('.cr2', all_formats)
        self.assertIn('.png', all_formats)
        self.assertIn('.xmp', all_formats)
        self.assertIn('.heic', all_formats)
        self.assertIn('.mov', all_formats)
    
    def test_get_format_classification(self):
        """Test format classification for various extensions."""
        # Test JPEG classification
        self.assertEqual(Photo.get_format_classification('.jpg'), 'jpeg')
        self.assertEqual(Photo.get_format_classification('.jpeg'), 'jpeg')
        self.assertEqual(Photo.get_format_classification('jpg'), 'jpeg')  # Without dot
        
        # Test RAW classification
        self.assertEqual(Photo.get_format_classification('.cr2'), 'raw')
        self.assertEqual(Photo.get_format_classification('.nef'), 'raw')
        self.assertEqual(Photo.get_format_classification('.arw'), 'raw')
        self.assertEqual(Photo.get_format_classification('.dng'), 'raw')
        
        # Test HEIC classification
        self.assertEqual(Photo.get_format_classification('.heic'), 'heic')
        self.assertEqual(Photo.get_format_classification('.heif'), 'heic')
        self.assertEqual(Photo.get_format_classification('.hif'), 'heic')
        
        # Test Live Photo classification
        self.assertEqual(Photo.get_format_classification('.mov'), 'live_photo')
        
        # Test Sidecar classification
        self.assertEqual(Photo.get_format_classification('.xmp'), 'sidecar')
        self.assertEqual(Photo.get_format_classification('.xml'), 'sidecar')
        self.assertEqual(Photo.get_format_classification('.aae'), 'sidecar')  # Apple adjustment data
        self.assertEqual(Photo.get_format_classification('.thm'), 'sidecar')
        
        # Test Other classification
        self.assertEqual(Photo.get_format_classification('.png'), 'other')
        self.assertEqual(Photo.get_format_classification('.gif'), 'other')
        self.assertEqual(Photo.get_format_classification('.svg'), 'other')
        
        # Test unsupported format
        self.assertIsNone(Photo.get_format_classification('.txt'))
        self.assertIsNone(Photo.get_format_classification('.doc'))
    
    def test_photo_initialization_success(self):
        """Test successful photo initialization with various formats."""
        test_files = [
            ('test.jpg', 'jpeg'),
            ('test.cr2', 'raw'),
            ('test.png', 'other'),
            ('test.heic', 'heic'),
            ('test.mov', 'live_photo'),
            ('test.xmp', 'sidecar')
        ]
        
        for filename, expected_classification in test_files:
            with self.subTest(filename=filename):
                file_path = self.create_temp_file(filename)
                photo = Photo(file_path)
                
                # Test basic attributes
                self.assertEqual(photo.absolute_path, Path(file_path).resolve())
                self.assertEqual(photo.basename, Path(filename).stem)
                self.assertEqual(photo.extension, Path(filename).suffix.lower())
                self.assertEqual(photo.filename, filename)
                self.assertEqual(photo.format_classification, expected_classification)
    
    def test_photo_initialization_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent files."""
        with self.assertRaises(FileNotFoundError):
            Photo("/non/existent/path/test.jpg")
    
    def test_photo_initialization_unsupported_format(self):
        """Test that ValueError is raised for unsupported file formats."""
        file_path = self.create_temp_file("test.txt")
        with self.assertRaises(ValueError) as context:
            Photo(file_path)
        
        self.assertIn("Unsupported image format", str(context.exception))
        self.assertIn(".txt", str(context.exception))
    
    def test_format_property_methods(self):
        """Test the is_* property methods for format checking."""
        test_cases = [
            ('test.jpg', 'is_jpeg', True),
            ('test.jpeg', 'is_jpeg', True),
            ('test.cr2', 'is_raw', True),
            ('test.nef', 'is_raw', True),
            ('test.png', 'is_other_format', True),
            ('test.gif', 'is_other_format', True),
            ('test.heic', 'is_heic', True),
            ('test.heif', 'is_heic', True),
            ('test.mov', 'is_live_photo', True),
            ('test.xmp', 'is_sidecar', True),
            ('test.xml', 'is_sidecar', True),
            # Test false cases
            ('test.png', 'is_jpeg', False),
            ('test.jpg', 'is_raw', False),
            ('test.cr2', 'is_heic', False),
        ]
        
        for filename, property_name, expected in test_cases:
            with self.subTest(filename=filename, property=property_name):
                file_path = self.create_temp_file(filename)
                photo = Photo(file_path)
                actual = getattr(photo, property_name)
                self.assertEqual(actual, expected)
    
    def test_size_properties(self):
        """Test file size properties."""
        # Create a file with known content
        file_path = self.create_temp_file("test.jpg")
        
        # Write specific content to know the size
        test_content = "a" * 1000  # 1000 bytes
        with open(file_path, 'w') as f:
            f.write(test_content)
        
        photo = Photo(file_path)
        
        # Test size_bytes
        self.assertEqual(photo.size_bytes, 1000)
        
        # Test size_mb (should be close to 1000/1024/1024)
        expected_mb = round(1000 / (1024 * 1024), 2)
        self.assertEqual(photo.size_mb, expected_mb)
    
    def test_exists_method(self):
        """Test the exists method."""
        file_path = self.create_temp_file("test.jpg")
        photo = Photo(file_path)
        
        # File should exist
        self.assertTrue(photo.exists())
        
        # Remove the file
        os.remove(file_path)
        
        # File should not exist
        self.assertFalse(photo.exists())
    
    def test_string_representations(self):
        """Test __str__ and __repr__ methods."""
        file_path = self.create_temp_file("test_image.jpg")
        photo = Photo(file_path)
        
        # Test __str__
        self.assertEqual(str(photo), "Photo(test_image.jpg)")
        
        # Test __repr__
        expected_repr = f"Photo(path='{photo.absolute_path}', basename='test_image', extension='.jpg')"
        self.assertEqual(repr(photo), expected_repr)
    
    def test_equality_and_hashing(self):
        """Test equality comparison and hashing."""
        file_path1 = self.create_temp_file("test1.jpg")
        file_path2 = self.create_temp_file("test2.jpg")
        
        photo1a = Photo(file_path1)
        photo1b = Photo(file_path1)  # Same file
        photo2 = Photo(file_path2)   # Different file
        
        # Test equality
        self.assertEqual(photo1a, photo1b)
        self.assertNotEqual(photo1a, photo2)
        self.assertNotEqual(photo1a, "not a photo")
        
        # Test hashing (should be able to use in sets/dicts)
        photo_set = {photo1a, photo1b, photo2}
        self.assertEqual(len(photo_set), 2)  # photo1a and photo1b should be the same
    
    def test_case_insensitive_extensions(self):
        """Test that extensions are handled case-insensitively."""
        test_cases = [
            ('test.JPG', '.jpg', 'jpeg'),
            ('test.JPEG', '.jpeg', 'jpeg'),
            ('test.CR2', '.cr2', 'raw'),
            ('test.PNG', '.png', 'other'),
            ('test.HEIC', '.heic', 'heic'),
            ('test.XMP', '.xmp', 'sidecar'),
        ]
        
        for filename, expected_ext, expected_classification in test_cases:
            with self.subTest(filename=filename):
                file_path = self.create_temp_file(filename)
                photo = Photo(file_path)
                
                self.assertEqual(photo.extension, expected_ext)
                self.assertEqual(photo.format_classification, expected_classification)
    
    def test_path_object_input(self):
        """Test that Path objects can be used as input."""
        file_path = self.create_temp_file("test.jpg")
        path_obj = Path(file_path)
        
        photo = Photo(path_obj)
        self.assertEqual(photo.absolute_path, path_obj.resolve())
        self.assertEqual(photo.filename, "test.jpg")
    
    def test_comprehensive_raw_formats(self):
        """Test a comprehensive list of RAW formats."""
        raw_extensions = [
            '.cr2', '.cr3', '.crw',  # Canon
            '.nef', '.nrw',          # Nikon
            '.arw', '.srf', '.sr2',  # Sony
            '.raf',                  # Fujifilm
            '.orf',                  # Olympus
            '.rw2',                  # Panasonic
            '.pef', '.ptx',          # Pentax
            '.rwl',                  # Leica
            '.dcr', '.kdc',          # Kodak
            '.mrw',                  # Minolta
            '.srw',                  # Samsung
            '.3fr',                  # Hasselblad
            '.mef',                  # Mamiya
            '.iiq',                  # Phase One
            '.x3f',                  # Sigma
            '.dng',                  # Adobe/Generic
            '.raw'                   # Generic
        ]
        
        for ext in raw_extensions:
            with self.subTest(extension=ext):
                self.assertIn(ext, Photo.RAW_FORMATS)
                self.assertEqual(Photo.get_format_classification(ext), 'raw')


if __name__ == '__main__':
    unittest.main()
