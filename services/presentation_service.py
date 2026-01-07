"""Presentation service for formatting CLI output."""

import click
from typing import Dict, Any, List


class PresentationService:
    """Service for formatting and presenting information to users."""
    
    @staticmethod
    def show_build_results(results: Dict[str, Any]) -> None:
        """Display the results of a database build operation."""
        if results.get('no_photos_found'):
            click.echo("No photos found in the specified directory.")
            return
            
        click.echo("\nScan completed successfully!")
        click.echo(f"Found {results['total_photos']} photos organized into {results['total_groups']} groups")
        click.echo(f"Valid groups (with actual photos): {results['valid_groups']}")
        
        # Show invalid groups if any
        if results['invalid_groups'] > 0:
            click.echo(f"Invalid groups (sidecar/live photos only): {results['invalid_groups']}")
            click.echo("Invalid groups:")
            for group in results['invalid_groups_list']:
                extensions = ', '.join(group['extensions'])
                click.echo(f"  {group['basename']}: {extensions}")
            if len(results['invalid_groups_list']) < results['invalid_groups']:
                remaining = results['invalid_groups'] - len(results['invalid_groups_list'])
                click.echo(f"  ... and {remaining} more invalid groups")
        
        # Show format breakdown
        if results['format_breakdown']:
            click.echo(f"\nFormat breakdown:")
            for format_type, count in results['format_breakdown'].items():
                click.echo(f"  {format_type}: {count} files")
        
        # Show groups with multiple formats
        if results['multi_format_groups']:
            click.echo(f"\nGroups with multiple formats: {results['multi_format_groups_total']}")
            for group in results['multi_format_groups']:
                extensions = ', '.join(group['extensions'])
                click.echo(f"  {group['basename']}: {extensions}")
            if len(results['multi_format_groups']) < results['multi_format_groups_total']:
                remaining = results['multi_format_groups_total'] - len(results['multi_format_groups'])
                click.echo(f"  ... and {remaining} more")
        
        click.echo(f"\n✅ Database successfully created!")
    
    @staticmethod
    def show_rename_results(results: Dict[str, Any]) -> None:
        """Display the results of a rename operation."""
        click.echo(f"\nProcessing {results['total_groups_processed']} photo groups...")
        
        if results['invalid_groups_skipped'] > 0:
            click.echo(f"Skipping {results['invalid_groups_skipped']} invalid photo groups (containing only sidecar/live photos)")
        
        click.echo(f"\nRename Summary:")
        click.echo(f"Total files to rename: {results['total_files']}")
        click.echo(f"Destination: {results['destination']}")
        
        if results['dry_run']:
            click.echo("\n🔍 DRY RUN - No files will be moved:")
            for op in results['operations']:
                click.echo(f"  {op['source']} -> {op['action']} -> {op['destination']}")
            if len(results['operations']) < results['total_files']:
                remaining = results['total_files'] - len(results['operations'])
                click.echo(f"  ... and {remaining} more files")
        else:
            action_verb = "Copying" if results['copy_mode'] else "Renaming"
            success_verb = "copied" if results['copy_mode'] else "renamed"
            
            click.echo(f"\n📁 {action_verb} {results['total_files']} files...")
            click.echo(f"✅ Successfully {success_verb} {results['processed_count']} files")
            
            if results['database_updated']:
                click.echo(f"\nUpdating database...")
                click.echo(f"Database updated: {results['destination']}")
            else:
                click.echo(f"Original files preserved at their original locations")
                click.echo(f"Database unchanged (copy operation)")
            
            click.echo(f"\n🎉 {action_verb} operation completed!")
            click.echo(f"Files {success_verb} to: {results['destination']}")
    
    @staticmethod
    def show_error(message: str, error_type: str = "Error") -> None:
        """Display an error message."""
        click.echo(f"❌ {error_type}: {message}", err=True)
    
    @staticmethod
    def show_processing_message(message: str) -> None:
        """Display a processing message."""
        click.echo(message)

    @staticmethod
    def show_validation_results(results: Dict[str, Any]) -> None:
        """Display the results of a validation operation."""
        if results.get('no_photos_found'):
            click.echo("No photos found in the specified directory.")
            return

        click.echo(f"\nValidation Summary:")
        click.echo(f"Total groups scanned: {results['total_groups']}")
        click.echo(f"OK: {results['ok_count']}")
        click.echo(f"Mismatches: {results['mismatch_count']}")
        click.echo(f"Unknown: {results['unknown_count']}")

        if not results['groups']:
            click.echo("\nNo groups to display.")
            return

        click.echo(f"\n{'='*60}")

        for group in results['groups']:
            PresentationService._show_group_validation(group)

        click.echo(f"{'='*60}")

        if results['mismatch_count'] > 0:
            click.echo(f"\n⚠️  {results['mismatch_count']} group(s) have date mismatches")
        else:
            click.echo(f"\n✅ All groups validated successfully!")

    @staticmethod
    def _show_group_validation(group: Dict[str, Any]) -> None:
        """Display validation details for a single group."""
        # Status indicator
        if group['status'] == 'OK':
            status_icon = '✓'
            status_color = 'green'
        elif group['status'] == 'MISMATCH':
            status_icon = '✗'
            status_color = 'red'
        else:
            status_icon = '?'
            status_color = 'yellow'

        click.echo(f"\nGroup: {group['basename']}")
        click.echo(f"  Current filename: {group.get('current_filename', group['basename'])}")
        click.echo(f"  Files: {', '.join(group['files'])}")

        # Date sources
        if group['date_sources']:
            click.echo(f"  Date Sources:")
            for source in group['date_sources']:
                click.echo(f"    - {source['file']} ({source['source']}): {source['date']}")

        # Comparison
        click.echo(f"  Filename date: {group['filename_date'] or 'N/A'}")
        click.echo(f"  Metadata date: {group['metadata_date'] or 'N/A'}")
        if group.get('metadata_datetime'):
            click.echo(f"  Metadata datetime: {group['metadata_datetime']}")

        # Status
        click.secho(f"  Status: {status_icon} {group['status']} - {group['message']}", fg=status_color)
