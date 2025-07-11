import json
import logging
from typing import Dict, List, Set, Optional
from collections import defaultdict
from pathlib import Path

from .photo import Photo


class PhotoGroup:
    """
    A group of photos that share the same base filename.
    
    This class manages collections of related files (e.g., RAW + JPEG, sidecar files)
    that have the same basename but different extensions.
    """
    
    def __init__(self, basename: str):
        """
        Initialize a PhotoGroup with a given basename.
        
        Args:
            basename: The base filename (without extension) for this group
        """
        self.basename = basename
        self._photos: Dict[str, Photo] = {}  # extension -> Photo mapping
        
    def add_photo(self, photo: Photo) -> None:
        """
        Add a photo to this group.
        
        Args:
            photo: The Photo instance to add
            
        Raises:
            ValueError: If the photo's basename doesn't match this group's basename
        """
        if photo.basename != self.basename:
            raise ValueError(
                f"Photo basename '{photo.basename}' doesn't match group basename '{self.basename}'"
            )
        
        self._photos[photo.extension] = photo
    
    def remove_photo(self, extension: str) -> Optional[Photo]:
        """
        Remove a photo with the given extension from this group.
        
        Args:
            extension: The file extension to remove (with or without leading dot)
            
        Returns:
            The removed Photo instance, or None if not found
        """
        # Normalize extension
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
            
        return self._photos.pop(ext, None)
    
    def get_photo(self, extension: str) -> Optional[Photo]:
        """
        Get a photo with the given extension from this group.
        
        Args:
            extension: The file extension to get (with or without leading dot)
            
        Returns:
            The Photo instance, or None if not found
        """
        # Normalize extension
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
            
        return self._photos.get(ext)
    
    def get_photos(self) -> List[Photo]:
        """
        Get all photos in this group.
        
        Returns:
            A list of all Photo instances in this group
        """
        return list(self._photos.values())
    
    def get_extensions(self) -> Set[str]:
        """
        Get all file extensions in this group.
        
        Returns:
            A set of all file extensions present in this group
        """
        return set(self._photos.keys())
    
    def has_extension(self, extension: str) -> bool:
        """
        Check if this group contains a photo with the given extension.
        
        Args:
            extension: The file extension to check (with or without leading dot)
            
        Returns:
            True if the extension exists in this group, False otherwise
        """
        # Normalize extension
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
            
        return ext in self._photos
    
    def has_format_type(self, format_type: str) -> bool:
        """
        Check if this group contains any photos of the given format type.
        
        Args:
            format_type: The format classification ('jpeg', 'raw', 'heic', etc.)
            
        Returns:
            True if any photo in the group matches the format type
        """
        return any(photo.format_classification == format_type for photo in self._photos.values())
    
    def get_photos_by_format(self, format_type: str) -> List[Photo]:
        """
        Get all photos in this group that match the given format type.
        
        Args:
            format_type: The format classification ('jpeg', 'raw', 'heic', etc.)
            
        Returns:
            A list of Photo instances matching the format type
        """
        return [photo for photo in self._photos.values() 
                if photo.format_classification == format_type]
    
    @property
    def count(self) -> int:
        """Get the number of photos in this group."""
        return len(self._photos)
    
    @property
    def is_empty(self) -> bool:
        """Check if this group is empty."""
        return len(self._photos) == 0
    
    @property
    def has_raw(self) -> bool:
        """Check if this group contains any RAW photos."""
        return self.has_format_type('raw')
    
    @property
    def has_jpeg(self) -> bool:
        """Check if this group contains any JPEG photos."""
        return self.has_format_type('jpeg')
    
    @property
    def has_sidecar(self) -> bool:
        """Check if this group contains any sidecar files."""
        return self.has_format_type('sidecar')
    
    @property
    def has_heic(self) -> bool:
        """Check if this group contains any HEIC photos."""
        return self.has_format_type('heic')
    
    @property
    def has_live_photo(self) -> bool:
        """Check if this group contains any Live Photos."""
        return self.has_format_type('live_photo')
    
    def __len__(self) -> int:
        """Return the number of photos in this group."""
        return len(self._photos)
    
    def __contains__(self, item) -> bool:
        """Check if a photo or extension is in this group."""
        if isinstance(item, Photo):
            return item.extension in self._photos and self._photos[item.extension] == item
        elif isinstance(item, str):
            return self.has_extension(item)
        return False
    
    def __iter__(self):
        """Iterate over all photos in this group."""
        return iter(self._photos.values())
    
    def __str__(self) -> str:
        """String representation of the PhotoGroup."""
        return f"PhotoGroup({self.basename}, {self.count} photos)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the PhotoGroup."""
        extensions = sorted(self._photos.keys())
        return f"PhotoGroup(basename='{self.basename}', extensions={extensions})"
    
    def __eq__(self, other) -> bool:
        """Check equality based on basename and contained photos."""
        if not isinstance(other, PhotoGroup):
            return False
        return self.basename == other.basename and self._photos == other._photos
    
    def __hash__(self) -> int:
        """Hash based on basename for use in sets and dicts."""
        return hash(self.basename)


class PhotoGroupManager:
    """
    Manages collections of PhotoGroup instances organized by basename.
    
    This class provides a high-level interface for organizing and accessing
    photos grouped by their base filenames.
    """
    
    def __init__(self):
        """Initialize an empty PhotoGroupManager."""
        self._groups: Dict[str, PhotoGroup] = {}
    
    def add_photo(self, photo: Photo) -> PhotoGroup:
        """
        Add a photo to the appropriate group based on its basename.
        
        Args:
            photo: The Photo instance to add
            
        Returns:
            The PhotoGroup that the photo was added to
        """
        basename = photo.basename
        
        if basename not in self._groups:
            self._groups[basename] = PhotoGroup(basename)
        
        self._groups[basename].add_photo(photo)
        return self._groups[basename]
    
    def add_photos(self, photos: List[Photo]) -> None:
        """
        Add multiple photos to their appropriate groups.
        
        Args:
            photos: List of Photo instances to add
        """
        for photo in photos:
            self.add_photo(photo)
    
    def get_group(self, basename: str) -> Optional[PhotoGroup]:
        """
        Get a photo group by basename.
        
        Args:
            basename: The base filename to look for
            
        Returns:
            The PhotoGroup instance, or None if not found
        """
        return self._groups.get(basename)
    
    def get_all_groups(self) -> List[PhotoGroup]:
        """
        Get all photo groups.
        
        Returns:
            A list of all PhotoGroup instances
        """
        return list(self._groups.values())
    
    def get_basenames(self) -> Set[str]:
        """
        Get all basenames that have groups.
        
        Returns:
            A set of all basenames
        """
        return set(self._groups.keys())
    
    def remove_group(self, basename: str) -> Optional[PhotoGroup]:
        """
        Remove a photo group by basename.
        
        Args:
            basename: The base filename group to remove
            
        Returns:
            The removed PhotoGroup instance, or None if not found
        """
        return self._groups.pop(basename, None)
    
    def get_groups_with_format(self, format_type: str) -> List[PhotoGroup]:
        """
        Get all groups that contain photos of the given format type.
        
        Args:
            format_type: The format classification ('jpeg', 'raw', 'heic', etc.)
            
        Returns:
            A list of PhotoGroup instances containing the format type
        """
        return [group for group in self._groups.values() 
                if group.has_format_type(format_type)]
    
    def get_groups_with_multiple_formats(self) -> List[PhotoGroup]:
        """
        Get all groups that contain multiple different file formats.
        
        Returns:
            A list of PhotoGroup instances with more than one photo
        """
        return [group for group in self._groups.values() if group.count > 1]
    
    @property
    def total_groups(self) -> int:
        """Get the total number of groups."""
        return len(self._groups)
    
    @property
    def total_photos(self) -> int:
        """Get the total number of photos across all groups."""
        return sum(group.count for group in self._groups.values())
    
    def __len__(self) -> int:
        """Return the number of groups."""
        return len(self._groups)
    
    def __contains__(self, basename: str) -> bool:
        """Check if a basename has a group."""
        return basename in self._groups
    
    def __iter__(self):
        """Iterate over all groups."""
        return iter(self._groups.values())
    
    def __getitem__(self, basename: str) -> PhotoGroup:
        """Get a group by basename using dictionary syntax."""
        return self._groups[basename]
    
    def __str__(self) -> str:
        """String representation of the PhotoGroupManager."""
        return f"PhotoGroupManager({self.total_groups} groups, {self.total_photos} photos)"
    
    def __repr__(self) -> str:
        """Detailed string representation of the PhotoGroupManager."""
        return f"PhotoGroupManager(groups={list(self._groups.keys())})"
    
    def scan_directory(self, directory_path: str | Path, recursive: bool = True) -> int:
        """
        Scan a directory for photo files and add them to groups.
        
        Args:
            directory_path: Path to the directory to scan
            recursive: Whether to scan subdirectories recursively
            
        Returns:
            The number of photos found and added
            
        Raises:
            FileNotFoundError: If the directory doesn't exist
            PermissionError: If the directory can't be accessed
        """
        logger = logging.getLogger(__name__)
        directory = Path(directory_path)
        
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        logger.info(f"Starting scan of directory: {directory}")
        logger.info(f"Recursive scan: {recursive}")
        
        photos_found = 0
        errors_encountered = 0
        supported_formats = Photo.get_all_supported_formats()
        
        # Choose the appropriate glob pattern
        pattern = "**/*" if recursive else "*"
        
        for file_path in directory.glob(pattern):
            if not file_path.is_file():
                continue
            
            # Check if the file extension is supported
            file_extension = file_path.suffix.lower()
            if file_extension not in supported_formats:
                continue
            
            try:
                photo = Photo(file_path)
                self.add_photo(photo)
                photos_found += 1
                
                if photos_found % 100 == 0:  # Log progress every 100 files
                    logger.info(f"Processed {photos_found} photos so far...")
                    
            except Exception as e:
                errors_encountered += 1
                logger.warning(f"Failed to process file {file_path}: {e}")
        
        logger.info(f"Scan completed. Found {photos_found} photos in {self.total_groups} groups")
        if errors_encountered > 0:
            logger.warning(f"Encountered {errors_encountered} errors during scan")
        
        return photos_found
    
    def to_dict(self) -> Dict:
        """
        Convert the PhotoGroupManager to a dictionary for JSON serialization.
        
        Returns:
            A dictionary representation of all groups and photos
        """
        result = {
            "metadata": {
                "total_groups": self.total_groups,
                "total_photos": self.total_photos,
                "created_by": "imgmaster",
                "version": "1.0"
            },
            "groups": {}
        }
        
        for basename, group in self._groups.items():
            group_data = {
                "basename": group.basename,
                "count": group.count,
                "formats": {
                    "jpeg": group.has_jpeg,
                    "raw": group.has_raw,
                    "heic": group.has_heic,
                    "live_photo": group.has_live_photo,
                    "sidecar": group.has_sidecar,
                    "other": group.has_other_format
                },
                "photos": []
            }
            
            for photo in group.get_photos():
                photo_data = {
                    "filename": photo.filename,
                    "basename": photo.basename,
                    "extension": photo.extension,
                    "absolute_path": str(photo.absolute_path),
                    "format_classification": photo.format_classification,
                    "size_bytes": photo.size_bytes,
                    "size_mb": photo.size_mb
                }
                group_data["photos"].append(photo_data)
            
            result["groups"][basename] = group_data
        
        return result
    
    def save_to_json(self, file_path: str | Path, indent: int = 2) -> None:
        """
        Save the PhotoGroupManager to a JSON file.
        
        Args:
            file_path: Path where to save the JSON file
            indent: Number of spaces for JSON indentation
            
        Raises:
            PermissionError: If the file cannot be written
            OSError: If there's an I/O error
        """
        logger = logging.getLogger(__name__)
        output_path = Path(file_path)
        
        logger.info(f"Saving photo database to: {output_path}")
        
        try:
            # Ensure the directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            data = self.to_dict()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            file_size = output_path.stat().st_size
            logger.info(f"Successfully saved database with {self.total_groups} groups and {self.total_photos} photos")
            logger.info(f"Output file size: {file_size:,} bytes ({file_size / 1024:.1f} KB)")
            
        except Exception as e:
            logger.error(f"Failed to save database to {output_path}: {e}")
            raise
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PhotoGroupManager':
        """
        Create a PhotoGroupManager from a dictionary (loaded from JSON).
        
        Args:
            data: Dictionary representation of the manager
            
        Returns:
            A new PhotoGroupManager instance
            
        Raises:
            KeyError: If required keys are missing from the data
            ValueError: If the data format is invalid
        """
        logger = logging.getLogger(__name__)
        
        if "groups" not in data:
            raise ValueError("Invalid data format: missing 'groups' key")
        
        manager = cls()
        
        for basename, group_data in data["groups"].items():
            if "photos" not in group_data:
                logger.warning(f"Skipping group {basename}: missing photos data")
                continue
            
            for photo_data in group_data["photos"]:
                try:
                    # Recreate Photo objects from saved data
                    photo_path = Path(photo_data["absolute_path"])
                    if photo_path.exists():
                        photo = Photo(photo_path)
                        manager.add_photo(photo)
                    else:
                        logger.warning(f"Photo file not found: {photo_path}")
                except Exception as e:
                    logger.warning(f"Failed to recreate photo from data: {e}")
        
        logger.info(f"Loaded {manager.total_groups} groups with {manager.total_photos} photos from saved data")
        return manager
    
    @classmethod
    def load_from_json(cls, file_path: str | Path) -> 'PhotoGroupManager':
        """
        Load a PhotoGroupManager from a JSON file.
        
        Args:
            file_path: Path to the JSON file to load
            
        Returns:
            A new PhotoGroupManager instance
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            json.JSONDecodeError: If the file is not valid JSON
            ValueError: If the data format is invalid
        """
        logger = logging.getLogger(__name__)
        input_path = Path(file_path)
        
        logger.info(f"Loading photo database from: {input_path}")
        
        if not input_path.exists():
            raise FileNotFoundError(f"Database file not found: {input_path}")
        
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            manager = cls.from_dict(data)
            logger.info(f"Successfully loaded database from {input_path}")
            return manager
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in file {input_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load database from {input_path}: {e}")
            raise
