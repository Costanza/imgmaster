"""Main CLI application for imgmaster."""

import click
import sys
from pathlib import Path

from services import DatabaseBuildService, PhotoRenameService, ValidationService, PresentationService, LoggingService


@click.group()
def cli():
    """Image Master - Simple, opinionated, photo library file manipulation."""
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
    """
    # Set up logging
    LoggingService.setup_logging(verbose)
    
    # Show initial message
    PresentationService.show_processing_message(f"Scanning directory: {directory}")
    
    try:
        # Build database using service
        database_service = DatabaseBuildService()
        results = database_service.build_database(directory, output, recursive)
        
        # Show results
        PresentationService.show_build_results(results)
        
    except FileNotFoundError as e:
        PresentationService.show_error(str(e))
        sys.exit(1)
    except PermissionError as e:
        PresentationService.show_error(f"Permission error: {e}")
        sys.exit(1)
    except Exception as e:
        PresentationService.show_error(f"Unexpected error: {e}")
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
@click.option('--skip-invalid/--include-invalid', default=True,
              help='Skip invalid photo groups (containing only sidecar/live photos). Default: skip invalid groups')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def rename(database: Path, destination: Path, scheme: str, sequence_digits: int, 
           dry_run: bool, copy: bool, skip_invalid: bool, verbose: bool):
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
    # Set up logging
    LoggingService.setup_logging(verbose)
    
    # Show initial message
    PresentationService.show_processing_message(f"Loading database: {database}")
    
    try:
        # Rename photos using service
        rename_service = PhotoRenameService()
        results = rename_service.rename_photos(
            database, destination, scheme, sequence_digits, 
            dry_run, copy, skip_invalid
        )
        
        # Show results
        PresentationService.show_rename_results(results)
        
    except ValueError as e:
        PresentationService.show_error(f"Invalid naming scheme: {e}")
        sys.exit(1)
    except FileNotFoundError as e:
        PresentationService.show_error(str(e))
        sys.exit(1)
    except PermissionError as e:
        PresentationService.show_error(f"Permission error: {e}")
        sys.exit(1)
    except Exception as e:
        PresentationService.show_error(f"Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.argument('root_folder', type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option('--errors-only', is_flag=True, default=False,
              help='Only show groups with date mismatches (default: show all)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def validate(root_folder: Path, errors_only: bool, verbose: bool):
    """
    Validate photo file names against their metadata dates.

    Scans the ROOT_FOLDER for photo files, extracts metadata, and checks
    if the filenames contain the correct date based on the photo's
    date taken metadata.

    This is useful for verifying that renamed photos have the correct
    dates in their filenames.

    \b
    Expected filename format: YYYYMMDD_* (e.g., 20250315_0001.jpg)

    \b
    Status indicators:
      OK       - Filename date matches metadata date
      MISMATCH - Filename date differs from metadata date
      UNKNOWN  - Could not determine date from filename or metadata
    """
    # Set up logging
    LoggingService.setup_logging(verbose)

    # Show initial message
    PresentationService.show_processing_message(f"Validating photos in: {root_folder}")

    try:
        # Validate photos using service
        validation_service = ValidationService()
        results = validation_service.validate_photos(root_folder, errors_only)

        # Show results
        PresentationService.show_validation_results(results)

    except FileNotFoundError as e:
        PresentationService.show_error(str(e))
        sys.exit(1)
    except PermissionError as e:
        PresentationService.show_error(f"Permission error: {e}")
        sys.exit(1)
    except Exception as e:
        PresentationService.show_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
