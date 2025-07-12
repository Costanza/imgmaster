import os
import tempfile
from pathlib import Path
import pytest
from click.testing import CliRunner

from main import cli
from models.photo_group import PhotoGroupManager


class TestSkipInvalidGroups:
    """Test the --skip-invalid option functionality."""
    
    def test_skip_invalid_groups_default(self):
        """Test that invalid groups are skipped by default."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source and destination directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files - one valid group, one invalid group
            (source_dir / "valid.jpg").write_text("fake jpg content")
            (source_dir / "valid.xmp").write_text("fake xmp content")
            (source_dir / "invalid_sidecar.xmp").write_text("fake xmp content - invalid")
            
            # Create database
            database_file = temp_path / "test.json"
            
            # Build the database
            runner = CliRunner()
            result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
            assert result.exit_code == 0
            
            # Rename with default behavior (should skip invalid groups)
            result = runner.invoke(cli, [
                'rename', 
                str(database_file), 
                str(dest_dir),
                '--scheme', 'photo',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Check output
            output = result.output
            assert "Processing 1 photo groups..." in output
            assert "problematic groups" in output  # Changed from specific skipping message
            assert "Total files to rename: 2" in output  # Only valid group files
            
            # Check that only valid group files are listed
            assert "valid.jpg" in output
            assert "valid.xmp" in output
            assert "invalid_sidecar.xmp" not in output
    
    def test_include_invalid_groups(self):
        """Test that invalid groups are included when --include-invalid is specified."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source and destination directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files - one valid group, one invalid group
            (source_dir / "valid.jpg").write_text("fake jpg content")
            (source_dir / "valid.xmp").write_text("fake xmp content")
            (source_dir / "invalid_sidecar.xmp").write_text("fake xmp content - invalid")
            
            # Create database
            database_file = temp_path / "test.json"
            
            # Build the database
            runner = CliRunner()
            result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
            assert result.exit_code == 0
            
            # Rename with --include-invalid
            result = runner.invoke(cli, [
                'rename', 
                str(database_file), 
                str(dest_dir),
                '--scheme', 'photo',
                '--include-invalid',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Check output
            output = result.output
            assert "Processing 2 photo groups..." in output
            assert "Skipping" not in output  # No skip message
            assert "Total files to rename: 3" in output  # All files including invalid
            
            # Check that all files are listed
            assert "valid.jpg" in output
            assert "valid.xmp" in output
            assert "invalid_sidecar.xmp" in output
    
    def test_skip_invalid_no_invalid_groups(self):
        """Test behavior when there are no invalid groups."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source and destination directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files - only valid groups
            (source_dir / "valid1.jpg").write_text("fake jpg content")
            (source_dir / "valid2.cr2").write_text("fake raw content")
            
            # Create database
            database_file = temp_path / "test.json"
            
            # Build the database
            runner = CliRunner()
            result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
            assert result.exit_code == 0
            
            # Rename with default behavior
            result = runner.invoke(cli, [
                'rename', 
                str(database_file), 
                str(dest_dir),
                '--scheme', 'photo',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Check output
            output = result.output
            assert "Processing 2 photo groups..." in output
            assert "Skipping 0 invalid photo groups" not in output  # No skip message when count is 0
            assert "Total files to rename: 2" in output
    
    def test_skip_invalid_all_groups_invalid(self):
        """Test behavior when all groups are invalid."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source and destination directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files - only invalid groups (sidecar files only)
            (source_dir / "sidecar1.xmp").write_text("fake xmp content")
            (source_dir / "sidecar2.xmp").write_text("fake xmp content 2")
            
            # Create database
            database_file = temp_path / "test.json"
            
            # Build the database
            runner = CliRunner()
            result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
            assert result.exit_code == 0
            
            # Rename with default behavior (should skip all groups)
            result = runner.invoke(cli, [
                'rename', 
                str(database_file), 
                str(dest_dir),
                '--scheme', 'photo',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Check output
            output = result.output
            assert "Processing 0 photo groups..." in output
            assert "problematic groups" in output  # Changed from specific skipping message
            assert "Total files to rename: 0" in output
