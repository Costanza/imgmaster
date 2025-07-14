"""Photo renaming service for file operations."""

import json
import logging
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from models import PhotoGroupManager
from repositories import PhotoGroupRepository, JsonFilePhotoGroupRepository
from services.error_handling_service import ErrorHandlingService, ErrorType


class PhotoRenameService:
    """Service for renaming and organizing photo files."""
    
    def __init__(self, repository: PhotoGroupRepository = None):
        self.logger = logging.getLogger(__name__)
        self.repository = repository or JsonFilePhotoGroupRepository()
        self.error_handler = ErrorHandlingService()
        from services.exif_merge_service import ExifMergeService
        self.exif_merge_service = ExifMergeService()
    
    def rename_photos(
        self,
        database_path: Path,
        destination: Path,
        scheme: str,
        sequence_digits: int = 3,
        dry_run: bool = False,
        copy_mode: bool = False,
        skip_invalid: bool = True
    ) -> Dict[str, Any]:
        """
        Rename photo files based on metadata and grouping rules.
        
        Args:
            database_path: Path to the JSON database file
            destination: Target directory for renamed files
            scheme: Naming scheme with metadata placeholders
            sequence_digits: Number of digits for sequence numbers
            dry_run: If True, only show what would be done
            copy_mode: If True, copy files instead of moving them
            skip_invalid: If True, skip invalid photo groups
            
        Returns:
            Dictionary with operation results and statistics
        """
        self.logger.info("Starting photo rename process")
        self.logger.info(f"Database file: {database_path}")
        self.logger.info(f"Destination directory: {destination}")
        self.logger.info(f"Naming scheme: {scheme}")
        self.logger.info(f"Sequence digits: {sequence_digits}")
        self.logger.info(f"Dry run mode: {dry_run}")
        self.logger.info(f"Copy mode: {copy_mode}")
        self.logger.info(f"Skip invalid groups: {skip_invalid}")
        
        # Load the photo database using repository
        manager = self.repository.load(str(database_path))
        
        # Create destination directory if needed
        if not dry_run:
            destination.mkdir(parents=True, exist_ok=True)
        
        # Validate the naming scheme
        self._validate_naming_scheme(scheme)
        
        # Separate valid groups from problematic ones
        valid_groups, problematic_groups = self._classify_groups(manager.get_all_groups())
        
        # Handle problematic groups based on skip_invalid flag
        error_results = {}
        if skip_invalid:
            # Skip problematic groups by moving to error folders in their SOURCE directories (if not dry_run)
            if not dry_run and problematic_groups:
                error_results = self._handle_problematic_groups_in_source(problematic_groups)
            
            # Check valid groups for required metadata and move those that fail to error folders too
            groups_to_process = []
            groups_missing_metadata = []
            
            for group in valid_groups:
                if self._group_has_required_metadata(group, scheme):
                    groups_to_process.append(group)
                else:
                    groups_missing_metadata.append((group, ErrorType.MISSING_DATE, "Required metadata missing for naming scheme"))
            
            # Move groups with missing required metadata to error folders
            if not dry_run and groups_missing_metadata:
                missing_metadata_results = self._handle_problematic_groups_in_source(groups_missing_metadata)
                # Add to problematic_groups list so they get removed from database
                problematic_groups.extend(groups_missing_metadata)
            
            # Count groups that would be skipped due to invalid metadata
            invalid_metadata_count = len(groups_missing_metadata)
        else:
            # Include problematic groups in processing
            all_groups = valid_groups + [group for group, _, _ in problematic_groups]
            groups_to_process = all_groups
            invalid_metadata_count = 0
        
        # Generate rename operations
        rename_operations = self._generate_rename_operations(
            groups_to_process, destination, scheme
        )
        
        # Apply sequence numbers to handle collisions
        self._apply_sequences_to_operations(rename_operations, sequence_digits)
        
        # Build results
        results = {
            'total_groups_processed': len(groups_to_process),
            'problematic_groups_moved': len(problematic_groups) if skip_invalid else 0,
            'invalid_metadata_skipped': invalid_metadata_count,
            'total_files': len(rename_operations),
            'dry_run': dry_run,
            'copy_mode': copy_mode,
            'destination': str(destination),
            'operations': [],
            'error_summary': self.error_handler.get_error_summary(str(destination)) if not dry_run and skip_invalid else {}
        }
        
        if dry_run:
            # Just collect the operations for reporting
            for op in rename_operations[:10]:  # Show first 10
                action = "copied to" if copy_mode else "moved to"
                results['operations'].append({
                    'source': op['old_path'].name,
                    'destination': op['new_path'].relative_to(destination),
                    'action': action
                })
        else:
            # Perform actual rename operations
            results['processed_count'] = self._execute_rename_operations(
                rename_operations, copy_mode
            )
            
            # Save updated database (only if we moved files, not copied)
            if not copy_mode:
                # Remove problematic groups from manager before saving
                # since they've been moved to error folders and their paths are no longer valid
                if skip_invalid and problematic_groups:
                    for group, _, _ in problematic_groups:
                        manager.remove_group(group.basename)
                        self.logger.debug(f"Removed problematic group {group.basename} from database before saving")
                
                manager.save_to_json(database_path)
                results['database_updated'] = True
            else:
                results['database_updated'] = False
        
        self.logger.info("Photo rename process completed")
        return results
    
    def _validate_naming_scheme(self, scheme: str) -> None:
        """Validate that the naming scheme contains only valid placeholders."""
        import re
        
        # Extract all placeholders from the scheme
        placeholders = re.findall(r'\{([^}]+)\}', scheme)
        
        # Define valid placeholders
        valid_placeholders = {
            'date', 'datetime', 'year', 'month', 'day', 'hour', 'minute', 'second',
            'camera_make', 'camera_model', 'lens_model', 'serial_number',
            'iso', 'aperture', 'focal_length', 'shutter_speed',
            'basename', 'sequence'
        }
        
        # Check for invalid placeholders
        invalid_placeholders = set(placeholders) - valid_placeholders
        if invalid_placeholders:
            raise ValueError(f"Invalid placeholders: {', '.join(invalid_placeholders)}")
    
    def _generate_rename_operations(
        self, 
        groups: List, 
        destination: Path, 
        scheme: str
    ) -> List[Dict[str, Any]]:
        """Generate rename operations for all photos in the groups."""
        rename_operations = []
        
        for group in groups:
            # Extract metadata for the group
            group_metadata = group.extract_metadata()
            
            # Generate base filename ONCE per group (not per photo)
            base_filename = self._generate_base_filename(scheme, group, group_metadata)
            
            # Process each photo in the group
            for photo in group.get_photos():
                # Calculate paths using the SAME base filename for all photos in group
                old_path = photo.absolute_path
                name_parts = base_filename.split('/')
                
                if len(name_parts) > 1:
                    # Has subdirectories
                    subdir_path = Path(*name_parts[:-1])
                    filename = name_parts[-1]
                    base_new_path = destination / subdir_path / filename
                else:
                    # No subdirectories
                    base_new_path = destination / base_filename
                
                rename_operations.append({
                    'group': group,
                    'photo': photo,
                    'old_path': old_path,
                    'base_new_path': base_new_path,
                    'base_filename': base_filename,
                    'destination': destination,
                })
        
        return rename_operations
    
    def _generate_base_filename(self, scheme: str, group, group_metadata) -> str:
        """Generate the base filename using the scheme and metadata."""
        new_name = scheme
        
        # Metadata from the group
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
            # If no date_taken available, use the group basename as fallback
            # This should only happen for groups that don't require dates in the scheme
            replacements = {
                '{date}': group.basename,  # Use original basename as fallback
                '{datetime}': group.basename,
                '{year}': group.basename.split('_')[0] if '_' in group.basename else group.basename,
                '{month}': 'XX',
                '{day}': 'XX',
                '{hour}': 'XX',
                '{minute}': 'XX',
                '{second}': 'XX',
            }
        
        # Camera info replacements
        if camera:
            replacements.update({
                '{camera_make}': self._safe_filename(camera.make or 'UnknownMake'),
                '{camera_model}': self._safe_filename(camera.model or 'UnknownModel'),
                '{lens_model}': self._safe_filename(camera.lens_model or 'UnknownLens'),
                '{serial_number}': self._safe_filename(str(camera.serial_number) if camera.serial_number is not None else 'NoSerial'),
            })
        else:
            replacements.update({
                '{camera_make}': 'UnknownMake',
                '{camera_model}': 'UnknownModel',
                '{lens_model}': 'UnknownLens',
                '{serial_number}': 'NoSerial',
            })
        
        # Technical info replacements
        if technical:
            replacements.update({
                '{iso}': str(technical.iso or 'UnknownISO'),
                '{aperture}': f"f{technical.aperture}" if technical.aperture else 'UnknownAperture',
                '{focal_length}': f"{technical.focal_length}mm" if technical.focal_length else 'UnknownFocal',
                '{shutter_speed}': str(technical.shutter_speed or 'UnknownShutter'),
            })
        else:
            replacements.update({
                '{iso}': 'UnknownISO',
                '{aperture}': 'UnknownAperture',
                '{focal_length}': 'UnknownFocal',
                '{shutter_speed}': 'UnknownShutter',
            })
        
        # File info replacements
        replacements['{basename}'] = group.basename
        
        # Apply all replacements (skip sequence for now)
        for placeholder, value in replacements.items():
            new_name = new_name.replace(placeholder, str(value))
        
        # Clean up the filename
        if '/' in new_name:
            parts = new_name.split('/')
            clean_parts = [self._safe_filename(part) for part in parts]
            new_name = '/'.join(clean_parts)
        else:
            new_name = self._safe_filename(new_name)
        
        return new_name
    
    def _safe_filename(self, filename: str) -> str:
        """Make a string safe for use as a filename."""
        import re
        
        # Replace unsafe characters with underscores
        safe_name = re.sub(r'[<>:"|\\?*]', '_', filename)
        
        # Remove multiple consecutive underscores
        safe_name = re.sub(r'_+', '_', safe_name)
        
        # Remove leading/trailing underscores and spaces
        safe_name = safe_name.strip('_ ')
        
        return safe_name
    
    def _apply_sequences_to_operations(self, rename_operations: List[Dict], sequence_digits: int) -> None:
        """Apply sequence numbers to rename operations where needed."""
        # Check if any operation has {sequence} placeholder
        has_sequence_placeholder = any('{sequence}' in op['base_filename'] for op in rename_operations)
        
        if has_sequence_placeholder:
            self._apply_explicit_sequences(rename_operations, sequence_digits)
        else:
            self._apply_collision_sequences(rename_operations, sequence_digits)
    
    def _sort_groups_by_date_taken(self, group_operations: Dict[str, List[Dict]]) -> List[str]:
        """Sort group names by their earliest date taken (chronological order)."""
        group_dates = {}
        
        for group_name, operations in group_operations.items():
            # Find the earliest date taken among all photos in this group
            earliest_date = None
            for operation in operations:
                group = operation['group']
                # Extract metadata to get date_taken
                metadata = group.extract_metadata()
                if metadata.dates.date_taken:
                    if earliest_date is None or metadata.dates.date_taken < earliest_date:
                        earliest_date = metadata.dates.date_taken
            
            group_dates[group_name] = earliest_date
        
        # Sort by date taken (None dates go to the end)
        def sort_key(group_name):
            date = group_dates[group_name]
            return (date is None, date if date else datetime.min)
        
        return sorted(group_operations.keys(), key=sort_key)
    
    def _apply_explicit_sequences(self, rename_operations: List[Dict], sequence_digits: int) -> None:
        """Apply sequences for operations that have explicit {sequence} placeholders."""
        # Group operations by pattern and photo group
        pattern_to_groups = defaultdict(lambda: defaultdict(list))
        
        for operation in rename_operations:
            base_filename = operation['base_filename']
            original_group_basename = operation['group'].basename
            pattern_to_groups[base_filename][original_group_basename].append(operation)
        
        # Apply sequences to each pattern group
        for pattern, group_operations in pattern_to_groups.items():
            # Sort groups by date taken (chronological order)
            sorted_group_names = self._sort_groups_by_date_taken(group_operations)
            
            for seq_idx, group_name in enumerate(sorted_group_names, 1):
                operations = group_operations[group_name]
                sequence_str = f"{seq_idx:0{sequence_digits}d}"
                final_filename = pattern.replace('{sequence}', sequence_str)
                
                for operation in operations:
                    destination = operation['destination']
                    name_parts = final_filename.split('/')
                    
                    if len(name_parts) > 1:
                        subdir_path = Path(*name_parts[:-1])
                        filename = name_parts[-1]
                        final_path = destination / subdir_path / f"{filename}{operation['photo'].extension}"
                    else:
                        final_path = destination / f"{final_filename}{operation['photo'].extension}"
                    
                    operation['new_path'] = final_path
                    operation['new_dir'] = final_path.parent
    
    def _apply_collision_sequences(self, rename_operations: List[Dict], sequence_digits: int) -> None:
        """Apply sequences for operations that would collide."""
        # Group operations by base path and track original groups
        basename_to_groups = defaultdict(set)
        basename_to_operations = defaultdict(list)
        
        for operation in rename_operations:
            base_path = str(operation['base_new_path'])
            original_group_basename = operation['group'].basename
            
            basename_to_groups[base_path].add(original_group_basename)
            basename_to_operations[base_path].append(operation)
        
        # Identify conflicts
        conflicting_basenames = []
        for base_path, original_groups in basename_to_groups.items():
            if len(original_groups) > 1:
                conflicting_basenames.append(base_path)
        
        # Apply sequences
        for base_path, operations in basename_to_operations.items():
            if base_path in conflicting_basenames:
                # Group by original photo group and assign same sequence
                group_to_operations = defaultdict(list)
                for operation in operations:
                    original_group_basename = operation['group'].basename
                    group_to_operations[original_group_basename].append(operation)
                
                # Sort groups by date taken (chronological order)
                sorted_group_names = self._sort_groups_by_date_taken(group_to_operations)
                
                for seq_idx, group_name in enumerate(sorted_group_names, 1):
                    group_operations = group_to_operations[group_name]
                    
                    for operation in group_operations:
                        base_path_obj = operation['base_new_path']
                        extension = operation['photo'].extension
                        sequence_str = f"_{seq_idx:0{sequence_digits}d}"
                        final_path = Path(f"{base_path_obj}{sequence_str}{extension}")
                        
                        operation['new_path'] = final_path
                        operation['new_dir'] = final_path.parent
            else:
                # No conflicts - use as-is
                for operation in operations:
                    base_path_obj = operation['base_new_path']
                    extension = operation['photo'].extension
                    final_path = Path(f"{base_path_obj}{extension}")
                    
                    operation['new_path'] = final_path
                    operation['new_dir'] = final_path.parent
    
    def _execute_rename_operations(self, rename_operations: List[Dict], copy_mode: bool) -> int:
        """Execute the actual file rename/copy operations."""
        processed_count = 0
        action_verb = "Copying" if copy_mode else "Renaming"
        
        for op in rename_operations:
            try:
                # Debug: Check if operation has required keys
                if 'new_path' not in op or 'new_dir' not in op:
                    self.logger.error(f"Operation missing new_path or new_dir: {op.keys()}")
                    continue
                
                # Create directory if needed
                op['new_dir'].mkdir(parents=True, exist_ok=True)
                
                # Copy or move the file
                if copy_mode:
                    self.logger.info(f"Copying {op['old_path']} -> {op['new_path']}")
                    shutil.copy2(str(op['old_path']), str(op['new_path']))
                    self._add_copy_history(op['photo'], op['old_path'], op['new_path'])
                else:
                    self.logger.info(f"Moving {op['old_path']} -> {op['new_path']}")
                    shutil.move(str(op['old_path']), str(op['new_path']))
                    self._update_photo_with_history(op['photo'], op['old_path'], op['new_path'])
                
                processed_count += 1
                
                if processed_count % 100 == 0:
                    self.logger.info(f"{action_verb} {processed_count}/{len(rename_operations)} files...")
                    
            except Exception as e:
                self.logger.error(f"Failed to {action_verb.lower()} {op['old_path']} -> {op['new_path']}: {e}")
        
        return processed_count
    
    def _update_photo_with_history(self, photo, old_path: Path, new_path: Path) -> None:
        """Update photo object with new path and add history entry."""
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
    
    def _add_copy_history(self, photo, old_path: Path, new_path: Path) -> None:
        """Add copy history entry to photo object without updating the path."""
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
    
    def _write_uuid_to_file(self, file_path: Path, group_uuid: str, keywords: Optional[List[str]] = None, backup_xmp: bool = True) -> bool:
        """
        Write UUID and keywords to file metadata when possible.
        
        Args:
            file_path: Path to the file to write UUID to
            group_uuid: UUID of the photo group
            keywords: Optional list of keywords to write
            backup_xmp: If True, create backup copies of original XMP files
            
        Returns:
            True if UUID was written successfully, False otherwise
        """
        if keywords is None:
            keywords = []
        
        # Get file extension to determine if metadata writing is supported
        file_ext = file_path.suffix.lower()
        
        # Handle XMP files directly (don't try EXIF writing on them)
        if file_ext == '.xmp':
            if self._write_uuid_to_xmp_sidecar(file_path, group_uuid, keywords, backup_xmp):
                self.logger.info(f"Wrote UUID and keywords to XMP file: {file_path.name}")
                return True
            else:
                self.logger.info(f"Failed to write UUID and keywords to XMP file: {file_path.name}")
                return False
        
        # For image files, write to both EXIF (if supported) AND XMP sidecar for maximum compatibility
        exif_success = self._write_uuid_to_exif(file_path, group_uuid)
        xmp_success = self._write_uuid_to_xmp_sidecar(file_path, group_uuid, keywords, backup_xmp)
        
        # Log results
        if exif_success:
            self.logger.info(f"Wrote UUID to EXIF metadata: {file_path.name}")
        
        if xmp_success:
            self.logger.info(f"Wrote UUID to XMP sidecar file: {file_path.with_suffix('.xmp').name}")
        
        # Return success if either method worked
        if exif_success or xmp_success:
            return True
        
        # If neither works, just log and continue
        self.logger.info(f"UUID writing not supported for {file_ext} format: {file_path.name}")
        return False
    
    # UUID writing implementations
    def _write_uuid_to_exif(self, file_path: Path, group_uuid: str) -> bool:
        """Write UUID to EXIF metadata using safe merging."""
        return self.exif_merge_service.merge_uuid(file_path, group_uuid)
    
    def _write_uuid_to_xmp_sidecar(self, file_path: Path, group_uuid: str, keywords: Optional[List[str]] = None, backup_xmp: bool = True) -> bool:
        """Write UUID and keywords to XMP sidecar file, preserving existing metadata."""
        if keywords is None:
            keywords = []
        
        try:
            # Create XMP sidecar file path
            xmp_path = file_path.with_suffix('.xmp')
            
            if xmp_path.exists():
                # Create backup if requested
                if backup_xmp:
                    self._create_xmp_backup(xmp_path)
                
                # Parse and merge with existing XMP file
                return self._merge_uuid_into_existing_xmp(xmp_path, group_uuid, keywords)
            else:
                # Create new XMP file with UUID and keywords
                return self._create_new_xmp_with_uuid(xmp_path, group_uuid, keywords)
            
        except Exception as e:
            self.logger.debug(f"XMP UUID writing failed for {file_path}: {e}")
            return False
    
    def _merge_uuid_into_existing_xmp(self, xmp_path: Path, group_uuid: str, keywords: Optional[List[str]] = None) -> bool:
        """Merge UUID and keywords into existing XMP file without destroying existing metadata."""
        if keywords is None:
            keywords = []
        
        try:
            # Read existing XMP file
            with open(xmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the XML
            root = ET.fromstring(content)
            
            # Define namespace mappings
            namespaces = {
                'x': 'adobe:ns:meta/',
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'imgmaster': 'http://imgmaster.local/ns/'
            }
            
            # Register namespaces for ElementTree
            for prefix, uri in namespaces.items():
                ET.register_namespace(prefix, uri)
            
            # Find or create RDF element
            rdf_elem = root.find('.//rdf:RDF', namespaces)
            if rdf_elem is None:
                self.logger.debug(f"No RDF element found in {xmp_path}, creating new structure")
                return self._create_new_xmp_with_uuid(xmp_path, group_uuid, keywords)
            
            # Find existing Description element or create one
            desc_elem = rdf_elem.find('.//rdf:Description', namespaces)
            if desc_elem is None:
                # Create new Description element
                desc_elem = ET.SubElement(rdf_elem, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
                desc_elem.set('rdf:about', '')
            
            # Add or update imgmaster namespace attributes
            desc_elem.set('xmlns:imgmaster', 'http://imgmaster.local/ns/')
            desc_elem.set('{http://imgmaster.local/ns/}GroupUUID', group_uuid)
            desc_elem.set('{http://imgmaster.local/ns/}CreatedBy', 'imgmaster')
            desc_elem.set('{http://imgmaster.local/ns/}Version', '1.0')
            
            # Add keywords if provided
            if keywords:
                # Add Dublin Core namespace
                desc_elem.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
                
                # Find or create dc:subject element
                dc_subject = desc_elem.find('.//dc:subject', {'dc': 'http://purl.org/dc/elements/1.1/'})
                if dc_subject is None:
                    # Create RDF Bag structure for keywords
                    dc_subject = ET.SubElement(desc_elem, '{http://purl.org/dc/elements/1.1/}subject')
                    rdf_bag = ET.SubElement(dc_subject, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')
                    for keyword in keywords:
                        rdf_li = ET.SubElement(rdf_bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                        rdf_li.text = keyword
                else:
                    # Merge with existing keywords
                    rdf_bag = dc_subject.find('.//rdf:Bag', namespaces)
                    if rdf_bag is not None:
                        # Get existing keywords
                        existing_keywords = set()
                        for li in rdf_bag.findall('.//rdf:li', namespaces):
                            if li.text:
                                existing_keywords.add(li.text)
                        
                        # Add new keywords that don't already exist
                        for keyword in keywords:
                            if keyword not in existing_keywords:
                                rdf_li = ET.SubElement(rdf_bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                                rdf_li.text = keyword
            
            # Write back the modified XML
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            
            with open(xmp_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                tree.write(f, encoding='unicode', xml_declaration=False)
            
            self.logger.debug(f"Successfully merged UUID into existing XMP file: {xmp_path}")
            return True
            
        except ET.ParseError as e:
            self.logger.debug(f"Failed to parse existing XMP file {xmp_path}: {e}, creating new file")
            # If parsing fails, create a new file
            return self._create_new_xmp_with_uuid(xmp_path, group_uuid, keywords)
        except Exception as e:
            self.logger.debug(f"Failed to merge UUID into XMP file {xmp_path}: {e}")
            return False
    
    def _create_new_xmp_with_uuid(self, xmp_path: Path, group_uuid: str, keywords: Optional[List[str]] = None) -> bool:
        """Create a new XMP file with UUID and keyword metadata."""
        if keywords is None:
            keywords = []
        
        try:
            # Create XML structure
            root = ET.Element('{adobe:ns:meta/}xmpmeta')
            root.set('xmlns:x', 'adobe:ns:meta/')
            root.set('x:xmptk', 'imgmaster')
            
            # Create RDF element
            rdf_elem = ET.SubElement(root, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF')
            rdf_elem.set('xmlns:rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
            
            # Create Description element
            desc_elem = ET.SubElement(rdf_elem, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description')
            desc_elem.set('rdf:about', '')
            
            # Add imgmaster namespace attributes
            desc_elem.set('xmlns:imgmaster', 'http://imgmaster.local/ns/')
            desc_elem.set('{http://imgmaster.local/ns/}GroupUUID', group_uuid)
            desc_elem.set('{http://imgmaster.local/ns/}CreatedBy', 'imgmaster')
            desc_elem.set('{http://imgmaster.local/ns/}Version', '1.0')
            
            # Add keywords if provided
            if keywords:
                desc_elem.set('xmlns:dc', 'http://purl.org/dc/elements/1.1/')
                
                # Create dc:subject with RDF Bag
                dc_subject = ET.SubElement(desc_elem, '{http://purl.org/dc/elements/1.1/}subject')
                rdf_bag = ET.SubElement(dc_subject, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Bag')
                
                for keyword in keywords:
                    rdf_li = ET.SubElement(rdf_bag, '{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li')
                    rdf_li.text = keyword
            
            # Register namespaces for pretty output
            ET.register_namespace('x', 'adobe:ns:meta/')
            ET.register_namespace('rdf', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#')
            ET.register_namespace('imgmaster', 'http://imgmaster.local/ns/')
            if keywords:
                ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
            
            # Write the XML file
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ", level=0)  # Pretty print
            
            with open(xmp_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                tree.write(f, encoding='unicode', xml_declaration=False)
            
            self.logger.debug(f"Created new XMP file with UUID and {len(keywords)} keywords: {xmp_path}")
            return True
            
        except Exception as e:
            self.logger.debug(f"Failed to create new XMP file {xmp_path}: {e}")
            return False
    
    def _create_xmp_backup(self, xmp_path: Path) -> None:
        """Create a backup copy of an XMP file as filename_orig.xmp."""
        try:
            # Generate backup filename: filename_orig.xmp
            backup_path = xmp_path.with_name(f"{xmp_path.stem}_orig{xmp_path.suffix}")
            
            # Only create backup if it doesn't already exist
            if not backup_path.exists():
                shutil.copy2(str(xmp_path), str(backup_path))
                self.logger.debug(f"Created XMP backup: {backup_path.name}")
            else:
                self.logger.debug(f"XMP backup already exists: {backup_path.name}")
                
        except Exception as e:
            self.logger.warning(f"Failed to create XMP backup for {xmp_path.name}: {e}")
            # Don't raise exception - backup failure shouldn't stop the main operation
    
    def _classify_groups(self, all_groups: List) -> tuple[List, List]:
        """
        Classify groups into valid and problematic ones.
        
        Returns:
            Tuple of (valid_groups, problematic_groups)
        """
        valid_groups = []
        problematic_groups = []
        
        for group in all_groups:
            try:
                # Check if group has basic requirements
                if not group or not group.get_photos():
                    problematic_groups.append((group, ErrorType.INVALID_FILE, "Empty group or no photos"))
                    continue
                
                # Use the existing is_valid property to detect groups with only supplementary files
                if not group.is_valid:
                    problematic_groups.append((group, ErrorType.INVALID_FILE, "Group contains only sidecar/live photos"))
                    continue
                
                # Check if any photos in the group have missing files
                missing_files = [photo for photo in group.get_photos() 
                               if not hasattr(photo, 'absolute_path') or not photo.absolute_path or not photo.absolute_path.exists()]
                if missing_files:
                    problematic_groups.append((group, ErrorType.INVALID_FILE, f"Missing {len(missing_files)} file(s)"))
                    continue
                
                # Check if group has basic metadata extraction capability
                try:
                    group_metadata = group.extract_metadata()
                    if not group_metadata:
                        problematic_groups.append((group, ErrorType.MISSING_DATE, "No metadata available"))
                        continue
                except Exception as e:
                    error_type = self.error_handler.classify_error(group=group, exception=e)
                    problematic_groups.append((group, error_type, str(e)))
                    continue
                
                # Group passed basic checks
                valid_groups.append(group)
                
            except Exception as e:
                # Unexpected error with group
                error_type = self.error_handler.classify_error(group=group, exception=e)
                problematic_groups.append((group, error_type, f"Unexpected error: {str(e)}"))
        
        return valid_groups, problematic_groups
    
    def _group_has_required_metadata(self, group, scheme: str) -> bool:
        """
        Check if a group has the required metadata for the naming scheme.
        """
        try:
            # Check for date requirements in scheme
            date_placeholders = ['{date}', '{datetime}', '{year}', '{month}', '{day}', '{hour}', '{minute}', '{second}']
            needs_date = any(placeholder in scheme for placeholder in date_placeholders)
            
            if needs_date:
                # Only filter out if we explicitly need date metadata
                group_metadata = group.extract_metadata()
                dates = getattr(group_metadata, 'dates', None) if group_metadata else None
                if not dates or not dates.date_taken:
                    return False
            
            # For schemes that don't require dates, all groups are valid
            return True
            
        except Exception:
            # If we can't extract metadata, it's invalid
            return False
    
    def _handle_problematic_groups(self, problematic_groups: List[tuple], destination: Path) -> Dict[str, int]:
        """
        Handle problematic groups by moving them to appropriate error folders.
        
        Args:
            problematic_groups: List of (group, error_type, reason) tuples
            destination: Base destination directory
            
        Returns:
            Dictionary with error handling statistics
        """
        error_stats = defaultdict(int)
        
        for group, error_type, reason in problematic_groups:
            try:
                results = self.error_handler.handle_error_group(
                    group, error_type, str(destination), reason
                )
                
                # Count successful moves
                successful_moves = sum(1 for success in results.values() if success)
                error_stats[error_type.value] += successful_moves
                
                self.logger.info(f"Moved {successful_moves} files from group {group.basename} to {error_type.value} folder")
                
            except Exception as e:
                self.logger.error(f"Failed to handle problematic group {group.basename}: {e}")
                error_stats['failed_to_move'] += len(group.get_photos())
        
        return dict(error_stats)
    
    def _handle_problematic_groups_in_source(self, problematic_groups: List[tuple]) -> Dict[str, int]:
        """
        Handle problematic groups by moving them to appropriate error folders in their source directories.
        
        Args:
            problematic_groups: List of (group, error_type, reason) tuples
            
        Returns:
            Dictionary with error handling statistics
        """
        error_stats = defaultdict(int)
        
        # Group problematic groups by their source directory
        groups_by_source_dir = defaultdict(list)
        
        for group, error_type, reason in problematic_groups:
            try:
                # Find the source directory for this group (use the first photo's directory)
                if group.get_photos():
                    source_dir = str(group.get_photos()[0].absolute_path.parent)
                    groups_by_source_dir[source_dir].append((group, error_type, reason))
            except Exception as e:
                self.logger.error(f"Failed to determine source directory for group {group.basename}: {e}")
                error_stats['failed_to_move'] += len(group.get_photos()) if hasattr(group, 'get_photos') else 1
        
        # Handle each source directory separately
        for source_dir, dir_groups in groups_by_source_dir.items():
            for group, error_type, reason in dir_groups:
                try:
                    results = self.error_handler.handle_error_group(
                        group, error_type, source_dir, reason
                    )
                    
                    # Count successful moves
                    successful_moves = sum(1 for success in results.values() if success)
                    error_stats[error_type.value] += successful_moves
                    
                    self.logger.info(f"Moved {successful_moves} files from group {group.basename} to {error_type.value} folder in source directory")
                    
                except Exception as e:
                    self.logger.error(f"Failed to handle problematic group {group.basename}: {e}")
                    error_stats['failed_to_move'] += len(group.get_photos()) if hasattr(group, 'get_photos') else 1
        
        return dict(error_stats)
