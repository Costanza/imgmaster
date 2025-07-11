"""Photo renaming service for file operations."""

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict

from models import PhotoGroupManager
from repositories import PhotoGroupRepository, JsonFilePhotoGroupRepository


class PhotoRenameService:
    """Service for renaming and organizing photo files."""
    
    def __init__(self, repository: PhotoGroupRepository = None):
        self.logger = logging.getLogger(__name__)
        self.repository = repository or JsonFilePhotoGroupRepository()
    
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
        
        # Determine which groups to process
        if skip_invalid:
            groups_to_process = manager.get_valid_groups()
            invalid_groups_count = manager.total_invalid_groups
        else:
            groups_to_process = manager.get_all_groups()
            invalid_groups_count = 0
        
        # Generate rename operations
        rename_operations = self._generate_rename_operations(
            groups_to_process, destination, scheme
        )
        
        # Apply sequence numbers to handle collisions
        self._apply_sequences_to_operations(rename_operations, sequence_digits)
        
        # Build results
        results = {
            'total_groups_processed': len(groups_to_process),
            'invalid_groups_skipped': invalid_groups_count,
            'total_files': len(rename_operations),
            'dry_run': dry_run,
            'copy_mode': copy_mode,
            'destination': str(destination),
            'operations': []
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
            
            # Process each photo in the group
            for photo in group.get_photos():
                # Generate new name based on scheme and metadata
                new_name = self._generate_base_filename(scheme, photo, group_metadata)
                
                # Calculate paths
                old_path = photo.absolute_path
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
                    'base_new_path': base_new_path,
                    'base_filename': new_name,
                    'destination': destination,
                })
        
        return rename_operations
    
    def _generate_base_filename(self, scheme: str, photo, group_metadata) -> str:
        """Generate the base filename using the scheme and metadata."""
        new_name = scheme
        
        # File modification time as fallback
        mtime = datetime.fromtimestamp(photo.absolute_path.stat().st_mtime)
        
        # Basic metadata
        basic = group_metadata.basic if hasattr(group_metadata, 'basic') else None
        camera = group_metadata.camera if hasattr(group_metadata, 'camera') else None
        technical = group_metadata.technical if hasattr(group_metadata, 'technical') else None
        
        # Date/time replacements
        if basic and basic.date_taken:
            dt = basic.date_taken
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
            # Fallback to file modification time
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
                '{camera_make}': self._safe_filename(camera.make or 'Unknown'),
                '{camera_model}': self._safe_filename(camera.model or 'Unknown'),
                '{lens_model}': self._safe_filename(camera.lens_model or 'Unknown'),
                '{serial_number}': self._safe_filename(camera.serial_number or 'Unknown'),
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
            sorted_group_names = sorted(group_operations.keys())
            
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
                
                sorted_group_names = sorted(group_to_operations.keys())
                
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
                # Create directory if needed
                op['new_dir'].mkdir(parents=True, exist_ok=True)
                
                # Copy or move the file
                if copy_mode:
                    shutil.copy2(str(op['old_path']), str(op['new_path']))
                    self._add_copy_history(op['photo'], op['old_path'], op['new_path'])
                else:
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
