"""Test XMP backup functionality."""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

from services.rename_service import PhotoRenameService


class TestXmpBackup(unittest.TestCase):
    """Test XMP backup functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.service = PhotoRenameService()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.uuid = "test-uuid-12345"
        
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_xmp_backup_success(self):
        """Test that XMP backup is created successfully."""
        # Create original XMP file
        original_xmp = self.temp_dir / "test.xmp"
        original_content = "<?xml version='1.0'?><x:xmpmeta><rdf:RDF/></x:xmpmeta>"
        original_xmp.write_text(original_content)
        
        # Create backup
        self.service._create_xmp_backup(original_xmp)
        
        # Verify backup was created
        backup_path = self.temp_dir / "test_orig.xmp"
        self.assertTrue(backup_path.exists())
        self.assertEqual(backup_path.read_text(), original_content)
        
    def test_create_xmp_backup_already_exists(self):
        """Test that existing backup is not overwritten."""
        # Create original XMP file
        original_xmp = self.temp_dir / "test.xmp"
        original_content = "<?xml version='1.0'?><x:xmpmeta><rdf:RDF/></x:xmpmeta>"
        original_xmp.write_text(original_content)
        
        # Create existing backup with different content
        backup_path = self.temp_dir / "test_orig.xmp"
        existing_backup_content = "existing backup content"
        backup_path.write_text(existing_backup_content)
        
        # Attempt to create backup again
        self.service._create_xmp_backup(original_xmp)
        
        # Verify existing backup is preserved
        self.assertEqual(backup_path.read_text(), existing_backup_content)

    def test_write_uuid_to_xmp_with_backup_enabled(self):
        """Test that XMP backup is created when backup_xmp=True."""
        # Create existing XMP file
        xmp_path = self.temp_dir / "test.xmp"
        original_content = """<?xml version='1.0'?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about=""
  xmlns:xmp="http://ns.adobe.com/xap/1.0/"
  xmp:CreatorTool="Test Camera"/>
</rdf:RDF>
</x:xmpmeta>"""
        xmp_path.write_text(original_content)
        
        # Write UUID with backup enabled
        result = self.service._write_uuid_to_xmp_sidecar(xmp_path, self.uuid, [], backup_xmp=True)
        
        # Verify operation succeeded
        self.assertTrue(result)
        
        # Verify backup was created
        backup_path = self.temp_dir / "test_orig.xmp"
        self.assertTrue(backup_path.exists())
        self.assertEqual(backup_path.read_text(), original_content)
        
        # Verify UUID was written to original file
        modified_content = xmp_path.read_text()
        self.assertIn(self.uuid, modified_content)

    def test_write_uuid_to_xmp_with_backup_disabled(self):
        """Test that no backup is created when backup_xmp=False."""
        # Create existing XMP file
        xmp_path = self.temp_dir / "test.xmp"
        original_content = """<?xml version='1.0'?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
<rdf:Description rdf:about=""
  xmlns:xmp="http://ns.adobe.com/xap/1.0/"
  xmp:CreatorTool="Test Camera"/>
</rdf:RDF>
</x:xmpmeta>"""
        xmp_path.write_text(original_content)
        
        # Write UUID with backup disabled
        result = self.service._write_uuid_to_xmp_sidecar(xmp_path, self.uuid, [], backup_xmp=False)
        
        # Verify operation succeeded
        self.assertTrue(result)
        
        # Verify backup was NOT created
        backup_path = self.temp_dir / "test_orig.xmp"
        self.assertFalse(backup_path.exists())
        
        # Verify UUID was written to original file
        modified_content = xmp_path.read_text()
        self.assertIn(self.uuid, modified_content)

    def test_write_uuid_to_new_xmp_no_backup_needed(self):
        """Test that no backup is attempted for new XMP files."""
        # Create image file (no existing XMP)
        image_path = self.temp_dir / "test.jpg"
        image_path.write_bytes(b"fake image data")
        
        # Write UUID to create new XMP sidecar
        result = self.service._write_uuid_to_xmp_sidecar(image_path, self.uuid, [], backup_xmp=True)
        
        # Verify operation succeeded
        self.assertTrue(result)
        
        # Verify XMP sidecar was created
        xmp_path = self.temp_dir / "test.xmp"
        self.assertTrue(xmp_path.exists())
        
        # Verify no backup was created (since original didn't exist)
        backup_path = self.temp_dir / "test_orig.xmp"
        self.assertFalse(backup_path.exists())
        
        # Verify UUID was written
        content = xmp_path.read_text()
        self.assertIn(self.uuid, content)

    def test_write_uuid_to_file_passes_backup_parameter(self):
        """Test that _write_uuid_to_file passes backup_xmp parameter correctly."""
        # Create test file
        jpeg_path = self.temp_dir / "test.jpg"
        jpeg_path.write_bytes(b"fake jpeg data")
        
        # Mock the sidecar writing method to verify backup parameter is passed
        with patch.object(self.service, '_write_uuid_to_xmp_sidecar') as mock_xmp_write:
            mock_xmp_write.return_value = True
            
            # Test with backup enabled
            self.service._write_uuid_to_file(jpeg_path, self.uuid, [], backup_xmp=True)
            mock_xmp_write.assert_called_with(jpeg_path, self.uuid, [], True)
            
            # Test with backup disabled  
            self.service._write_uuid_to_file(jpeg_path, self.uuid, [], backup_xmp=False)
            mock_xmp_write.assert_called_with(jpeg_path, self.uuid, [], False)


if __name__ == '__main__':
    unittest.main()
