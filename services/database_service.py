"""Database building service for photo group management."""

import logging
from pathlib import Path
from typing import Dict, Any

from models import PhotoGroupManager
from repositories import PhotoGroupRepository, JsonFilePhotoGroupRepository


class DatabaseBuildService:
    """Service for building photo group databases."""
    
    def __init__(self, repository: PhotoGroupRepository = None):
        self.logger = logging.getLogger(__name__)
        self.repository = repository or JsonFilePhotoGroupRepository()
    
    def build_database(
        self, 
        directory: Path, 
        output: Path, 
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Build a photo group database from a directory.
        
        Args:
            directory: Source directory to scan
            output: Output JSON file path
            recursive: Whether to scan recursively
            
        Returns:
            Dictionary with build results and statistics
            
        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If unable to write to output file
            ValueError: If no photos found
        """
        self.logger.info(f"Starting photo database build process")
        self.logger.info(f"Source directory: {directory}")
        self.logger.info(f"Output file: {output}")
        self.logger.info(f"Recursive scan: {recursive}")
        
        # Initialize manager and scan directory
        manager = PhotoGroupManager()
        manager.scan_directory(directory, recursive=recursive)
        
        # Check if any photos were found
        if manager.total_photos == 0:
            self.logger.warning("No photos found - exiting")
            return {
                'total_photos': 0,
                'total_groups': 0,
                'valid_groups': 0,
                'invalid_groups': 0,
                'format_breakdown': {},
                'multi_format_groups': [],
                'multi_format_groups_total': 0,
                'invalid_groups_list': [],
                'no_photos_found': True
            }
        
        # Build result statistics
        results = self._build_statistics(manager)
        
        # Extract metadata for all groups
        self.logger.info("Extracting metadata for all photo groups...")
        manager.extract_all_metadata()
        
        # Add date extraction summary to results
        self.logger.info("Building date extraction summary...")
        date_summary = self._build_date_extraction_summary(manager)
        self.logger.info(f"Date extraction summary: {date_summary}")
        results['date_extraction_summary'] = date_summary
        
        # Save to repository
        self.logger.info(f"Saving photo database to: {output}")
        self.repository.save(manager, str(output))
        
        self.logger.info("Photo database build completed successfully")
        return results
    
    def _build_statistics(self, manager: PhotoGroupManager) -> Dict[str, Any]:
        """Build statistics about the scanned photos."""
        # Get format breakdown
        format_breakdown = {}
        for group in manager.get_all_groups():
            for photo in group.get_photos():
                format_type = photo.format_classification
                format_breakdown[format_type] = format_breakdown.get(format_type, 0) + 1
        
        # Get groups with multiple formats
        multi_format_groups = manager.get_groups_with_multiple_formats()
        
        # Get invalid groups
        invalid_groups = manager.get_invalid_groups()
        
        return {
            'total_photos': manager.total_photos,
            'total_groups': manager.total_groups,
            'valid_groups': manager.total_valid_groups,
            'invalid_groups': manager.total_invalid_groups,
            'format_breakdown': format_breakdown,
            'multi_format_groups': [
                {
                    'basename': group.basename,
                    'extensions': sorted(group.get_extensions())
                }
                for group in multi_format_groups[:5]  # Limit to first 5
            ],
            'multi_format_groups_total': len(multi_format_groups),
            'invalid_groups_list': [
                {
                    'basename': group.basename,
                    'extensions': sorted(group.get_extensions())
                }
                for group in invalid_groups[:5]  # Limit to first 5
            ]
        }
    
    def _build_date_extraction_summary(self, manager: PhotoGroupManager) -> Dict[str, Any]:
        """Build summary of date extraction results."""
        summary = manager.date_extraction_summary
        
        # Convert to dictionary for JSON serialization
        result = {
            'total_files_processed': summary.total_files_processed,
            'successful_extractions': summary.successful_extractions,
            'failed_extractions': summary.failed_extractions,
            'failure_summary': {}
        }
        
        if summary.failures:
            # Group failures by error reason
            from collections import defaultdict
            failures_by_reason = defaultdict(list)
            failures_by_extension = defaultdict(int)
            
            for failure in summary.failures:
                failures_by_reason[failure.error_reason].append({
                    'file_path': failure.file_path,
                    'group_basename': failure.group_basename,
                    'file_extension': failure.file_extension,
                    'attempted_methods': failure.attempted_methods
                })
                failures_by_extension[failure.file_extension or 'unknown'] += 1
            
            result['failure_summary'] = {
                'by_error_reason': dict(failures_by_reason),
                'by_file_extension': dict(failures_by_extension),
                'total_unique_error_reasons': len(failures_by_reason),
                'sample_failures': summary.failures[:10]  # First 10 failures as examples
            }
        
        return result
