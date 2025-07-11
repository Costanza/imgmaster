import os
from pathlib import Path
from typing import Optional


class Photo:
    """
    Represents a photo image file on the filesystem.
    
    This model stores essential file information including the absolute path,
    basename, and extension for easy access and manipulation.
    """
    
    # JPEG formats
    JPEG_FORMATS = {'.jpg', '.jpeg'}
    
    # RAW formats organized by manufacturer
    RAW_FORMATS = {
        # Canon
        '.cr2', '.cr3', '.crw',
        # Nikon
        '.nef', '.nrw',
        # Sony
        '.arw', '.srf', '.sr2',
        # Fujifilm
        '.raf',
        # Olympus
        '.orf',
        # Panasonic
        '.rw2',
        # Pentax
        '.pef', '.ptx',
        # Leica
        '.rwl',
        # Kodak
        '.dcr', '.kdc',
        # Minolta
        '.mrw',
        # Samsung
        '.srw',
        # Hasselblad
        '.3fr',
        # Mamiya
        '.mef',
        # Phase One
        '.iiq',
        # Sigma
        '.x3f',
        # Adobe/Generic
        '.dng',
        # Generic RAW
        '.raw'
    }
    
    # Live Photo formats (Apple)
    LIVE_PHOTO_FORMATS = {'.mov'}
    
    # HEIC/HEIF formats (High Efficiency Image formats)
    HEIC_FORMATS = {'.heif', '.heic', '.hif'}
    
    # Sidecar/metadata files (accompanying image files)
    SIDECAR_FORMATS = {
        '.xmp',    # Adobe XMP metadata
        '.xml',    # Generic XML metadata
        '.thm',    # Thumbnail files (often from cameras)
        '.pp3',    # RawTherapee processing parameters
        '.dop',    # DxO Optics Pro settings
        '.pto',    # Hugin panorama project
        '.lrtemplate',  # Lightroom template
        '.xmp.xml',     # XMP in XML format
    }
    
    # Other standard photo formats
    OTHER_PHOTO_FORMATS = {
        '.png', '.gif', '.bmp', '.tiff', '.tif',
        '.webp', '.ico', '.svg'
    }
    
    @classmethod
    def get_all_supported_formats(cls) -> set[str]:
        """
        Get all supported image formats.
        
        Returns:
            A set containing all supported file extensions
        """
        return (cls.JPEG_FORMATS | cls.RAW_FORMATS | 
                cls.LIVE_PHOTO_FORMATS | cls.HEIC_FORMATS | 
                cls.SIDECAR_FORMATS | cls.OTHER_PHOTO_FORMATS)
    
    @classmethod
    def get_format_classification(cls, extension: str) -> str | None:
        """
        Get the classification of a file format.
        
        Args:
            extension: File extension (with or without leading dot)
            
        Returns:
            The format classification ('jpeg', 'raw', 'live_photo', 'heic', 'sidecar', 'other') 
            or None if not supported
        """
        # Normalize extension
        ext = extension.lower()
        if not ext.startswith('.'):
            ext = '.' + ext
        
        if ext in cls.JPEG_FORMATS:
            return 'jpeg'
        elif ext in cls.RAW_FORMATS:
            return 'raw'
        elif ext in cls.LIVE_PHOTO_FORMATS:
            return 'live_photo'
        elif ext in cls.HEIC_FORMATS:
            return 'heic'
        elif ext in cls.SIDECAR_FORMATS:
            return 'sidecar'
        elif ext in cls.OTHER_PHOTO_FORMATS:
            return 'other'
        else:
            return None
    
    def __init__(self, file_path: str | Path):
        """
        Initialize a Photo instance.
        
        Args:
            file_path: The path to the photo file (can be relative or absolute)
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            ValueError: If the file is not a valid image format
        """
        # Convert to Path object for easier manipulation
        path_obj = Path(file_path)
        
        # Store the absolute path
        self.absolute_path = path_obj.resolve()
        
        # Verify the file exists
        if not self.absolute_path.exists():
            raise FileNotFoundError(f"Photo file not found: {self.absolute_path}")
        
        # Store basename (filename without extension)
        self.basename = self.absolute_path.stem
        
        # Store extension (including the dot)
        self.extension = self.absolute_path.suffix.lower()
        
        # Store the full filename
        self.filename = self.absolute_path.name
        
        # Get format classification
        self.format_classification = self.get_format_classification(self.extension)
        
        # Initialize history tracking
        self.history = []
        
        # Validate it's an image file
        self._validate_image_format()
    
    def _validate_image_format(self) -> None:
        """
        Validate that the file has a supported image extension.
        
        Raises:
            ValueError: If the file extension is not a supported image format
        """
        if self.extension not in self.get_all_supported_formats():
            raise ValueError(
                f"Unsupported image format: {self.extension}. "
                f"Supported formats: {', '.join(sorted(self.get_all_supported_formats()))}"
            )
    
    @property
    def is_jpeg(self) -> bool:
        """Check if the photo is a JPEG format."""
        return self.extension in self.JPEG_FORMATS
    
    @property
    def is_raw(self) -> bool:
        """Check if the photo is a RAW format."""
        return self.extension in self.RAW_FORMATS
    
    @property
    def is_live_photo(self) -> bool:
        """Check if the photo is a Live Photo format."""
        return self.extension in self.LIVE_PHOTO_FORMATS
    
    @property
    def is_heic(self) -> bool:
        """Check if the photo is a HEIC/HEIF format."""
        return self.extension in self.HEIC_FORMATS
    
    @property
    def is_sidecar(self) -> bool:
        """Check if the file is a sidecar/metadata file."""
        return self.extension in self.SIDECAR_FORMATS
    
    @property
    def is_other_format(self) -> bool:
        """Check if the photo is another standard format (PNG, GIF, etc.)."""
        return self.extension in self.OTHER_PHOTO_FORMATS
    
    @property
    def size_bytes(self) -> int:
        """Get the file size in bytes."""
        return self.absolute_path.stat().st_size
    
    @property
    def size_mb(self) -> float:
        """Get the file size in megabytes, rounded to 2 decimal places."""
        return round(self.size_bytes / (1024 * 1024), 2)
    
    def exists(self) -> bool:
        """Check if the photo file still exists on the filesystem."""
        return self.absolute_path.exists()
    
    def __str__(self) -> str:
        """String representation of the Photo."""
        return f"Photo({self.filename})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the Photo."""
        return f"Photo(path='{self.absolute_path}', basename='{self.basename}', extension='{self.extension}')"
    
    def __eq__(self, other) -> bool:
        """Check equality based on absolute path."""
        if not isinstance(other, Photo):
            return False
        return self.absolute_path == other.absolute_path
    
    def __hash__(self) -> int:
        """Hash based on absolute path for use in sets and dicts."""
        return hash(self.absolute_path)
