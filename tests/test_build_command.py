import unittest
import tempfile
import os
import json
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import patch

from main import cli


class TestBuildCommand(unittest.TestCase):
    """Test cases for the build CLI command."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.runner = CliRunner()
        
    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_test_photos(self, filenames: list) -> None:
        """Create test photo files in temp directory."""
        for filename in filenames:
            file_path = os.path.join(self.temp_dir, filename)
            with open(file_path, 'w') as f:
                f.write("test photo content")
    
    def test_build_command_success(self):
        """Test successful build command execution."""
        # Create test photos
        self.create_test_photos([
            "vacation.jpg", "vacation.cr2", "vacation.xmp",
            "portrait.heic", "landscape.png"
        ])
        
        output_file = os.path.join(self.temp_dir, "test_output.json")
        
        # Run build command
        result = self.runner.invoke(cli, [
            'build', 
            self.temp_dir,
            '--output', output_file,
            '--recursive'
        ])
        
        # Check command succeeded
        self.assertEqual(result.exit_code, 0)
        self.assertIn("Scan completed successfully", result.output)
        self.assertIn("5 photos organized into 3 groups", result.output)
        
        # Check output file was created
        self.assertTrue(os.path.exists(output_file))
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        self.assertIn("metadata", data)
        self.assertIn("groups", data)
        self.assertEqual(data["metadata"]["total_photos"], 5)
        self.assertEqual(data["metadata"]["total_groups"], 3)
    
    def test_build_command_nonexistent_directory(self):
        """Test build command with non-existent directory."""
        result = self.runner.invoke(cli, [
            'build', 
            '/nonexistent/directory'
        ])
        
        # Should fail with non-zero exit code
        self.assertNotEqual(result.exit_code, 0)
    
    def test_build_command_no_photos(self):
        """Test build command when no photos are found."""
        # Create empty directory
        empty_dir = os.path.join(self.temp_dir, "empty")
        os.makedirs(empty_dir)
        
        result = self.runner.invoke(cli, [
            'build', 
            empty_dir
        ])
        
        # Should complete but warn about no photos
        self.assertEqual(result.exit_code, 0)
        self.assertIn("No photos found", result.output)
    
    def test_build_command_verbose_logging(self):
        """Test build command with verbose logging enabled."""
        self.create_test_photos(["test.jpg"])
        
        result = self.runner.invoke(cli, [
            'build', 
            self.temp_dir,
            '--verbose'
        ])
        
        self.assertEqual(result.exit_code, 0)
        # With verbose logging, we should see more detailed output
        # (This would need to be adjusted based on actual logging output)
    
    def test_build_command_non_recursive(self):
        """Test build command with non-recursive scanning."""
        # Create photos in root and subdirectory
        self.create_test_photos(["root.jpg"])
        
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir)
        with open(os.path.join(subdir, "sub.jpg"), 'w') as f:
            f.write("test content")
        
        result = self.runner.invoke(cli, [
            'build', 
            self.temp_dir,
            '--no-recursive'
        ])
        
        self.assertEqual(result.exit_code, 0)
        # Should only find the root photo, not the subdirectory photo
        self.assertIn("1 photos organized into 1 groups", result.output)


if __name__ == '__main__':
    unittest.main()
