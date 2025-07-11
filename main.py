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
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def rename(database: Path, destination: Path, scheme: str, sequence_digits: int, dry_run: bool, verbose: bool):
    """
    Rename photo files based on metadata and grouping rules.
    
    Uses the photo DATABASE to rename files according to the specified SCHEME
    and moves them to the DESTINATION directory based on metadata like dates, 
    camera info, and group relationships.
    
    DATABASE: Path to the JSON database file created by the build command
    DESTINATION: Target directory where renamed files will be moved
    
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
        basename_counter = defaultdict(int)
        
        for group in manager.get_all_groups():
            # Extract metadata for the group
            group_metadata = group.extract_metadata()
            
            # Process each photo in the group
            for photo in group.get_photos():
                # Generate new name based on scheme and metadata
                new_name = _generate_new_filename(
                    scheme, photo, group_metadata, basename_counter, sequence_digits
                )
                
                # Calculate paths - handle subdirectories in the scheme
                old_path = photo.absolute_path
                # Split the new_name into directory parts and filename
                name_parts = new_name.split('/')
                if len(name_parts) > 1:
                    # Has subdirectories
                    subdir_path = Path(*name_parts[:-1])
                    filename = name_parts[-1]
                    new_path = destination / subdir_path / f"{filename}{photo.extension}"
                else:
                    # No subdirectories
                    new_path = destination / f"{new_name}{photo.extension}"
                
                # Ensure directory exists for new path
                new_dir = new_path.parent
                
                rename_operations.append({
                    'group': group,
                    'photo': photo,
                    'old_path': old_path,
                    'new_path': new_path,
                    'new_dir': new_dir
                })
        
        # Show summary
        click.echo(f"\nRename Summary:")
        click.echo(f"Total files to rename: {len(rename_operations)}")
        click.echo(f"Destination: {destination}")
        
        if dry_run:
            click.echo("\n🔍 DRY RUN - No files will be moved:")
            for i, op in enumerate(rename_operations[:10]):  # Show first 10
                click.echo(f"  {op['old_path'].name} -> {op['new_path'].relative_to(destination)}")
            if len(rename_operations) > 10:
                click.echo(f"  ... and {len(rename_operations) - 10} more files")
        else:
            # Perform actual rename operations
            click.echo(f"\n📁 Renaming {len(rename_operations)} files...")
            
            renamed_count = 0
            for op in rename_operations:
                try:
                    # Create directory if needed
                    op['new_dir'].mkdir(parents=True, exist_ok=True)
                    
                    # Move the file
                    shutil.move(str(op['old_path']), str(op['new_path']))
                    
                    # Update photo object with new path and add history
                    _update_photo_with_history(op['photo'], op['old_path'], op['new_path'])
                    
                    renamed_count += 1
                    
                    if renamed_count % 100 == 0:
                        click.echo(f"  Renamed {renamed_count}/{len(rename_operations)} files...")
                        
                except Exception as e:
                    logger.error(f"Failed to rename {op['old_path']} -> {op['new_path']}: {e}")
                    click.echo(f"❌ Error renaming {op['old_path'].name}: {e}")
            
            click.echo(f"✅ Successfully renamed {renamed_count} files")
            
            # Save updated database
            click.echo(f"\nUpdating database...")
            manager.save_to_json(database)
            
            click.echo(f"\n🎉 Rename operation completed!")
            click.echo(f"Files moved to: {destination}")
            click.echo(f"Database updated: {database}")
        
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


def _generate_new_filename(scheme: str, photo, group_metadata, basename_counter: dict, sequence_digits: int) -> str:
    """Generate a new filename based on the scheme and metadata."""
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
    
    # Apply all replacements except sequence
    for placeholder, value in replacements.items():
        new_name = new_name.replace(placeholder, str(value))
    
    # Handle sequence number
    if '{sequence}' in new_name:
        basename_counter[new_name] += 1
        sequence_num = basename_counter[new_name]
        sequence_str = f"{sequence_num:0{sequence_digits}d}"
        new_name = new_name.replace('{sequence}', sequence_str)
    
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


if __name__ == "__main__":
    cli()
