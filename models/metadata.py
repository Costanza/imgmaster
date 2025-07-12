"""
Metadata extraction utilities for photo files.

This module provides functionality to extract EXIF data from photos and 
parse XMP sidecar files to retrieve camera information and dates.
"""

import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict
import json

try:
    import exifread
    from PIL import Image
    from PIL.ExifTags import TAGS
    EXIF_AVAILABLE = True
except ImportError:
    EXIF_AVAILABLE = False
    logging.warning("EXIF libraries not available. Install with: pip install exifread pillow")


@dataclass
class CameraInfo:
    """Camera information extracted from metadata."""
    make: Optional[str] = None
    model: Optional[str] = None
    lens_model: Optional[str] = None
    serial_number: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if camera info is empty."""
        return not any([self.make, self.model, self.lens_model, self.serial_number])


@dataclass
class CameraInfoWithSource:
    """Camera information with source file tracking."""
    make: Optional[str] = None
    make_source: Optional[str] = None
    model: Optional[str] = None
    model_source: Optional[str] = None
    lens_model: Optional[str] = None
    lens_model_source: Optional[str] = None
    serial_number: Optional[str] = None
    serial_number_source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if camera info is empty."""
        return not any([self.make, self.model, self.lens_model, self.serial_number])


@dataclass
class DateInfo:
    """Date information extracted from metadata."""
    date_taken: Optional[datetime] = None
    date_modified: Optional[datetime] = None
    date_digitized: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        if self.date_taken:
            result['date_taken'] = self.date_taken.isoformat()
        if self.date_modified:
            result['date_modified'] = self.date_modified.isoformat()
        if self.date_digitized:
            result['date_digitized'] = self.date_digitized.isoformat()
        return result
    
    def is_empty(self) -> bool:
        """Check if date info is empty."""
        return not any([self.date_taken, self.date_modified, self.date_digitized])


@dataclass
class DateInfoWithSource:
    """Date information with source file tracking."""
    date_taken: Optional[datetime] = None
    date_taken_source: Optional[str] = None
    date_modified: Optional[datetime] = None
    date_modified_source: Optional[str] = None
    date_digitized: Optional[datetime] = None
    date_digitized_source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        if self.date_taken:
            result['date_taken'] = self.date_taken.isoformat()
            if self.date_taken_source:
                result['date_taken_source'] = self.date_taken_source
        if self.date_modified:
            result['date_modified'] = self.date_modified.isoformat()
            if self.date_modified_source:
                result['date_modified_source'] = self.date_modified_source
        if self.date_digitized:
            result['date_digitized'] = self.date_digitized.isoformat()
            if self.date_digitized_source:
                result['date_digitized_source'] = self.date_digitized_source
        return result
    
    def is_empty(self) -> bool:
        """Check if date info is empty."""
        return not any([self.date_taken, self.date_modified, self.date_digitized])


@dataclass
class TechnicalInfo:
    """Technical camera settings extracted from metadata."""
    iso: Optional[int] = None
    aperture: Optional[float] = None
    shutter_speed: Optional[str] = None
    focal_length: Optional[float] = None
    focal_length_35mm: Optional[int] = None
    flash_fired: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if technical info is empty."""
        return not any([
            self.iso, self.aperture, self.shutter_speed, 
            self.focal_length, self.focal_length_35mm, self.flash_fired
        ])


@dataclass
class TechnicalInfoWithSource:
    """Technical camera settings with source file tracking."""
    iso: Optional[int] = None
    iso_source: Optional[str] = None
    aperture: Optional[float] = None
    aperture_source: Optional[str] = None
    shutter_speed: Optional[str] = None
    shutter_speed_source: Optional[str] = None
    focal_length: Optional[float] = None
    focal_length_source: Optional[str] = None
    focal_length_35mm: Optional[int] = None
    focal_length_35mm_source: Optional[str] = None
    flash_fired: Optional[bool] = None
    flash_fired_source: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if technical info is empty."""
        return not any([
            self.iso, self.aperture, self.shutter_speed, 
            self.focal_length, self.focal_length_35mm, self.flash_fired
        ])


@dataclass
class PhotoMetadata:
    """Complete metadata for a photo."""
    camera: CameraInfo
    dates: DateInfo
    technical: TechnicalInfo
    source_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'camera': self.camera.to_dict(),
            'dates': self.dates.to_dict(),
            'technical': self.technical.to_dict(),
            'source_file': self.source_file
        }
    
    def is_empty(self) -> bool:
        """Check if metadata is empty."""
        return self.camera.is_empty() and self.dates.is_empty() and self.technical.is_empty()


@dataclass
class PhotoMetadataWithSource:
    """Complete metadata for a photo group with source file tracking."""
    camera: CameraInfoWithSource
    dates: DateInfoWithSource
    technical: TechnicalInfoWithSource
    source_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'camera': self.camera.to_dict(),
            'dates': self.dates.to_dict(),
            'technical': self.technical.to_dict(),
            'source_file': self.source_file
        }
    
    def is_empty(self) -> bool:
        """Check if metadata is empty."""
        return self.camera.is_empty() and self.dates.is_empty() and self.technical.is_empty()


class MetadataExtractor:
    """Extract metadata from photo files and sidecar files."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def extract_from_photo(self, photo_path: Path) -> PhotoMetadata:
        """
        Extract metadata from a photo file using EXIF data.
        
        Args:
            photo_path: Path to the photo file
            
        Returns:
            PhotoMetadata object with extracted information
        """
        if not EXIF_AVAILABLE:
            self.logger.warning("EXIF libraries not available - cannot extract metadata")
            return PhotoMetadata(
                camera=CameraInfo(),
                dates=DateInfo(),
                technical=TechnicalInfo(),
                source_file=str(photo_path)
            )
        
        try:
            # Try PIL first (works well with JPEG, TIFF)
            metadata = self._extract_with_pil(photo_path)
            if not metadata.is_empty():
                return metadata
            
            # Fallback to exifread (works with RAW files)
            metadata = self._extract_with_exifread(photo_path)
            metadata.source_file = str(photo_path)
            return metadata
            
        except Exception as e:
            self.logger.warning(f"Failed to extract metadata from {photo_path}: {e}")
            return PhotoMetadata(
                camera=CameraInfo(),
                dates=DateInfo(),
                technical=TechnicalInfo(),
                source_file=str(photo_path)
            )
    
    def _extract_with_pil(self, photo_path: Path) -> PhotoMetadata:
        """Extract metadata using PIL."""
        camera = CameraInfo()
        dates = DateInfo()
        technical = TechnicalInfo()
        
        try:
            with Image.open(photo_path) as img:
                exif_data = img._getexif()
                
                if exif_data:
                    # Camera info
                    camera.make = exif_data.get(271)  # Make
                    camera.model = exif_data.get(272)  # Model
                    camera.lens_model = exif_data.get(42036)  # LensModel
                    camera.serial_number = exif_data.get(42033)  # SerialNumber
                    
                    # Date info - ONLY use DateTimeOriginal, never DateTime (modification date)
                    date_str = exif_data.get(36868)  # DateTimeOriginal ONLY
                    if date_str:
                        try:
                            dates.date_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                        except ValueError:
                            pass
                    
                    # Technical info
                    technical.iso = exif_data.get(34855)  # ISOSpeedRatings
                    
                    # Aperture
                    fnumber = exif_data.get(33437)  # FNumber
                    if fnumber and hasattr(fnumber, 'num') and hasattr(fnumber, 'den'):
                        technical.aperture = float(fnumber.num) / float(fnumber.den)
                    
                    # Focal length
                    focal_len = exif_data.get(37386)  # FocalLength
                    if focal_len and hasattr(focal_len, 'num') and hasattr(focal_len, 'den'):
                        technical.focal_length = float(focal_len.num) / float(focal_len.den)
                    
                    technical.focal_length_35mm = exif_data.get(41989)  # FocalLengthIn35mmFilm
                    
                    # Flash
                    flash_data = exif_data.get(37385)  # Flash
                    if flash_data is not None:
                        technical.flash_fired = bool(flash_data & 1)
                        
        except Exception as e:
            self.logger.debug(f"PIL extraction failed for {photo_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            source_file=str(photo_path)
        )
    
    def _extract_with_exifread(self, photo_path: Path) -> PhotoMetadata:
        """Extract metadata using exifread."""
        camera = CameraInfo()
        dates = DateInfo()
        technical = TechnicalInfo()
        
        try:
            with open(photo_path, 'rb') as f:
                tags = exifread.process_file(f, details=False)
                
                # Camera info
                camera.make = str(tags.get('Image Make', '')).strip() or None
                camera.model = str(tags.get('Image Model', '')).strip() or None
                camera.lens_model = str(tags.get('EXIF LensModel', '')).strip() or None
                camera.serial_number = str(tags.get('EXIF BodySerialNumber', '')).strip() or None
                
                # Date info - ONLY use DateTimeOriginal, never DateTime (modification date)
                date_str = str(tags.get('EXIF DateTimeOriginal', ''))
                if date_str and date_str != '':
                    try:
                        dates.date_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        pass
                
                # Technical info
                iso_str = str(tags.get('EXIF ISOSpeedRatings', ''))
                if iso_str and iso_str.isdigit():
                    technical.iso = int(iso_str)
                
                # Aperture
                fnumber = tags.get('EXIF FNumber')
                if fnumber:
                    try:
                        technical.aperture = float(fnumber.values[0])
                    except (AttributeError, ValueError, IndexError):
                        pass
                
                # Shutter speed
                exposure_time = tags.get('EXIF ExposureTime')
                if exposure_time:
                    technical.shutter_speed = str(exposure_time)
                
                # Focal length
                focal_len = tags.get('EXIF FocalLength')
                if focal_len:
                    try:
                        technical.focal_length = float(focal_len.values[0])
                    except (AttributeError, ValueError, IndexError):
                        pass
                
                # Flash
                flash_data = tags.get('EXIF Flash')
                if flash_data:
                    try:
                        flash_val = flash_data.values[0]
                        technical.flash_fired = bool(flash_val & 1)
                    except (AttributeError, ValueError, IndexError):
                        pass
                        
        except Exception as e:
            self.logger.debug(f"exifread extraction failed for {photo_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            source_file=str(photo_path)
        )
    
    def extract_from_xmp(self, xmp_path: Path) -> PhotoMetadata:
        """
        Extract metadata from an XMP sidecar file.
        
        Args:
            xmp_path: Path to the XMP file
            
        Returns:
            PhotoMetadata object with extracted information
        """
        camera = CameraInfo()
        dates = DateInfo()
        technical = TechnicalInfo()
        
        try:
            with open(xmp_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse XML
            root = ET.fromstring(content)
            
            # Define namespaces
            namespaces = {
                'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                'exif': 'http://ns.adobe.com/exif/1.0/',
                'tiff': 'http://ns.adobe.com/tiff/1.0/',
                'xmp': 'http://ns.adobe.com/xap/1.0/',
                'aux': 'http://ns.adobe.com/exif/1.0/aux/'
            }
            
            # Extract camera info
            camera.make = self._get_xmp_value(root, './/tiff:Make', namespaces)
            camera.model = self._get_xmp_value(root, './/tiff:Model', namespaces)
            camera.lens_model = self._get_xmp_value(root, './/aux:Lens', namespaces)
            camera.serial_number = self._get_xmp_value(root, './/aux:SerialNumber', namespaces)
            
            # Extract date info
            date_str = self._get_xmp_value(root, './/exif:DateTimeOriginal', namespaces)
            if date_str:
                try:
                    # XMP dates are usually in ISO format
                    dates.date_taken = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                except ValueError:
                    try:
                        # Try EXIF format
                        dates.date_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError:
                        pass
            
            # Extract technical info
            iso_str = self._get_xmp_value(root, './/exif:ISOSpeedRatings', namespaces)
            if iso_str and iso_str.isdigit():
                technical.iso = int(iso_str)
            
            aperture_str = self._get_xmp_value(root, './/exif:FNumber', namespaces)
            if aperture_str:
                try:
                    technical.aperture = float(aperture_str)
                except ValueError:
                    pass
            
            technical.shutter_speed = self._get_xmp_value(root, './/exif:ExposureTime', namespaces)
            
            focal_len_str = self._get_xmp_value(root, './/exif:FocalLength', namespaces)
            if focal_len_str:
                try:
                    technical.focal_length = float(focal_len_str)
                except ValueError:
                    pass
                    
        except Exception as e:
            self.logger.warning(f"Failed to extract XMP metadata from {xmp_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            source_file=str(xmp_path)
        )
    
    def _get_xmp_value(self, root: ET.Element, xpath: str, namespaces: Dict[str, str]) -> Optional[str]:
        """Extract a value from XMP using XPath."""
        try:
            element = root.find(xpath, namespaces)
            if element is not None:
                return element.text
        except Exception:
            pass
        return None
