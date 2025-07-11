import os
import tempfile
import shutil
from pathlib import Path
import pytest
from click.testing import CliRunner

from main import cli
from models.photo_group import PhotoGroupManager


class TestSequenceGroupLevel:
    """Test that sequence numbers are applied at the photo group level."""
    
    def test_explicit_sequence_group_level(self):
        """Test that explicit {sequence} placeholders are applied at group level."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source and destination directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files with photo groups
            (source_dir / "vacation.jpg").write_text("fake jpg content")
            (source_dir / "vacation.xmp").write_text("fake xmp content")
            (source_dir / "beach.jpg").write_text("fake jpg content 2")
            (source_dir / "beach.xmp").write_text("fake xmp content 2")
            (source_dir / "mountain.jpg").write_text("fake jpg content 3")
            
            # Create database
            database_file = temp_path / "test.json"
            
            # Build the database
            runner = CliRunner()
            result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
            assert result.exit_code == 0
            
            # Rename with explicit sequence
            result = runner.invoke(cli, [
                'rename', 
                str(database_file), 
                str(dest_dir),
                '--scheme', '{basename}_{sequence}',
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Parse the output to check sequence assignments
            output_lines = result.output.split('\n')
            rename_lines = [line for line in output_lines if '->' in line and 'moved to' in line]
            
            # Extract the filename mappings
            mappings = {}
            for line in rename_lines:
                # Parse lines like: "  vacation.jpg -> moved to -> vacation_001.jpg"
                parts = line.strip().split(' -> moved to -> ')
                if len(parts) == 2:
                    source_file = parts[0].strip()
                    dest_file = parts[1].strip()
                    mappings[source_file] = dest_file
            
            # Verify that files from the same group get the same sequence number
            # Both vacation files should have the same sequence
            vacation_jpg_dest = mappings.get('vacation.jpg', '')
            vacation_xmp_dest = mappings.get('vacation.xmp', '')
            assert vacation_jpg_dest.startswith('vacation_')
            assert vacation_xmp_dest.startswith('vacation_')
            
            # Extract sequence numbers (the part between the last underscore and the extension)
            vacation_jpg_seq = vacation_jpg_dest.split('_')[-1].split('.')[0]
            vacation_xmp_seq = vacation_xmp_dest.split('_')[-1].split('.')[0] 
            assert vacation_jpg_seq == vacation_xmp_seq, f"vacation.jpg and vacation.xmp should have same sequence: {vacation_jpg_seq} vs {vacation_xmp_seq}"
            
            # Both beach files should have the same sequence
            beach_jpg_dest = mappings.get('beach.jpg', '')
            beach_xmp_dest = mappings.get('beach.xmp', '')
            assert beach_jpg_dest.startswith('beach_')
            assert beach_xmp_dest.startswith('beach_')
            
            beach_jpg_seq = beach_jpg_dest.split('_')[-1].split('.')[0]
            beach_xmp_seq = beach_xmp_dest.split('_')[-1].split('.')[0]
            assert beach_jpg_seq == beach_xmp_seq, f"beach.jpg and beach.xmp should have same sequence: {beach_jpg_seq} vs {beach_xmp_seq}"
            
            # Mountain should get its own sequence (single file group)
            mountain_dest = mappings.get('mountain.jpg', '')
            assert mountain_dest.startswith('mountain_')
            
    def test_collision_sequence_group_level(self):
        """Test that automatic collision detection applies sequences at group level."""
        # Create a temporary directory structure
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create source and destination directories
            source_dir = temp_path / "source"
            dest_dir = temp_path / "dest"
            source_dir.mkdir()
            dest_dir.mkdir()
            
            # Create test files with photo groups that will collide when using "photo" scheme
            (source_dir / "vacation.jpg").write_text("fake jpg content")
            (source_dir / "vacation.xmp").write_text("fake xmp content")
            (source_dir / "beach.jpg").write_text("fake jpg content 2")
            (source_dir / "beach.xmp").write_text("fake xmp content 2")
            
            # Create database
            database_file = temp_path / "test.json"
            
            # Build the database
            runner = CliRunner()
            result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
            assert result.exit_code == 0
            
            # Rename with scheme that causes collisions
            result = runner.invoke(cli, [
                'rename', 
                str(database_file), 
                str(dest_dir),
                '--scheme', 'photo',  # This will cause all files to collide
                '--dry-run'
            ])
            assert result.exit_code == 0
            
            # Parse the output to check sequence assignments
            output_lines = result.output.split('\n')
            rename_lines = [line for line in output_lines if '->' in line and 'moved to' in line]
            
            # Extract the filename mappings
            mappings = {}
            for line in rename_lines:
                # Parse lines like: "  vacation.jpg -> moved to -> photo_001.jpg"
                parts = line.strip().split(' -> moved to -> ')
                if len(parts) == 2:
                    source_file = parts[0].strip()
                    dest_file = parts[1].strip()
                    mappings[source_file] = dest_file
            
            # Verify that files from the same group get the same sequence number
            vacation_jpg_dest = mappings.get('vacation.jpg', '')
            vacation_xmp_dest = mappings.get('vacation.xmp', '')
            
            # Extract sequence numbers 
            vacation_jpg_seq = vacation_jpg_dest.split('_')[-1].split('.')[0]
            vacation_xmp_seq = vacation_xmp_dest.split('_')[-1].split('.')[0]
            assert vacation_jpg_seq == vacation_xmp_seq, f"vacation.jpg and vacation.xmp should have same sequence: {vacation_jpg_seq} vs {vacation_xmp_seq}"
            
            # Beach files should also have the same sequence
            beach_jpg_dest = mappings.get('beach.jpg', '')
            beach_xmp_dest = mappings.get('beach.xmp', '')
            
            beach_jpg_seq = beach_jpg_dest.split('_')[-1].split('.')[0]
            beach_xmp_seq = beach_xmp_dest.split('_')[-1].split('.')[0]
            assert beach_jpg_seq == beach_xmp_seq, f"beach.jpg and beach.xmp should have same sequence: {beach_jpg_seq} vs {beach_xmp_seq}"
            
            # But the two groups should have different sequences
            assert vacation_jpg_seq != beach_jpg_seq, f"Different groups should have different sequences: {vacation_jpg_seq} vs {beach_jpg_seq}"
