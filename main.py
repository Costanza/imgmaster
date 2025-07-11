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


if __name__ == "__main__":
    cli()
