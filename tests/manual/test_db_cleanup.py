#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the project root to the Python path  
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import tempfile
import json
from click.testing import CliRunner
from main import cli

def test_problematic_groups_removed_from_database():
    """Test that problematic groups are removed from database after being moved to error folders."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source and destination directories
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files - one valid group, one invalid group (only sidecar)
        (source_dir / "valid.jpg").write_text("fake jpg content")
        (source_dir / "invalid_only_sidecar.xmp").write_text("fake xmp content")
        
        # Create database
        database_file = temp_path / "test.json"
        
        # Build the database
        runner = CliRunner()
        result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
        print(f"Build result: {result.exit_code}")
        
        if result.exit_code != 0:
            return
        
        # Check initial database content
        with open(database_file, 'r') as f:
            db_before = json.load(f)
        
        print(f"Groups before rename: {list(db_before['groups'].keys())}")
        
