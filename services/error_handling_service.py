"""Error handling service for managing files that cannot be processed."""

import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum

from models.photo import Photo
from models.photo_group import PhotoGroup


class ErrorType(Enum):
    """Types of errors that can occur during photo processing."""
    MISSING_DATE = "missing_date"
    INVALID_FILE = "invalid_file"
    CORRUPTED_FILE = "corrupted_file"
    PERMISSION_ERROR = "permission_error"
    UNSUPPORTED_FORMAT = "unsupported_format"


class ErrorHandlingService:
    """Service for handling files that cannot be processed normally."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.error_folders = {
            ErrorType.MISSING_DATE: "_ERROR_MISSING_DATE",
            ErrorType.INVALID_FILE: "_ERROR_INVALID",
            ErrorType.CORRUPTED_FILE: "_ERROR_CORRUPTED",
            ErrorType.PERMISSION_ERROR: "_ERROR_PERMISSION",
            ErrorType.UNSUPPORTED_FORMAT: "_ERROR_UNSUPPORTED"
        }
    
    def handle_error_photo(self, photo: Photo, error_type: ErrorType, 
                          base_directory: str, reason: str = "") -> bool:
        """
        Move a single photo to an appropriate error folder.
        
        Args:
            photo: The photo that cannot be processed
            error_type: The type of error encountered
            base_directory: The base directory for creating error folders
            reason: Optional additional reason for the error
            
        Returns:
            bool: True if the file was successfully moved, False otherwise
        """
        try:
            error_folder_name = self.error_folders[error_type]
            error_folder_path = os.path.join(base_directory, error_folder_name)
            
            # Create error folder if it doesn't exist
            os.makedirs(error_folder_path, exist_ok=True)
            
            # Determine destination filename (keep original name)
            original_filename = os.path.basename(photo.absolute_path)
            destination_path = os.path.join(error_folder_path, original_filename)
            
            # Handle filename conflicts
            counter = 1
            base_name, extension = os.path.splitext(original_filename)
            while os.path.exists(destination_path):
                new_filename = f"{base_name}_{counter}{extension}"
                destination_path = os.path.join(error_folder_path, new_filename)
                counter += 1
            
            # Move the file
            shutil.move(str(photo.absolute_path), destination_path)
            
            # Log the error and move
            log_message = f"Moved {original_filename} to {error_folder_name}"
            if reason:
                log_message += f" - Reason: {reason}"
            self.logger.info(log_message)
            
            # Create a log file in the error folder if it doesn't exist
            self._create_error_log(error_folder_path, photo, error_type, reason)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move {photo.absolute_path} to error folder: {e}")
            return False
    
    def handle_error_group(self, group: PhotoGroup, error_type: ErrorType, 
                          base_directory: str, reason: str = "") -> Dict[str, bool]:
        """
        Move all photos in a group to an appropriate error folder.
        
        Args:
            group: The photo group that cannot be processed
            error_type: The type of error encountered
            base_directory: The base directory for creating error folders
            reason: Optional additional reason for the error
            
        Returns:
            Dict[str, bool]: Mapping of photo filepath to success status
        """
        results = {}
        
        for photo in group.get_photos():
            success = self.handle_error_photo(photo, error_type, base_directory, reason)
            results[str(photo.absolute_path)] = success
        
        return results
    
    def classify_error(self, photo: Optional[Photo] = None, group: Optional[PhotoGroup] = None, 
                      exception: Optional[Exception] = None) -> ErrorType:
        """
        Classify the type of error based on the photo/group and exception.
        
        Args:
            photo: The photo that had an error (optional)
            group: The photo group that had an error (optional)
            exception: The exception that occurred (optional)
            
        Returns:
            ErrorType: The classified error type
        """
        # Check for permission errors
        if exception and isinstance(exception, PermissionError):
            return ErrorType.PERMISSION_ERROR
        
        # Check for missing date in group
        if group:
            try:
                metadata = group.extract_metadata()
                if not metadata.dates.date_taken:
                    return ErrorType.MISSING_DATE
            except Exception:
                pass  # Continue to other checks
        
        # Check for missing date in individual photo (if photo model has metadata)
        if photo:
            try:
                # Check if photo has a path that we can analyze
                if hasattr(photo, 'absolute_path') and not photo.absolute_path.exists():
                    return ErrorType.INVALID_FILE
            except Exception:
                pass  # Continue to other checks
        
        # Check for corrupted files (based on exception types)
        if exception and any(keyword in str(exception).lower() 
                           for keyword in ['corrupt', 'invalid', 'broken', 'damaged']):
            return ErrorType.CORRUPTED_FILE
        
        # Check for unsupported format
        if photo and hasattr(photo, 'absolute_path'):
            ext = photo.absolute_path.suffix.lower()
            if ext not in ['.jpg', '.jpeg', '.tiff', '.tif', '.png', '.raw', '.cr2', '.nef', '.arw']:
                return ErrorType.UNSUPPORTED_FORMAT
        
        # Default to invalid file
        return ErrorType.INVALID_FILE
    
    def _create_error_log(self, error_folder_path: str, photo: Photo, 
                         error_type: ErrorType, reason: str):
        """Create or append to an error log file in the error folder."""
        log_file_path = os.path.join(error_folder_path, "error_log.txt")
        
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"File: {os.path.basename(photo.absolute_path)}\n")
            f.write(f"Error Type: {error_type.value}\n")
            f.write(f"Original Path: {photo.absolute_path}\n")
            if reason:
                f.write(f"Reason: {reason}\n")
            f.write(f"Timestamp: {Path().cwd()}\n")  # Using current time implicitly
            f.write("-" * 50 + "\n")
    
    def get_error_summary(self, base_directory: str) -> Dict[str, int]:
        """
        Get a summary of files in each error folder.
        
        Args:
            base_directory: The base directory containing error folders
            
        Returns:
            Dict[str, int]: Mapping of error folder name to file count
        """
        summary = {}
        
        for error_type, folder_name in self.error_folders.items():
            folder_path = os.path.join(base_directory, folder_name)
            if os.path.exists(folder_path):
                file_count = len([f for f in os.listdir(folder_path) 
                                if os.path.isfile(os.path.join(folder_path, f)) 
                                and not f.startswith('.') and f != 'error_log.txt'])
                summary[folder_name] = file_count
            else:
                summary[folder_name] = 0
        
        return summary
