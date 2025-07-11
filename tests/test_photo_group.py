import unittest
import tempfile
import os
import json
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

from models.photo import Photo
from models.photo_group import PhotoGroup, PhotoGroupManager


class TestPhotoGroup(unittest.TestCase):
    """Test cases for the PhotoGroup class."""
    
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
    
    def create_photo_group_with_files(self, basename: str, extensions: list) -> tuple:
        """Create a PhotoGroup with test files."""
        group = PhotoGroup(basename)
        photos = []
        
        for ext in extensions:
            filename = f"{basename}{ext}"
            file_path = self.create_temp_file(filename)
            photo = Photo(file_path)
            group.add_photo(photo)
            photos.append(photo)
        
        return group, photos
    
    def test_photo_group_initialization(self):
        """Test PhotoGroup initialization."""
        basename = "test_image"
        group = PhotoGroup(basename)
        
        self.assertEqual(group.basename, basename)
        self.assertEqual(group.count, 0)
        self.assertTrue(group.is_empty)
        self.assertEqual(len(group), 0)
    
    def test_add_photo_success(self):
        """Test successfully adding photos to a group."""
        basename = "sunset"
        group = PhotoGroup(basename)
        
        # Create test photos
        jpg_path = self.create_temp_file(f"{basename}.jpg")
        raw_path = self.create_temp_file(f"{basename}.cr2")
        
        jpg_photo = Photo(jpg_path)
        raw_photo = Photo(raw_path)
        
        # Add photos to group
        group.add_photo(jpg_photo)
        group.add_photo(raw_photo)
        
        self.assertEqual(group.count, 2)
        self.assertFalse(group.is_empty)
        self.assertIn('.jpg', group.get_extensions())
        self.assertIn('.cr2', group.get_extensions())
    
    def test_add_photo_wrong_basename(self):
        """Test that adding a photo with wrong basename raises ValueError."""
        group = PhotoGroup("test_image")
        
        # Create photo with different basename
        wrong_path = self.create_temp_file("different_name.jpg")
        wrong_photo = Photo(wrong_path)
        
        with self.assertRaises(ValueError) as context:
            group.add_photo(wrong_photo)
        
        self.assertIn("doesn't match group basename", str(context.exception))
    
    def test_get_photo(self):
        """Test retrieving photos by extension."""
        group, photos = self.create_photo_group_with_files("test", [".jpg", ".cr2", ".xmp"])
        
        # Test getting existing photos
        jpg_photo = group.get_photo(".jpg")
        self.assertIsNotNone(jpg_photo)
        self.assertEqual(jpg_photo.extension, ".jpg")
        
        # Test getting photo without dot
        cr2_photo = group.get_photo("cr2")
        self.assertIsNotNone(cr2_photo)
        self.assertEqual(cr2_photo.extension, ".cr2")
        
        # Test getting non-existent photo
        self.assertIsNone(group.get_photo(".png"))
    
    def test_remove_photo(self):
        """Test removing photos from a group."""
        group, photos = self.create_photo_group_with_files("test", [".jpg", ".cr2", ".xmp"])
        
        # Remove existing photo
        removed_photo = group.remove_photo(".jpg")
        self.assertIsNotNone(removed_photo)
        self.assertEqual(removed_photo.extension, ".jpg")
        self.assertEqual(group.count, 2)
        self.assertNotIn(".jpg", group.get_extensions())
        
        # Try to remove non-existent photo
        self.assertIsNone(group.remove_photo(".png"))
        
        # Remove photo without dot
        removed_raw = group.remove_photo("cr2")
        self.assertIsNotNone(removed_raw)
        self.assertEqual(group.count, 1)
    
    def test_get_photos(self):
        """Test getting all photos in a group."""
        group, original_photos = self.create_photo_group_with_files("test", [".jpg", ".cr2", ".xmp"])
        
        all_photos = group.get_photos()
        self.assertEqual(len(all_photos), 3)
        
        # Check that all original photos are in the returned list
        for photo in original_photos:
            self.assertIn(photo, all_photos)
    
    def test_has_extension(self):
        """Test checking if group has specific extensions."""
        group, _ = self.create_photo_group_with_files("test", [".jpg", ".cr2"])
        
        # Test existing extensions
        self.assertTrue(group.has_extension(".jpg"))
        self.assertTrue(group.has_extension("jpg"))  # Without dot
        self.assertTrue(group.has_extension(".cr2"))
        
        # Test non-existing extensions
        self.assertFalse(group.has_extension(".png"))
        self.assertFalse(group.has_extension("png"))
    
    def test_format_type_methods(self):
        """Test format type checking methods."""
        group, _ = self.create_photo_group_with_files("test", [".jpg", ".cr2", ".xmp", ".heic", ".mov"])
        
        # Test has_format_type
        self.assertTrue(group.has_format_type("jpeg"))
        self.assertTrue(group.has_format_type("raw"))
        self.assertTrue(group.has_format_type("sidecar"))
        self.assertTrue(group.has_format_type("heic"))
        self.assertTrue(group.has_format_type("live_photo"))
        self.assertFalse(group.has_format_type("other"))
        
        # Test convenience properties
        self.assertTrue(group.has_jpeg)
        self.assertTrue(group.has_raw)
        self.assertTrue(group.has_sidecar)
        self.assertTrue(group.has_heic)
        self.assertTrue(group.has_live_photo)
    
    def test_get_photos_by_format(self):
        """Test getting photos filtered by format type."""
        group, _ = self.create_photo_group_with_files("test", [".jpg", ".jpeg", ".cr2", ".nef"])
        
        jpeg_photos = group.get_photos_by_format("jpeg")
        self.assertEqual(len(jpeg_photos), 2)  # .jpg and .jpeg
        
        raw_photos = group.get_photos_by_format("raw")
        self.assertEqual(len(raw_photos), 2)   # .cr2 and .nef
        
        other_photos = group.get_photos_by_format("other")
        self.assertEqual(len(other_photos), 0)
    
    def test_magic_methods(self):
        """Test magic methods for PhotoGroup."""
        group, photos = self.create_photo_group_with_files("test", [".jpg", ".cr2"])
        
        # Test __len__
        self.assertEqual(len(group), 2)
        
        # Test __contains__ with extension
        self.assertIn(".jpg", group)
        self.assertIn("jpg", group)
        self.assertNotIn(".png", group)
        
        # Test __contains__ with Photo object
        self.assertIn(photos[0], group)
        
        # Test __iter__
        iterated_photos = list(group)
        self.assertEqual(len(iterated_photos), 2)
        
        # Test __str__ and __repr__
        self.assertIn("PhotoGroup", str(group))
        self.assertIn("test", str(group))
        self.assertIn("2 photos", str(group))
        
        repr_str = repr(group)
        self.assertIn("PhotoGroup", repr_str)
        self.assertIn("test", repr_str)
        self.assertIn("extensions", repr_str)
    
    def test_equality_and_hashing(self):
        """Test equality and hashing for PhotoGroup."""
        group1, _ = self.create_photo_group_with_files("test", [".jpg", ".cr2"])
        group2, _ = self.create_photo_group_with_files("test", [".jpg", ".cr2"])
        group3, _ = self.create_photo_group_with_files("different", [".jpg"])
        
        # Groups with same basename and photos should be equal
        self.assertEqual(group1, group2)
        
        # Groups with different basenames should not be equal
        self.assertNotEqual(group1, group3)
        
        # Test hashing
        group_set = {group1, group2, group3}
        self.assertEqual(len(group_set), 2)  # group1 and group2 should hash the same


class TestPhotoGroupManager(unittest.TestCase):
    """Test cases for the PhotoGroupManager class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PhotoGroupManager()
        
    def tearDown(self):
        """Clean up after each test method."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_temp_file(self, filename: str) -> str:
        """Create a temporary file for testing."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write("test content")
        return file_path
    
    def create_test_photos(self, filenames: list) -> list:
        """Create multiple test photos."""
        photos = []
        for filename in filenames:
            file_path = self.create_temp_file(filename)
            photos.append(Photo(file_path))
        return photos
    
    def test_manager_initialization(self):
        """Test PhotoGroupManager initialization."""
        self.assertEqual(self.manager.total_groups, 0)
        self.assertEqual(self.manager.total_photos, 0)
        self.assertEqual(len(self.manager), 0)
    
    def test_add_single_photo(self):
        """Test adding a single photo to the manager."""
        photos = self.create_test_photos(["sunset.jpg"])
        
        group = self.manager.add_photo(photos[0])
        
        self.assertEqual(self.manager.total_groups, 1)
        self.assertEqual(self.manager.total_photos, 1)
        self.assertEqual(group.basename, "sunset")
        self.assertEqual(group.count, 1)
    
    def test_add_multiple_photos_same_basename(self):
        """Test adding multiple photos with the same basename."""
        photos = self.create_test_photos(["sunset.jpg", "sunset.cr2", "sunset.xmp"])
        
        for photo in photos:
            self.manager.add_photo(photo)
        
        self.assertEqual(self.manager.total_groups, 1)
        self.assertEqual(self.manager.total_photos, 3)
        
        group = self.manager.get_group("sunset")
        self.assertIsNotNone(group)
        self.assertEqual(group.count, 3)
    
    def test_add_multiple_photos_different_basenames(self):
        """Test adding photos with different basenames."""
        photos = self.create_test_photos([
            "sunset.jpg", "sunset.cr2",
            "landscape.jpg", "landscape.nef",
            "portrait.heic"
        ])
        
        for photo in photos:
            self.manager.add_photo(photo)
        
        self.assertEqual(self.manager.total_groups, 3)
        self.assertEqual(self.manager.total_photos, 5)
        
        # Check individual groups
        sunset_group = self.manager.get_group("sunset")
        self.assertEqual(sunset_group.count, 2)
        
        landscape_group = self.manager.get_group("landscape")
        self.assertEqual(landscape_group.count, 2)
        
        portrait_group = self.manager.get_group("portrait")
        self.assertEqual(portrait_group.count, 1)
    
    def test_add_photos_batch(self):
        """Test adding multiple photos using add_photos method."""
        photos = self.create_test_photos(["img1.jpg", "img1.cr2", "img2.png"])
        
        self.manager.add_photos(photos)
        
        self.assertEqual(self.manager.total_groups, 2)
        self.assertEqual(self.manager.total_photos, 3)
    
    def test_get_group(self):
        """Test retrieving groups by basename."""
        photos = self.create_test_photos(["test.jpg", "test.cr2"])
        self.manager.add_photos(photos)
        
        # Test getting existing group
        group = self.manager.get_group("test")
        self.assertIsNotNone(group)
        self.assertEqual(group.basename, "test")
        
        # Test getting non-existent group
        self.assertIsNone(self.manager.get_group("nonexistent"))
    
    def test_get_all_groups(self):
        """Test getting all groups."""
        photos = self.create_test_photos(["img1.jpg", "img2.png", "img3.cr2"])
        self.manager.add_photos(photos)
        
        all_groups = self.manager.get_all_groups()
        self.assertEqual(len(all_groups), 3)
        
        basenames = {group.basename for group in all_groups}
        self.assertEqual(basenames, {"img1", "img2", "img3"})
    
    def test_get_basenames(self):
        """Test getting all basenames."""
        photos = self.create_test_photos(["img1.jpg", "img2.png", "img1.cr2"])
        self.manager.add_photos(photos)
        
        basenames = self.manager.get_basenames()
        self.assertEqual(basenames, {"img1", "img2"})
    
    def test_remove_group(self):
        """Test removing a group."""
        photos = self.create_test_photos(["test.jpg", "test.cr2"])
        self.manager.add_photos(photos)
        
        # Remove existing group
        removed_group = self.manager.remove_group("test")
        self.assertIsNotNone(removed_group)
        self.assertEqual(removed_group.basename, "test")
        self.assertEqual(self.manager.total_groups, 0)
        
        # Try to remove non-existent group
        self.assertIsNone(self.manager.remove_group("nonexistent"))
    
    def test_get_groups_with_format(self):
        """Test getting groups that contain specific format types."""
        photos = self.create_test_photos([
            "img1.jpg", "img1.cr2",
            "img2.png",
            "img3.heic", "img3.cr2"
        ])
        self.manager.add_photos(photos)
        
        # Get groups with RAW format
        raw_groups = self.manager.get_groups_with_format("raw")
        self.assertEqual(len(raw_groups), 2)  # img1 and img3
        
        # Get groups with JPEG format
        jpeg_groups = self.manager.get_groups_with_format("jpeg")
        self.assertEqual(len(jpeg_groups), 1)  # only img1
        
        # Get groups with HEIC format
        heic_groups = self.manager.get_groups_with_format("heic")
        self.assertEqual(len(heic_groups), 1)  # only img3
    
    def test_get_groups_with_multiple_formats(self):
        """Test getting groups that contain multiple file formats."""
        photos = self.create_test_photos([
            "img1.jpg", "img1.cr2",        # Multiple formats
            "img2.png",                    # Single format
            "img3.heic", "img3.xmp",       # Multiple formats
            "img4.cr2"                     # Single format
        ])
        self.manager.add_photos(photos)
        
        multi_format_groups = self.manager.get_groups_with_multiple_formats()
        self.assertEqual(len(multi_format_groups), 2)  # img1 and img3
        
        basenames = {group.basename for group in multi_format_groups}
        self.assertEqual(basenames, {"img1", "img3"})
    
    def test_magic_methods(self):
        """Test magic methods for PhotoGroupManager."""
        photos = self.create_test_photos(["img1.jpg", "img2.png"])
        self.manager.add_photos(photos)
        
        # Test __len__
        self.assertEqual(len(self.manager), 2)
        
        # Test __contains__
        self.assertIn("img1", self.manager)
        self.assertNotIn("nonexistent", self.manager)
        
        # Test __getitem__
        group = self.manager["img1"]
        self.assertEqual(group.basename, "img1")
        
        # Test __iter__
        iterated_groups = list(self.manager)
        self.assertEqual(len(iterated_groups), 2)
        
        # Test __str__ and __repr__
        self.assertIn("PhotoGroupManager", str(self.manager))
        self.assertIn("2 groups", str(self.manager))
        self.assertIn("2 photos", str(self.manager))
        
        repr_str = repr(self.manager)
        self.assertIn("PhotoGroupManager", repr_str)
        self.assertIn("groups=", repr_str)
    
    def test_complex_scenario(self):
        """Test a complex scenario with multiple photo types."""
        # Create a realistic photo collection
        photos = self.create_test_photos([
            # Vacation photos with RAW + JPEG
            "vacation_001.cr2", "vacation_001.jpg", "vacation_001.xmp",
            "vacation_002.cr2", "vacation_002.jpg",
            
            # Phone photos
            "phone_pic.heic", "phone_pic.mov",  # Live photo
            
            # Single files
            "screenshot.png",
            "document_scan.pdf"  # This should fail validation
        ])
        
        # Add all valid photos (PDF will raise exception)
        valid_photos = photos[:-1]  # Exclude the PDF
        
        self.manager.add_photos(valid_photos)
        
        # Verify structure
        self.assertEqual(self.manager.total_groups, 4)
        self.assertEqual(self.manager.total_photos, 7)
        
        # Check vacation photos group
        vacation_001 = self.manager.get_group("vacation_001")
        self.assertEqual(vacation_001.count, 3)
        self.assertTrue(vacation_001.has_raw)
        self.assertTrue(vacation_001.has_jpeg)
        self.assertTrue(vacation_001.has_sidecar)
        
        vacation_002 = self.manager.get_group("vacation_002")
        self.assertEqual(vacation_002.count, 2)
        
        # Check phone photo group
        phone_pic = self.manager.get_group("phone_pic")
        self.assertEqual(phone_pic.count, 2)
        self.assertTrue(phone_pic.has_heic)
        self.assertTrue(phone_pic.has_live_photo)
        
        # Get groups with multiple formats
        multi_format = self.manager.get_groups_with_multiple_formats()
        self.assertEqual(len(multi_format), 3)  # vacation_001, vacation_002, phone_pic


class TestPhotoGroupManagerDirectoryScanning(unittest.TestCase):
    """Test cases for directory scanning functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PhotoGroupManager()
        
        # Set up logging to capture log messages
        self.log_handler = logging.StreamHandler()
        self.log_handler.setLevel(logging.DEBUG)
        logger = logging.getLogger('models.photo_group')
        logger.addHandler(self.log_handler)
        logger.setLevel(logging.DEBUG)
        
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_directory_structure(self) -> None:
        """Create a test directory structure with photos."""
        # Root level photos
        self.create_temp_file("photo1.jpg")
        self.create_temp_file("photo1.cr2")
        self.create_temp_file("photo2.png")
        
        # Subdirectory with photos
        subdir = os.path.join(self.temp_dir, "subfolder")
        os.makedirs(subdir)
        
        with open(os.path.join(subdir, "photo3.heic"), 'w') as f:
            f.write("test content")
        with open(os.path.join(subdir, "photo3.mov"), 'w') as f:
            f.write("test content")
        
        # Non-photo files (should be ignored)
        self.create_temp_file("readme.txt")
        with open(os.path.join(subdir, "document.pdf"), 'w') as f:
            f.write("test content")
    
    def create_temp_file(self, filename: str) -> str:
        """Create a temporary file for testing."""
        file_path = os.path.join(self.temp_dir, filename)
        with open(file_path, 'w') as f:
            f.write("test content")
        return file_path
    
    def test_scan_directory_recursive(self):
        """Test recursive directory scanning."""
        self.create_directory_structure()
        
        photos_found = self.manager.scan_directory(self.temp_dir, recursive=True)
        
        # Should find all photos in root and subdirectories
        self.assertEqual(photos_found, 5)  # 3 in root + 2 in subfolder
        self.assertEqual(self.manager.total_groups, 3)  # photo1, photo2, photo3
        
        # Verify specific groups
        photo1_group = self.manager.get_group("photo1")
        self.assertEqual(photo1_group.count, 2)  # .jpg and .cr2
        
        photo3_group = self.manager.get_group("photo3")
        self.assertEqual(photo3_group.count, 2)  # .heic and .mov
    
    def test_scan_directory_non_recursive(self):
        """Test non-recursive directory scanning."""
        self.create_directory_structure()
        
        photos_found = self.manager.scan_directory(self.temp_dir, recursive=False)
        
        # Should only find photos in root directory
        self.assertEqual(photos_found, 3)  # Only root level photos
        self.assertEqual(self.manager.total_groups, 2)  # photo1, photo2
    
    def test_scan_nonexistent_directory(self):
        """Test scanning a directory that doesn't exist."""
        with self.assertRaises(FileNotFoundError):
            self.manager.scan_directory("/nonexistent/directory")
    
    def test_scan_file_instead_of_directory(self):
        """Test scanning a file instead of directory."""
        file_path = self.create_temp_file("test.jpg")
        
        with self.assertRaises(ValueError):
            self.manager.scan_directory(file_path)


class TestPhotoGroupManagerSerialization(unittest.TestCase):
    """Test cases for JSON serialization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = PhotoGroupManager()
        
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_photos(self, filenames: list) -> list:
        """Create multiple test photos."""
        photos = []
        for filename in filenames:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test content")
            photos.append(Photo(file_path))
        return photos
    
    def test_to_dict(self):
        """Test converting manager to dictionary."""
        photos = self.create_test_photos(["img1.jpg", "img1.cr2", "img2.png"])
        self.manager.add_photos(photos)
        
        data = self.manager.to_dict()
        
        # Check metadata
        self.assertIn("metadata", data)
        metadata = data["metadata"]
        self.assertEqual(metadata["total_groups"], 2)
        self.assertEqual(metadata["total_photos"], 3)
        self.assertEqual(metadata["created_by"], "imgmaster")
        
        # Check groups
        self.assertIn("groups", data)
        groups = data["groups"]
        self.assertIn("img1", groups)
        self.assertIn("img2", groups)
        
        # Check img1 group details
        img1_group = groups["img1"]
        self.assertEqual(img1_group["count"], 2)
        self.assertTrue(img1_group["formats"]["jpeg"])
        self.assertTrue(img1_group["formats"]["raw"])
        self.assertEqual(len(img1_group["photos"]), 2)
    
    def test_save_and_load_json(self):
        """Test saving to and loading from JSON file."""
        # Create test data
        photos = self.create_test_photos(["test1.jpg", "test1.xmp", "test2.heic"])
        self.manager.add_photos(photos)
        
        # Save to JSON
        json_path = os.path.join(self.temp_dir, "test_database.json")
        self.manager.save_to_json(json_path)
        
        # Verify file was created
        self.assertTrue(os.path.exists(json_path))
        
        # Load from JSON
        loaded_manager = PhotoGroupManager.load_from_json(json_path)
        
        # Verify loaded data
        self.assertEqual(loaded_manager.total_groups, self.manager.total_groups)
        self.assertEqual(loaded_manager.total_photos, self.manager.total_photos)
        
        # Check specific groups
        test1_group = loaded_manager.get_group("test1")
        self.assertIsNotNone(test1_group)
        self.assertEqual(test1_group.count, 2)
    
    def test_save_json_creates_directory(self):
        """Test that saving JSON creates necessary directories."""
        photos = self.create_test_photos(["test.jpg"])
        self.manager.add_photos(photos)
        
        # Save to nested path that doesn't exist
        nested_path = os.path.join(self.temp_dir, "nested", "dir", "database.json")
        self.manager.save_to_json(nested_path)
        
        # Verify file was created and directories were made
        self.assertTrue(os.path.exists(nested_path))
    
    def test_load_nonexistent_json(self):
        """Test loading from non-existent JSON file."""
        with self.assertRaises(FileNotFoundError):
            PhotoGroupManager.load_from_json("/nonexistent/file.json")
    
    def test_from_dict_with_missing_files(self):
        """Test loading from dict when some photo files are missing."""
        # Create and save manager
        photos = self.create_test_photos(["test.jpg", "test.cr2"])
        self.manager.add_photos(photos)
        data = self.manager.to_dict()
        
        # Remove one of the photo files
        os.remove(photos[0].absolute_path)
        
        # Load from dict (should handle missing file gracefully)
        loaded_manager = PhotoGroupManager.from_dict(data)
        
        # Should have loaded only the existing photo
        self.assertEqual(loaded_manager.total_photos, 1)
        self.assertEqual(loaded_manager.total_groups, 1)
