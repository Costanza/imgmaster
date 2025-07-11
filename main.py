import click
import logging
import sys
from pathlib import Path
from models import PhotoGroupManager


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(console_handler)
    
    # Set specific loggers
    logging.getLogger('models').setLevel(level)


@click.group()
def cli():
    """Image Master - A powerful image processing CLI tool."""
    pass


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--output', '-o', type=click.Path(path_type=Path), default='photo_database.json',
              help='Output JSON file path (default: photo_database.json)')
@click.option('--recursive/--no-recursive', default=True,
              help='Scan directories recursively (default: True)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def build(directory: Path, output: Path, recursive: bool, verbose: bool):
    """
    Build a photo group database from a directory.
    
    Recursively scans the given DIRECTORY for photo files, groups them by
    basename, and saves the database to a JSON file.
    
    DIRECTORY: Path to the directory to scan for photos
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting photo database build process")
    logger.info(f"Source directory: {directory}")
    logger.info(f"Output file: {output}")
    logger.info(f"Recursive scan: {recursive}")
    
    try:
        # Create photo group manager
        manager = PhotoGroupManager()
        
        # Scan directory for photos
        click.echo(f"Scanning directory: {directory}")
        photos_found = manager.scan_directory(directory, recursive=recursive)
        
        if photos_found == 0:
            click.echo("No photos found in the specified directory.")
            logger.warning("No photos found - exiting")
            return
        
        # Display summary
        click.echo(f"\nScan completed successfully!")
        click.echo(f"Found {photos_found} photos organized into {manager.total_groups} groups")
        click.echo(f"Valid groups (with actual photos): {manager.total_valid_groups}")
        
        # Show invalid groups if any
        invalid_groups = manager.get_invalid_groups()
        if invalid_groups:
            click.echo(f"Invalid groups (sidecar/live photos only): {manager.total_invalid_groups}")
            click.echo("Invalid groups:")
            for group in invalid_groups[:5]:  # Show first 5
                extensions = sorted(group.get_extensions())
                click.echo(f"  {group.basename}: {', '.join(extensions)}")
            if len(invalid_groups) > 5:
                click.echo(f"  ... and {len(invalid_groups) - 5} more invalid groups")
        
        # Show format breakdown
        format_stats = {}
        for group in manager.get_all_groups():
            for photo in group.get_photos():
                format_type = photo.format_classification
                format_stats[format_type] = format_stats.get(format_type, 0) + 1
        
        click.echo("\nFormat breakdown:")
        for format_type, count in sorted(format_stats.items()):
            click.echo(f"  {format_type}: {count} files")
        
        # Show groups with multiple formats
        multi_format_groups = manager.get_groups_with_multiple_formats()
        if multi_format_groups:
            click.echo(f"\nGroups with multiple formats: {len(multi_format_groups)}")
            for group in multi_format_groups[:5]:  # Show first 5
                extensions = sorted(group.get_extensions())
                click.echo(f"  {group.basename}: {', '.join(extensions)}")
            if len(multi_format_groups) > 5:
                click.echo(f"  ... and {len(multi_format_groups) - 5} more")
        
        # Extract metadata for all groups
        click.echo("\nExtracting metadata from photos...")
        manager.extract_all_metadata()
        
        # Save to JSON
        click.echo(f"\nSaving database to: {output}")
        manager.save_to_json(output)
        
        click.echo(f"\n✅ Database successfully created!")
        logger.info("Photo database build completed successfully")
        
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except PermissionError as e:
        click.echo(f"❌ Permission error: {e}", err=True)
        logger.error(f"Permission error: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument('database', type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path))
@click.argument('destination', type=click.Path(file_okay=False, dir_okay=True, path_type=Path))
@click.option('--scheme', '-s', required=True,
              help='Naming scheme with metadata placeholders (e.g., "{date}_{camera_model}_{basename}")')
@click.option('--sequence-digits', type=click.IntRange(1, 6), default=3,
              help='Number of digits for sequence numbers when basenames would be identical (1-6, default: 3)')
@click.option('--dry-run', is_flag=True, default=False,
              help='Show what would be renamed without actually renaming files')
@click.option('--copy', is_flag=True, default=False,
              help='Copy files instead of moving them (leaves originals in place)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def rename(database: Path, destination: Path, scheme: str, sequence_digits: int, dry_run: bool, copy: bool, verbose: bool):
    """
    Rename photo files based on metadata and grouping rules.
    
    Uses the photo DATABASE to rename files according to the specified SCHEME
    and moves them to the DESTINATION directory based on metadata like dates, 
    camera info, and group relationships.
    
    With --copy flag, files are copied instead of moved, leaving originals in place.
    This is useful for testing and validation before committing to the operation.
    
    DATABASE: Path to the JSON database file created by the build command
    DESTINATION: Target directory where renamed files will be moved or copied
    
    NAMING SCHEME PLACEHOLDERS:
    
    \b
    Date/Time:
      {date}          - Date in YYYY-MM-DD format
      {datetime}      - Date and time in YYYY-MM-DD_HH-MM-SS format
      {year}          - 4-digit year
      {month}         - 2-digit month
      {day}           - 2-digit day
      {hour}          - 2-digit hour (24h format)
      {minute}        - 2-digit minute
      {second}        - 2-digit second
    
    \b
    Camera Info:
      {camera_make}   - Camera manufacturer
      {camera_model}  - Camera model
      {lens_model}    - Lens model
      {serial_number} - Camera serial number
    
    \b
    Technical Info:
      {iso}           - ISO value
      {aperture}      - Aperture (f-stop)
      {focal_length}  - Focal length in mm
      {shutter_speed} - Shutter speed
    
    \b
    File Info:
      {basename}      - Original basename (without extension)
      {sequence}      - Auto-generated sequence number for duplicates
    
    \b
    Examples:
      "{date}_{camera_model}_{basename}"
      "{datetime}_{iso}_{aperture}"
      "{year}/{month}/{camera_make}_{sequence}"
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting photo rename process")
    logger.info(f"Database file: {database}")
    logger.info(f"Destination directory: {destination}")
    logger.info(f"Naming scheme: {scheme}")
    logger.info(f"Sequence digits: {sequence_digits}")
    logger.info(f"Dry run mode: {dry_run}")
    logger.info(f"Copy mode: {copy}")
    
    try:
        # Load the photo database
        click.echo(f"Loading database: {database}")
        manager = PhotoGroupManager.load_from_json(database)
        
        # Create destination directory if it doesn't exist
        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)
        
        # Import required modules for renaming
        import re
        import shutil
        from datetime import datetime
        from collections import defaultdict
        
        # Validate the naming scheme
        _validate_naming_scheme(scheme)
        
        # Process all groups and generate new names
        click.echo(f"\nProcessing {manager.total_groups} photo groups...")
        rename_operations = []
        
        # First pass: generate base filenames without sequences
        for group in manager.get_all_groups():
            # Extract metadata for the group
            group_metadata = group.extract_metadata()
            
            # Process each photo in the group
            for photo in group.get_photos():
                # Generate new name based on scheme and metadata (without sequence)
                new_name = _generate_base_filename(scheme, photo, group_metadata)
                
                # Calculate paths - handle subdirectories in the scheme
                old_path = photo.absolute_path
                # Split the new_name into directory parts and filename
                name_parts = new_name.split('/')
                if len(name_parts) > 1:
                    # Has subdirectories
                    subdir_path = Path(*name_parts[:-1])
                    filename = name_parts[-1]
                    base_new_path = destination / subdir_path / filename
                else:
                    # No subdirectories
                    base_new_path = destination / new_name
                
                rename_operations.append({
                    'group': group,
                    'photo': photo,
                    'old_path': old_path,
                    'base_new_path': base_new_path,  # Without extension and without sequence
                    'base_filename': new_name,  # The complete relative path/filename without extension
                    'destination': destination,  # Store destination for path calculations
                })
        
        # Second pass: detect collisions and apply sequences
        _apply_sequences_to_operations(rename_operations, sequence_digits)
        
        # Show summary
        click.echo(f"\nRename Summary:")
        click.echo(f"Total files to rename: {len(rename_operations)}")
        click.echo(f"Destination: {destination}")
        
        if dry_run:
            click.echo("\n🔍 DRY RUN - No files will be moved:")
            for i, op in enumerate(rename_operations[:10]):  # Show first 10
                action = "copied to" if copy else "moved to"
                click.echo(f"  {op['old_path'].name} -> {action} -> {op['new_path'].relative_to(destination)}")
            if len(rename_operations) > 10:
                click.echo(f"  ... and {len(rename_operations) - 10} more files")
        else:
            # Perform actual rename operations
            action_verb = "Copying" if copy else "Renaming"
            click.echo(f"\n📁 {action_verb} {len(rename_operations)} files...")
            
            processed_count = 0
            for op in rename_operations:
                try:
                    # Create directory if needed
                    op['new_dir'].mkdir(parents=True, exist_ok=True)
                    
                    # Copy or move the file based on the copy flag
                    if copy:
                        shutil.copy2(str(op['old_path']), str(op['new_path']))
                        # For copy mode, we don't update the original photo path, but we still track history
                        _add_copy_history(op['photo'], op['old_path'], op['new_path'])
                    else:
                        # Move the file
                        shutil.move(str(op['old_path']), str(op['new_path']))
                        # Update photo object with new path and add history
                        _update_photo_with_history(op['photo'], op['old_path'], op['new_path'])
                    
                    processed_count += 1
                    
                    if processed_count % 100 == 0:
                        click.echo(f"  {action_verb.rstrip('ing')}ed {processed_count}/{len(rename_operations)} files...")
                        
                except Exception as e:
                    logger.error(f"Failed to {action_verb.lower()} {op['old_path']} -> {op['new_path']}: {e}")
                    click.echo(f"❌ Error {action_verb.lower()} {op['old_path'].name}: {e}")
            
            success_verb = "copied" if copy else "renamed"
            click.echo(f"✅ Successfully {success_verb} {processed_count} files")
            
            # Save updated database (only if we moved files, not copied)
            if not copy:
                click.echo(f"\nUpdating database...")
                manager.save_to_json(database)
            
            click.echo(f"\n🎉 {action_verb} operation completed!")
            click.echo(f"Files {success_verb} to: {destination}")
            if not copy:
                click.echo(f"Database updated: {database}")
            else:
                click.echo(f"Original files preserved at their original locations")
                click.echo(f"Database unchanged (copy operation)")
        
        logger.info("Photo rename process completed")
        
    except FileNotFoundError as e:
        click.echo(f"❌ Error: {e}", err=True)
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        click.echo(f"❌ Invalid naming scheme: {e}", err=True)
        logger.error(f"Invalid naming scheme: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)


def _validate_naming_scheme(scheme: str) -> None:
    """Validate that the naming scheme contains valid placeholders."""
    import re
    
    # Find all placeholders in the scheme
    placeholders = re.findall(r'\{([^}]+)\}', scheme)
    
    valid_placeholders = {
        'date', 'datetime', 'year', 'month', 'day', 'hour', 'minute', 'second',
        'camera_make', 'camera_model', 'lens_model', 'serial_number',
        'iso', 'aperture', 'focal_length', 'shutter_speed',
        'basename', 'sequence'
    }
    
    invalid_placeholders = set(placeholders) - valid_placeholders
    if invalid_placeholders:
        raise ValueError(f"Invalid placeholders: {', '.join(invalid_placeholders)}")


def _generate_base_filename(scheme: str, photo, group_metadata) -> str:
    """Generate a base filename based on the scheme and metadata (without sequence numbers)."""
    import re
    from datetime import datetime
    
    # Start with the scheme
    new_name = scheme
    
    # Extract metadata components
    camera = group_metadata.camera if hasattr(group_metadata, 'camera') else None
    dates = group_metadata.dates if hasattr(group_metadata, 'dates') else None
    technical = group_metadata.technical if hasattr(group_metadata, 'technical') else None
    
    # Date/time replacements
    if dates and dates.date_taken:
        dt = dates.date_taken
        replacements = {
            '{date}': dt.strftime('%Y-%m-%d'),
            '{datetime}': dt.strftime('%Y-%m-%d_%H-%M-%S'),
            '{year}': dt.strftime('%Y'),
            '{month}': dt.strftime('%m'),
            '{day}': dt.strftime('%d'),
            '{hour}': dt.strftime('%H'),
            '{minute}': dt.strftime('%M'),
            '{second}': dt.strftime('%S'),
        }
    else:
        # Use file modification time as fallback
        mtime = datetime.fromtimestamp(photo.absolute_path.stat().st_mtime)
        replacements = {
            '{date}': mtime.strftime('%Y-%m-%d'),
            '{datetime}': mtime.strftime('%Y-%m-%d_%H-%M-%S'),
            '{year}': mtime.strftime('%Y'),
            '{month}': mtime.strftime('%m'),
            '{day}': mtime.strftime('%d'),
            '{hour}': mtime.strftime('%H'),
            '{minute}': mtime.strftime('%M'),
            '{second}': mtime.strftime('%S'),
        }
    
    # Camera info replacements
    if camera:
        replacements.update({
            '{camera_make}': _safe_filename(camera.make or 'Unknown'),
            '{camera_model}': _safe_filename(camera.model or 'Unknown'),
            '{lens_model}': _safe_filename(camera.lens_model or 'Unknown'),
            '{serial_number}': _safe_filename(camera.serial_number or 'Unknown'),
        })
    else:
        replacements.update({
            '{camera_make}': 'Unknown',
            '{camera_model}': 'Unknown',
            '{lens_model}': 'Unknown',
            '{serial_number}': 'Unknown',
        })
    
    # Technical info replacements
    if technical:
        replacements.update({
            '{iso}': str(technical.iso or 'Unknown'),
            '{aperture}': f"f{technical.aperture}" if technical.aperture else 'Unknown',
            '{focal_length}': f"{technical.focal_length}mm" if technical.focal_length else 'Unknown',
            '{shutter_speed}': str(technical.shutter_speed or 'Unknown'),
        })
    else:
        replacements.update({
            '{iso}': 'Unknown',
            '{aperture}': 'Unknown',
            '{focal_length}': 'Unknown',
            '{shutter_speed}': 'Unknown',
        })
    
    # File info replacements
    replacements['{basename}'] = photo.basename
    
    # Apply all replacements (skip sequence for now)
    for placeholder, value in replacements.items():
        new_name = new_name.replace(placeholder, str(value))
    
    # Clean up the filename - handle directory separators properly
    if '/' in new_name:
        # Has subdirectories - clean each part separately
        parts = new_name.split('/')
        clean_parts = [_safe_filename(part) for part in parts]
        new_name = '/'.join(clean_parts)
    else:
        # No subdirectories - clean the whole name
        new_name = _safe_filename(new_name)
    
    return new_name


def _safe_filename(filename: str) -> str:
    """Make a string safe for use as a filename (single part, no directories)."""
    import re
    
    # Replace unsafe characters with underscores (excluding forward slash since we handle that separately)
    safe_name = re.sub(r'[<>:"|\\?*]', '_', filename)
    
    # Remove multiple consecutive underscores
    safe_name = re.sub(r'_+', '_', safe_name)
    
    # Remove leading/trailing underscores and spaces
    safe_name = safe_name.strip('_ ')
    
    return safe_name


def _update_photo_with_history(photo, old_path: Path, new_path: Path) -> None:
    """Update photo object with new path and add history entry."""
    from datetime import datetime
    
    # Add history entry if not already present
    if not hasattr(photo, 'history'):
        photo.history = []
    
    # Add the old location to history
    photo.history.append({
        'path': str(old_path),
        'timestamp': datetime.now().isoformat(),
        'operation': 'rename'
    })
    
    # Update the photo's path
    photo.absolute_path = new_path


def _add_copy_history(photo, old_path: Path, new_path: Path) -> None:
    """Add copy history entry to photo object without updating the path."""
    from datetime import datetime
    
    # Add history entry if not already present
    if not hasattr(photo, 'history'):
        photo.history = []
    
    # Add the copy operation to history
    photo.history.append({
        'original_path': str(old_path),
        'copied_to': str(new_path),
        'timestamp': datetime.now().isoformat(),
        'operation': 'copy'
    })
    # Note: We don't update photo.absolute_path for copy operations


def _apply_sequences_to_operations(rename_operations: list, sequence_digits: int) -> None:
    """Apply sequence numbers to rename operations where filenames would collide."""
    from collections import defaultdict
    
    # Check if any operation has {sequence} placeholder in the base filename
    has_sequence_placeholder = any('{sequence}' in op['base_filename'] for op in rename_operations)
    
    if has_sequence_placeholder:
        # Handle explicit {sequence} placeholders
        _apply_explicit_sequences(rename_operations, sequence_digits)
    else:
        # Handle automatic collision detection
        _apply_collision_sequences(rename_operations, sequence_digits)


def _apply_explicit_sequences(rename_operations: list, sequence_digits: int) -> None:
    """Apply sequences for operations that have explicit {sequence} placeholders."""
    from collections import defaultdict
    
    # Group operations by their base filename pattern (with {sequence} still in place)
    pattern_groups = defaultdict(list)
    
    for operation in rename_operations:
        base_filename = operation['base_filename']
        pattern_groups[base_filename].append(operation)
    
    # Apply sequences to each pattern group
    for pattern, operations in pattern_groups.items():
        for i, operation in enumerate(operations, 1):
            # Replace {sequence} with the actual sequence number
            sequence_str = f"{i:0{sequence_digits}d}"
            final_filename = pattern.replace('{sequence}', sequence_str)
            
            # Calculate final paths using the stored destination
            destination = operation['destination']
            name_parts = final_filename.split('/')
            if len(name_parts) > 1:
                # Has subdirectories
                subdir_path = Path(*name_parts[:-1])
                filename = name_parts[-1]
                final_path = destination / subdir_path / f"{filename}{operation['photo'].extension}"
            else:
                # No subdirectories
                final_path = destination / f"{final_filename}{operation['photo'].extension}"
            
            operation['new_path'] = final_path
            operation['new_dir'] = final_path.parent


def _apply_collision_sequences(rename_operations: list, sequence_digits: int) -> None:
    """Apply sequences for operations that would collide (automatic collision detection)."""
    from collections import defaultdict
    
    # Group operations by their final filename (including extension and full path)
    filename_groups = defaultdict(list)
    
    for operation in rename_operations:
        # Create the full filename with extension
        base_path = operation['base_new_path']
        extension = operation['photo'].extension
        full_path = f"{base_path}{extension}"
        
        filename_groups[str(full_path)].append(operation)
    
    # Process each group of files that would have the same name
    for full_path, operations in filename_groups.items():
        if len(operations) == 1:
            # No collision - use the base path as-is
            operation = operations[0]
            base_path = operation['base_new_path']
            extension = operation['photo'].extension
            final_path = Path(f"{base_path}{extension}")
            
            operation['new_path'] = final_path
            operation['new_dir'] = final_path.parent
        else:
            # Collision detected - apply sequences
            for i, operation in enumerate(operations, 1):
                base_path = operation['base_new_path']
                extension = operation['photo'].extension
                
                # Insert sequence number before the extension
                sequence_str = f"_{i:0{sequence_digits}d}"
                final_path = Path(f"{base_path}{sequence_str}{extension}")
                
                operation['new_path'] = final_path
                operation['new_dir'] = final_path.parent


if __name__ == "__main__":
    cli()
