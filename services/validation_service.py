"""Validation service for checking photo file naming against metadata dates."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from models import PhotoGroupManager


class ValidationService:
    """Service for validating photo file names against metadata dates."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_photos(
        self,
        root_folder: Path,
        errors_only: bool = False
    ) -> Dict[str, Any]:
        """
        Validate photo file names against their metadata dates.

        Args:
            root_folder: Root folder to scan for photo groups
            errors_only: If True, only return groups with mismatches

        Returns:
            Dictionary with validation results

        Raises:
            FileNotFoundError: If root_folder doesn't exist
        """
        self.logger.info(f"Starting photo validation")
        self.logger.info(f"Root folder: {root_folder}")
        self.logger.info(f"Errors only: {errors_only}")

        # Initialize manager and scan directory
        manager = PhotoGroupManager()
        manager.scan_directory(root_folder, recursive=True)

        # Check if any photos were found
        if manager.total_photos == 0:
            self.logger.warning("No photos found")
            return {
                'total_groups': 0,
                'validated_groups': 0,
                'ok_count': 0,
                'mismatch_count': 0,
                'unknown_count': 0,
                'groups': [],
                'no_photos_found': True
            }

        # Extract metadata for all groups
        self.logger.info("Extracting metadata for all photo groups...")
        manager.extract_all_metadata()

        # Validate each group
        validation_results = []
        ok_count = 0
        mismatch_count = 0
        unknown_count = 0

        for group in manager.get_all_groups():
            result = self._validate_group(group)

            if result['status'] == 'OK':
                ok_count += 1
            elif result['status'] == 'MISMATCH':
                mismatch_count += 1
            else:
                unknown_count += 1

            # Apply filter
            if errors_only and result['status'] == 'OK':
                continue

            validation_results.append(result)

        self.logger.info(f"Validation complete: {ok_count} OK, {mismatch_count} mismatches, {unknown_count} unknown")

        return {
            'total_groups': manager.total_groups,
            'validated_groups': len(validation_results),
            'ok_count': ok_count,
            'mismatch_count': mismatch_count,
            'unknown_count': unknown_count,
            'groups': validation_results,
            'no_photos_found': False
        }

    def _validate_group(self, group) -> Dict[str, Any]:
        """
        Validate a single photo group.

        Args:
            group: PhotoGroup to validate

        Returns:
            Dictionary with validation details for this group
        """
        photos = group.get_photos()
        if not photos:
            return {
                'basename': group.basename,
                'files': [],
                'date_sources': [],
                'filename_date': None,
                'metadata_date': None,
                'status': 'UNKNOWN',
                'message': 'No photos in group'
            }

        # Get the first photo to extract filename date
        first_photo = photos[0]
        current_filename = first_photo.basename

        # Extract date from filename
        filename_date = self._extract_date_from_filename(current_filename)

        # Get all date sources from group
        date_sources = self._get_all_date_sources(group)

        # Get metadata date_taken
        metadata = group.extract_metadata()
        metadata_date = None
        if metadata.dates and metadata.dates.date_taken:
            metadata_date = metadata.dates.date_taken

        # Compare dates
        status, message = self._compare_dates(filename_date, metadata_date)

        return {
            'basename': group.basename,
            'current_filename': current_filename,
            'files': [p.filename for p in photos],
            'date_sources': date_sources,
            'filename_date': filename_date.strftime('%Y%m%d') if filename_date else None,
            'metadata_date': metadata_date.strftime('%Y%m%d') if metadata_date else None,
            'metadata_datetime': metadata_date.isoformat() if metadata_date else None,
            'status': status,
            'message': message
        }

    def _extract_date_from_filename(self, filename: str) -> Optional[datetime]:
        """
        Extract date from a filename.

        Expects format like: YYYYMMDD_XXXX or YYYYMMDD-XXXX or just YYYYMMDD at start

        Args:
            filename: The filename (without extension) to parse

        Returns:
            datetime if date found, None otherwise
        """
        # Pattern for YYYYMMDD at the start of filename
        pattern = r'^(\d{4})(\d{2})(\d{2})'
        match = re.match(pattern, filename)

        if match:
            try:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                return datetime(year, month, day)
            except ValueError:
                return None

        return None

    def _get_all_date_sources(self, group) -> List[Dict[str, Any]]:
        """
        Get all available date information from files in a group.

        Args:
            group: PhotoGroup to extract dates from

        Returns:
            List of date source dictionaries
        """
        date_sources = []

        for photo in group.get_photos():
            # Get file modification time
            try:
                mtime = datetime.fromtimestamp(photo.absolute_path.stat().st_mtime)
                date_sources.append({
                    'file': photo.filename,
                    'source': 'File mtime',
                    'date': mtime.isoformat()
                })
            except Exception:
                pass

            # For non-sidecar files, try to extract EXIF
            if photo.format_classification != 'sidecar':
                try:
                    from models.metadata import MetadataExtractor
                    extractor = MetadataExtractor()
                    metadata = extractor.extract_from_photo(photo.absolute_path)
                    if metadata.dates and metadata.dates.date_taken:
                        date_sources.append({
                            'file': photo.filename,
                            'source': 'EXIF DateTimeOriginal',
                            'date': metadata.dates.date_taken.isoformat()
                        })
                except Exception:
                    pass

            # For sidecar files (XMP), extract XMP dates
            if photo.format_classification == 'sidecar' and photo.extension.lower() in ['.xmp', '.xml']:
                try:
                    from models.metadata import MetadataExtractor
                    extractor = MetadataExtractor()
                    metadata = extractor.extract_from_xmp(photo.absolute_path)
                    if metadata.dates and metadata.dates.date_taken:
                        date_sources.append({
                            'file': photo.filename,
                            'source': 'XMP DateCreated',
                            'date': metadata.dates.date_taken.isoformat()
                        })
                except Exception:
                    pass

        return date_sources

    def _compare_dates(
        self,
        filename_date: Optional[datetime],
        metadata_date: Optional[datetime]
    ) -> tuple:
        """
        Compare filename date with metadata date.

        Args:
            filename_date: Date extracted from filename
            metadata_date: Date from metadata

        Returns:
            Tuple of (status, message)
        """
        if filename_date is None:
            return ('UNKNOWN', 'Could not extract date from filename')

        if metadata_date is None:
            return ('UNKNOWN', 'No metadata date available')

        # Compare just the date portion (ignore time)
        if filename_date.date() == metadata_date.date():
            return ('OK', 'Filename date matches metadata')
        else:
            return ('MISMATCH', f'Filename has {filename_date.strftime("%Y%m%d")} but metadata has {metadata_date.strftime("%Y%m%d")}')
