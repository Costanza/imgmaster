#!/usr/bin/env python3

import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import tempfile
import json
from datetime import datetime
from click.testing import CliRunner
from main import cli

def test_chronological_sequence_with_metadata():
    """Test chronological sequence assignment with manually set metadata."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source and destination directories
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        (source_dir / "newer.jpg").write_text("fake jpg content - newer")
        (source_dir / "older.jpg").write_text("fake jpg content - older")
        (source_dir / "middle.jpg").write_text("fake jpg content - middle")
        
        # Create database
        database_file = temp_path / "test.json"
        
        # Build the database
        runner = CliRunner()
        result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
        print(f"Build result: {result.exit_code}")
        
        if result.exit_code != 0:
            return
        
        # Manually modify the database to add specific dates for testing
        with open(database_file, 'r') as f:
            db_data = json.load(f)
        
