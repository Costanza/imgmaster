#!/usr/bin/env python3

import tempfile
from pathlib import Path
from click.testing import CliRunner
from main import cli

def test_debug():
    """Debug test to see what's happening."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create source and destination directories
        source_dir = temp_path / "source"
        dest_dir = temp_path / "dest"
        source_dir.mkdir()
        dest_dir.mkdir()
        
        # Create test files
        (source_dir / "vacation.jpg").write_text("fake jpg content")
        (source_dir / "vacation.xmp").write_text("fake xmp content")
        (source_dir / "beach.jpg").write_text("fake jpg content 2")
        
        # Create database
        database_file = temp_path / "test.json"
        
        # Build the database
        runner = CliRunner()
        result = runner.invoke(cli, ['build', str(source_dir), '--output', str(database_file)])
        print(f"Build result: {result.exit_code}")
        print(f"Build output: {result.output}")
        
        if result.exit_code != 0:
            return
        
        # Rename with explicit sequence
        result = runner.invoke(cli, [
            'rename',
            str(database_file),
            str(dest_dir),
            '--scheme', '{basename}_{sequence}',
            '--dry-run'
        ])
        print(f"Rename result: {result.exit_code}")
        print(f"Rename output: {result.output}")
        if result.exception:
            print(f"Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exception.__traceback__)

if __name__ == "__main__":
    test_debug()
