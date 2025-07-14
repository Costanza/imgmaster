"""Service for safely merging new EXIF data (e.g., UUID) into image files."""

import piexif
import subprocess
from pathlib import Path
import logging

class ExifMergeService:
    """Service for merging EXIF data into JPEG, RAW, and HEIC files without overwriting existing metadata."""
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def merge_uuid_into_jpeg(self, file_path: Path, uuid: str) -> bool:
        """Merge UUID into JPEG EXIF metadata using piexif."""
        try:
            exif_dict = piexif.load(str(file_path))
            # Use the 'Exif' IFD for custom tags, or '0th' for user comments
            # We'll use the UserComment tag (37510) in Exif IFD for UUID
            user_comment_tag = piexif.ExifIFD.UserComment
            comment = f"UUID:{uuid}".encode('utf-8')
            exif_dict['Exif'][user_comment_tag] = comment
            exif_bytes = piexif.dump(exif_dict)
            piexif.insert(exif_bytes, str(file_path))
            return True
        except Exception as e:
            self.logger.error(f"Failed to merge UUID into JPEG EXIF: {e}")
            return False

    def merge_uuid_into_raw_or_heic(self, file_path: Path, uuid: str) -> bool:
        """Merge UUID into RAW or HEIC EXIF metadata using exiftool (must be installed)."""
        try:
            # Use a custom tag or comment field for UUID
            # Example: set XMP:ImageUniqueID or EXIF:ImageUniqueID
            result = subprocess.run([
                "exiftool",
                "-overwrite_original",
                f"-XMP:ImageUniqueID={uuid}",
                str(file_path)
            ], capture_output=True, text=True)
            if result.returncode == 0:
                return True
            else:
                self.logger.error(f"ExifTool error: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to merge UUID into RAW/HEIC EXIF: {e}")
            return False

    def merge_uuid(self, file_path: Path, uuid: str) -> bool:
        """Dispatch to the correct merge method based on file extension."""
        ext = file_path.suffix.lower()
        if ext in {'.jpg', '.jpeg'}:
            return self.merge_uuid_into_jpeg(file_path, uuid)
        elif ext in {'.cr2', '.nef', '.arw', '.dng', '.rw2', '.orf', '.raf', '.pef', '.srw', '.heic', '.heif'}:
            return self.merge_uuid_into_raw_or_heic(file_path, uuid)
        else:
            self.logger.debug(f"EXIF UUID merge not supported for format: {ext} (file: {file_path.name})")
            return False
