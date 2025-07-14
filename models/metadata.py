"""
Metadata extraction utilities for photo files.

This module provides functionality to extract EXIF data from photos and 
parse XMP sidecar files to retrieve camera information, dates, and keywords/tags.
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
class KeywordInfo:
    """Keywords/tags extracted from metadata."""
    keywords: Optional[List[str]] = None
    
    def __post_init__(self):
        """Initialize keywords as empty list if None."""
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if keyword info is empty."""
        return not self.keywords or len(self.keywords) == 0


@dataclass
class KeywordInfoWithSource:
    """Keywords/tags with source file tracking."""
    keywords: Optional[List[str]] = None
    keywords_source: Optional[str] = None
    
    def __post_init__(self):
        """Initialize keywords as empty list if None."""
        if self.keywords is None:
            self.keywords = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def is_empty(self) -> bool:
        """Check if keyword info is empty."""
        return not self.keywords or len(self.keywords) == 0


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
    keywords: KeywordInfo
    source_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'camera': self.camera.to_dict(),
            'dates': self.dates.to_dict(),
            'technical': self.technical.to_dict(),
            'keywords': self.keywords.to_dict(),
            'source_file': self.source_file
        }
    
    def is_empty(self) -> bool:
        """Check if metadata is empty."""
        return self.camera.is_empty() and self.dates.is_empty() and self.technical.is_empty() and self.keywords.is_empty()


@dataclass
class PhotoMetadataWithSource:
    """Complete metadata for a photo group with source file tracking."""
    camera: CameraInfoWithSource
    dates: DateInfoWithSource
    technical: TechnicalInfoWithSource
    keywords: KeywordInfoWithSource
    source_file: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'camera': self.camera.to_dict(),
            'dates': self.dates.to_dict(),
            'technical': self.technical.to_dict(),
            'keywords': self.keywords.to_dict(),
            'source_file': self.source_file
        }
    
    def is_empty(self) -> bool:
        """Check if metadata is empty."""
        return self.camera.is_empty() and self.dates.is_empty() and self.technical.is_empty() and self.keywords.is_empty()


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
                keywords=KeywordInfo(),
                source_file=str(photo_path)
            )
        
        try:
            # For HEIC files and files that need keyword extraction, try exiftool first
            if photo_path.suffix.lower() in ['.heic', '.heif']:
                metadata = self._extract_with_exiftool(photo_path)
                if not metadata.is_empty():
                    return metadata
            
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
                keywords=KeywordInfo(),
                source_file=str(photo_path)
            )
    
    def _extract_with_pil(self, photo_path: Path) -> PhotoMetadata:
        """Extract metadata using PIL."""
        camera = CameraInfo()
        dates = DateInfo()
        technical = TechnicalInfo()
        keywords = KeywordInfo()
        
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
                        
                    # Keywords (from UserComment or XPKeywords)
                    user_comment = exif_data.get(37510)  # UserComment
                    if user_comment:
                        # Extract keywords from UserComment if available
                        keywords.keywords = [kw.strip() for kw in user_comment.split(',') if kw.strip()]
                    
                    if not keywords.keywords:
                        # Fallback to XPKeywords if UserComment does not exist or is empty
                        xp_keywords = exif_data.get(42034)  # XPKeywords
                        if xp_keywords:
                            keywords.keywords = [kw.strip() for kw in xp_keywords.split(';') if kw.strip()]
                        
        except Exception as e:
            self.logger.debug(f"PIL extraction failed for {photo_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            keywords=keywords,
            source_file=str(photo_path)
        )
    
    def _extract_with_exifread(self, photo_path: Path) -> PhotoMetadata:
        """Extract metadata using exifread."""
        camera = CameraInfo()
        dates = DateInfo()
        technical = TechnicalInfo()
        keywords = KeywordInfo()
        
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
                
                # Keywords (from UserComment or XPKeywords)
                user_comment = tags.get('EXIF UserComment')
                if user_comment:
                    try:
                        keywords.keywords = [kw.strip() for kw in user_comment.values[0].split(',') if kw.strip()]
                    except (AttributeError, ValueError, IndexError):
                        pass
                
                if not keywords.keywords:
                    # Fallback to XPKeywords if UserComment does not exist or is empty
                    xp_keywords = tags.get('EXIF XPKeywords')
                    if xp_keywords:
                        try:
                            keywords.keywords = [kw.strip() for kw in xp_keywords.values[0].split(';') if kw.strip()]
                        except (AttributeError, ValueError, IndexError):
                            pass
                        
        except Exception as e:
            self.logger.debug(f"exifread extraction failed for {photo_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            keywords=keywords,
            source_file=str(photo_path)
        )
    
    def _extract_with_exiftool(self, photo_path: Path) -> PhotoMetadata:
        """Extract metadata using exiftool, especially for HEIC files and keyword extraction."""
        import subprocess
        import json
        
        camera = CameraInfo()
        dates = DateInfo()
        technical = TechnicalInfo()
        keywords = KeywordInfo()
        
        try:
            # Run exiftool to extract metadata in JSON format
            cmd = [
                'exiftool', '-j', 
                '-Make', '-Model', '-LensModel', '-SerialNumber',  # Camera info
                '-DateTimeOriginal',  # Date info
                '-ISO', '-FNumber', '-ExposureTime', '-FocalLength', '-FocalLengthIn35mmFilm', '-Flash',  # Technical info
                '-Subject', '-Keywords', '-XMP:Subject', '-IPTC:Keywords', '-HierarchicalSubject', '-WeightedFlatSubject',  # Keywords
                str(photo_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            if result.stdout:
                data = json.loads(result.stdout)[0]
                
                # Camera info
                camera.make = data.get('Make')
                camera.model = data.get('Model')
                camera.lens_model = data.get('LensModel')
                camera.serial_number = data.get('SerialNumber')
                
                # Date info - ONLY use DateTimeOriginal
                date_str = data.get('DateTimeOriginal')
                if date_str:
                    try:
                        # Handle various date formats
                        if 'T' in date_str:
                            # ISO format like "2022-12-28T18:44:47+11:00"
                            dates.date_taken = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            # EXIF format like "2022:12:28 18:44:47"
                            dates.date_taken = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    except ValueError as e:
                        self.logger.debug(f"Failed to parse date {date_str}: {e}")
                
                # Technical info
                iso_val = data.get('ISO')
                if iso_val:
                    technical.iso = int(iso_val)
                
                fnumber = data.get('FNumber')
                if fnumber:
                    technical.aperture = float(fnumber)
                
                exposure_time = data.get('ExposureTime')
                if exposure_time:
                    technical.shutter_speed = str(exposure_time)
                
                focal_length = data.get('FocalLength')
                if focal_length:
                    try:
                        # Handle cases where focal length includes units (e.g., "9.0 mm")
                        if isinstance(focal_length, str):
                            # Extract just the numeric part
                            focal_length = focal_length.split()[0]
                        technical.focal_length = float(focal_length)
                    except (ValueError, IndexError):
                        pass
                
                focal_length_35mm = data.get('FocalLengthIn35mmFilm')
                if focal_length_35mm:
                    technical.focal_length_35mm = int(focal_length_35mm)
                
                flash_val = data.get('Flash')
                if flash_val:
                    technical.flash_fired = bool(flash_val & 1) if isinstance(flash_val, int) else 'fired' in str(flash_val).lower()
                
                # Keywords - extract from multiple possible fields
                keyword_list = []
                
                # Try different keyword fields
                for field in ['Subject', 'Keywords', 'XMP:Subject', 'IPTC:Keywords', 'HierarchicalSubject', 'WeightedFlatSubject']:
                    field_data = data.get(field)
                    if field_data:
                        if isinstance(field_data, list):
                            # Convert all items to strings and add to keyword list
                            keyword_list.extend([str(item) for item in field_data])
                        elif isinstance(field_data, str):
                            # Split by common delimiters
                            for delimiter in [';', ',']:
                                if delimiter in field_data:
                                    keyword_list.extend([kw.strip() for kw in field_data.split(delimiter) if kw.strip()])
                                    break
                            else:
                                keyword_list.append(field_data.strip())
                
                # Remove duplicates while preserving order
                if keyword_list:
                    keywords.keywords = list(dict.fromkeys(keyword_list))
                
        except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError) as e:
            self.logger.debug(f"exiftool extraction failed for {photo_path}: {e}")
        except Exception as e:
            self.logger.debug(f"Unexpected error in exiftool extraction for {photo_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            keywords=keywords,
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
        keywords = KeywordInfo()
        
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
                'aux': 'http://ns.adobe.com/exif/1.0/aux/',
                'dc': 'http://purl.org/dc/elements/1.1/'
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
            
            # Extract keywords (from dc:subject or xmp:Keywords)
            keywords_list = self._get_xmp_value(root, './/dc:subject', namespaces)
            if keywords_list:
                # Split by comma and strip whitespace
                keywords.keywords = [kw.strip() for kw in keywords_list.split(',') if kw.strip()]
            
            if not keywords.keywords:
                # Fallback to xmp:Keywords if dc:subject does not exist or is empty
                xmp_keywords = self._get_xmp_value(root, './/xmp:Keywords', namespaces)
                if xmp_keywords:
                    # Split by comma and strip whitespace
                    keywords.keywords = [kw.strip() for kw in xmp_keywords.split(',') if kw.strip()]
                    
        except Exception as e:
            self.logger.warning(f"Failed to extract XMP metadata from {xmp_path}: {e}")
        
        return PhotoMetadata(
            camera=camera,
            dates=dates,
            technical=technical,
            keywords=keywords,
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
