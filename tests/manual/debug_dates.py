#!/usr/bin/env python3

import tempfile
import json
from pathlib import Path
from datetime import datetime
from click.testing import CliRunner
from main import cli
from repositories import JsonFilePhotoGroupRepository

def debug_chronological_sequence():
    """Debug chronological sequence assignment."""
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
        result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file), '--verbose'])
        print(f"Build result: {result.exit_code}")
        print(f"Build output: {result.output}")
        
        if result.exit_code != 0:
            return
        
        # Manually modify the database to add specific dates for testing
        with open(database_file, 'r') as f:
            db_data = json.load(f)
        
        # Set specific dates to test chronological ordering
        # older: 2020-01-01, middle: 2021-01-01, newer: 2022-01-01
        for group_name, group_data in db_data['groups'].items():
            if group_name == 'older':
                db_data['groups'][group_name]['metadata']['dates']['date_taken'] = '2020-01-01T12:00:00'
            elif group_name == 'middle':
                db_data['groups'][group_name]['metadata']['dates']['date_taken'] = '2021-01-01T12:00:00'
            elif group_name == 'newer':
                db_data['groups'][group_name]['metadata']['dates']['date_taken'] = '2022-01-01T12:00:00'
        
        # Save the modified database
        with open(database_file, 'w') as f:
            json.dump(db_data, f, indent=2)
        
        # Load and examine the groups
        repo = JsonFilePhotoGroupRepository()
        manager = repo.load(str(database_file))
        
        print("\nGroup dates after loading:")
        for group in manager.get_all_groups():
            metadata = group.extract_metadata()
            print(f"  {group.basename}: {metadata.dates.date_taken}")

if __name__ == "__main__":
    debug_chronological_sequence()
