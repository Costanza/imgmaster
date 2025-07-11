"""Tests for the repository pattern implementation."""

import unittest
import tempfile
import json
from pathlib import Path

from repositories import JsonFilePhotoGroupRepository, RepositoryNotFoundError, RepositoryError
from models import PhotoGroupManager, PhotoGroup


class TestJsonFilePhotoGroupRepository(unittest.TestCase):
    """Test cases for JSON file repository implementation."""
    
    def setUp(self):
        self.repository = JsonFilePhotoGroupRepository()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_repo.json"
        
    def tearDown(self):
        """Clean up test files."""
        if self.test_file.exists():
            self.test_file.unlink()
        self.temp_dir.rmdir()
    
    def test_exists_method(self):
        """Test the exists method."""
        # Non-existent file should return False
        self.assertFalse(self.repository.exists(str(self.test_file)))
        
        # Create file and test again
        self.test_file.write_text("{}")
        self.assertTrue(self.repository.exists(str(self.test_file)))
    
    def test_save_and_load_cycle(self):
        """Test saving and loading a photo group manager."""
        # Create a manager with some test data
        manager = PhotoGroupManager()
        
        # Save using repository
        self.repository.save(manager, str(self.test_file))
        
        # Verify file exists
        self.assertTrue(self.test_file.exists())
        
        # Load using repository
        loaded_manager = self.repository.load(str(self.test_file))
        
        # Verify loaded manager
        self.assertIsInstance(loaded_manager, PhotoGroupManager)
        self.assertEqual(loaded_manager.total_groups, manager.total_groups)
    
    def test_load_nonexistent_file(self):
        """Test loading from non-existent file raises appropriate error."""
        with self.assertRaises(RepositoryNotFoundError):
            self.repository.load(str(self.test_file))
    
    def test_delete_method(self):
        """Test the delete method."""
        # Create file
        self.test_file.write_text("{}")
        self.assertTrue(self.test_file.exists())
        
        # Delete using repository
        self.repository.delete(str(self.test_file))
        
        # Verify file is gone
        self.assertFalse(self.test_file.exists())
    
    def test_delete_nonexistent_file(self):
        """Test deleting non-existent file raises appropriate error."""
        with self.assertRaises(RepositoryNotFoundError):
            self.repository.delete(str(self.test_file))


if __name__ == '__main__':
    unittest.main()
