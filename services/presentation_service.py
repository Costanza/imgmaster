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
