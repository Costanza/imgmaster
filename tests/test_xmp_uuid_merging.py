"""Test XMP UUID merging functionality."""

import pytest
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from services.rename_service import PhotoRenameService


class TestXMPUUIDMerging:
    """Test XMP UUID merging and preservation of existing metadata."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.service = PhotoRenameService()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.uuid = "test-uuid-12345"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_create_new_xmp_with_uuid(self):
        """Test creating a new XMP file with UUID."""
        xmp_path = self.temp_dir / "test.xmp"
        
        result = self.service._create_new_xmp_with_uuid(xmp_path, self.uuid)
        
        assert result is True
        assert xmp_path.exists()
        
        # Verify content
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert self.uuid in content
        assert 'imgmaster:GroupUUID' in content
        assert 'imgmaster:CreatedBy' in content
    
    def test_merge_uuid_into_existing_xmp_simple(self):
        """Test merging UUID into a simple existing XMP file."""
        xmp_path = self.temp_dir / "existing.xmp"
        
        # Create existing XMP with minimal structure
        existing_content = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about=""
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            dc:creator="Test Author"/>
    </rdf:RDF>
</x:xmpmeta>"""
        
        with open(xmp_path, 'w', encoding='utf-8') as f:
            f.write(existing_content)
        
        result = self.service._merge_uuid_into_existing_xmp(xmp_path, self.uuid)
        
        assert result is True
        
        # Verify that existing content is preserved and UUID is added
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert self.uuid in content
        assert 'dc:creator="Test Author"' in content
        assert 'imgmaster:GroupUUID' in content
    
    def test_merge_uuid_into_existing_xmp_complex(self):
        """Test merging UUID into a complex existing XMP file."""
        xmp_path = self.temp_dir / "complex.xmp"
        
        # Create existing XMP with multiple namespaces and elements
        existing_content = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about=""
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            xmlns:xmp="http://ns.adobe.com/xap/1.0/"
            xmlns:photoshop="http://ns.adobe.com/photoshop/1.0/"
            dc:creator="Complex Author"
            xmp:Rating="5"
            photoshop:Headline="Test Photo">
            <dc:subject>
                <rdf:Bag>
                    <rdf:li>keyword1</rdf:li>
                    <rdf:li>keyword2</rdf:li>
                </rdf:Bag>
            </dc:subject>
        </rdf:Description>
    </rdf:RDF>
</x:xmpmeta>"""
        
        with open(xmp_path, 'w', encoding='utf-8') as f:
            f.write(existing_content)
        
        result = self.service._merge_uuid_into_existing_xmp(xmp_path, self.uuid)
        
        assert result is True
        
        # Verify that all existing content is preserved
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert self.uuid in content
        assert 'dc:creator="Complex Author"' in content
        assert 'Rating="5"' in content  # Namespace prefix may change during XML processing
        assert 'Headline="Test Photo"' in content  # Namespace prefix may change during XML processing
        assert 'keyword1' in content
        assert 'keyword2' in content
        assert 'imgmaster:GroupUUID' in content
    
    def test_merge_uuid_handles_invalid_xml(self):
        """Test that invalid XML falls back to creating new file."""
        xmp_path = self.temp_dir / "invalid.xmp"
        
        # Create invalid XML
        invalid_content = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about=""
            dc:creator="Test Author"
        <!-- Missing closing tags -->"""
        
        with open(xmp_path, 'w', encoding='utf-8') as f:
            f.write(invalid_content)
        
        result = self.service._merge_uuid_into_existing_xmp(xmp_path, self.uuid)
        
        assert result is True
        
        # Should have created new valid XMP
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert self.uuid in content
        assert 'imgmaster:GroupUUID' in content
        # Original invalid content should be replaced
        assert 'Test Author' not in content
    
    def test_write_uuid_to_xmp_sidecar_new_file(self):
        """Test writing UUID to a new XMP sidecar file."""
        photo_path = self.temp_dir / "photo.jpg"
        photo_path.touch()  # Create empty photo file
        
        result = self.service._write_uuid_to_xmp_sidecar(photo_path, self.uuid)
        
        assert result is True
        
        xmp_path = photo_path.with_suffix('.xmp')
        assert xmp_path.exists()
        
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert self.uuid in content
    
    def test_write_uuid_to_xmp_sidecar_existing_file(self):
        """Test writing UUID to an existing XMP sidecar file."""
        photo_path = self.temp_dir / "photo.jpg"
        photo_path.touch()
        
        xmp_path = photo_path.with_suffix('.xmp')
        
        # Create existing XMP
        existing_content = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
    <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
        <rdf:Description rdf:about=""
            xmlns:dc="http://purl.org/dc/elements/1.1/"
            dc:creator="Original Author"/>
    </rdf:RDF>
</x:xmpmeta>"""
        
        with open(xmp_path, 'w', encoding='utf-8') as f:
            f.write(existing_content)
        
        result = self.service._write_uuid_to_xmp_sidecar(photo_path, self.uuid)
        
        assert result is True
        
        # Verify existing content preserved and UUID added
        with open(xmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert self.uuid in content
        assert 'dc:creator="Original Author"' in content
        assert 'imgmaster:GroupUUID' in content
