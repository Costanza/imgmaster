# ImgMaster

**Simple, opinionated, photo library file manipulation**

ImgMaster is a powerful CLI tool designed to help photographers organize and rename their photo libraries based on metadata and intelligent grouping. It provides a clean, service-oriented architecture for processing large photo collections efficiently.

## Features

🔍 **Smart Photo Grouping**
- Groups photos by basename (e.g., `IMG_001.jpg`, `IMG_001.cr2`, `IMG_001.xmp`)
- Supports RAW, JPEG, and sidecar file relationships
- Handles live photos and burst sequences

📋 **Metadata-Driven Renaming**
- Extract and use EXIF/XMP metadata for intelligent file naming
- Support for date/time, camera info, technical settings
- Flexible naming scheme with placeholders
- Automatic sequence numbering for duplicates

🎯 **Opinionated Workflow**
- Two-step process: build database, then rename
- Validation before file operations
- Dry-run mode for safe testing
- Copy or move operations

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd imgmaster

# Install dependencies with uv (recommended)
uv install

# Or install with pip
pip install -e .
```

## Quick Start

### 1. Build a Photo Database

First, scan your photo directory to create a database of photo groups:

```bash
uv run python main.py build /path/to/photos --output photo_database.json
```

This will:
- Recursively scan the directory for supported photo formats
- Group files by basename
- Extract metadata from photos
- Save the database to JSON for the next step

### 2. Rename Photos

Use the database to rename and organize your photos:

```bash
uv run python main.py rename photo_database.json /path/to/destination \
  --scheme "{date}_{camera_model}_{sequence}"
```

## Usage

### Build Command

```bash
uv run python main.py build [OPTIONS] DIRECTORY

Options:
  -o, --output PATH             Output JSON file path (default: photo_database.json)
  --recursive / --no-recursive  Scan directories recursively (default: True)
  -v, --verbose                 Enable verbose logging
  --help                        Show help message
```

**Examples:**
```bash
# Basic scan
uv run python main.py build ~/Pictures/Import

# Non-recursive scan with custom output
uv run python main.py build ~/Pictures/Import --no-recursive -o my_photos.json

# Verbose mode for troubleshooting
uv run python main.py build ~/Pictures/Import --verbose
```

### Rename Command

```bash
uv run python main.py rename [OPTIONS] DATABASE DESTINATION

Options:
  -s, --scheme TEXT             Naming scheme with metadata placeholders [required]
  --sequence-digits INTEGER     Number of digits for sequence numbers (1-6, default: 3)
  --dry-run                     Show what would be renamed without actually renaming
  --copy                        Copy files instead of moving them
  --skip-invalid / --include-invalid  Skip invalid photo groups (default: skip)
  -v, --verbose                 Enable verbose logging
  --help                        Show help message
```

**Examples:**
```bash
# Basic rename with date and camera
uv run python main.py rename photos.json ~/Pictures/Organized \
  --scheme "{date}_{camera_model}_{basename}"

# Test with dry-run first
uv run python main.py rename photos.json ~/Pictures/Organized \
  --scheme "{datetime}_{iso}_{aperture}" --dry-run

# Copy instead of move (safer for testing)
uv run python main.py rename photos.json ~/Pictures/Organized \
  --scheme "{year}/{month}/{date}_{sequence}" --copy

# Include technical metadata
uv run python main.py rename photos.json ~/Pictures/Organized \
  --scheme "{year}/{camera_make}/{date}_{focal_length}mm_{sequence}"
```

## Naming Scheme Placeholders

### Date/Time
- `{date}` - Date in YYYY-MM-DD format
- `{datetime}` - Date and time in YYYY-MM-DD_HH-MM-SS format
- `{year}` - 4-digit year
- `{month}` - 2-digit month  
- `{day}` - 2-digit day
- `{hour}` - 2-digit hour (24h format)
- `{minute}` - 2-digit minute
- `{second}` - 2-digit second

### Camera Info
- `{camera_make}` - Camera manufacturer (e.g., "Canon", "Nikon")
- `{camera_model}` - Camera model (e.g., "EOS R5", "D850")
- `{lens_model}` - Lens model
- `{serial_number}` - Camera serial number

### Technical Settings
- `{iso}` - ISO value (e.g., "100", "1600")
- `{aperture}` - Aperture f-stop (e.g., "2.8", "5.6")
- `{focal_length}` - Focal length in mm
- `{shutter_speed}` - Shutter speed

### File Info
- `{basename}` - Original file basename (without extension)
- `{sequence}` - Auto-generated sequence number for duplicates

## Example Workflows

### Organizing by Date and Camera
```bash
# Create date-based folder structure
uv run python main.py rename photos.json ~/Pictures/Organized \
  --scheme "{year}/{month}/{date}_{camera_model}_{sequence}"

# Result: 2024/03/2024-03-15_Canon_EOS_R5_001.jpg
```

### Technical Photography Organization
```bash
# Group by technical settings
uv run python main.py rename photos.json ~/Pictures/Technical \
  --scheme "{camera_make}/{lens_model}/{iso}_{aperture}_{focal_length}mm_{sequence}"

# Result: Canon/RF24-70mm_F2.8_L_IS_USM/400_2.8_50mm_001.cr2
```

### Event-Based Organization
```bash
# Organize by date with original names preserved
uv run python main.py rename photos.json ~/Pictures/Events \
  --scheme "{date}_{basename}"

# Result: 2024-03-15_IMG_001.jpg
```

## Supported File Formats

### RAW Formats
- Canon: `.cr2`, `.cr3`
- Nikon: `.nef`
- Sony: `.arw`
- Fujifilm: `.raf`
- And many more...

### Standard Formats
- JPEG: `.jpg`, `.jpeg`
- TIFF: `.tif`, `.tiff`
- PNG: `.png`

### Sidecar Files
- XMP: `.xmp`
- Adobe Camera Raw: `.aae`

## Architecture

ImgMaster follows a clean, service-oriented architecture with the repository pattern for data persistence:

```
imgmaster/
├── main.py              # Lightweight CLI interface
├── services/            # Business logic services
│   ├── database_service.py     # Photo database operations
│   ├── rename_service.py       # File renaming logic
│   ├── presentation_service.py # CLI output formatting
│   └── logging_service.py      # Logging configuration
├── repositories/        # Data persistence abstraction
│   └── photo_group_repository.py  # Repository pattern implementations
├── models/              # Data models
│   ├── photo.py         # Photo file representation
│   ├── photo_group.py   # Photo grouping logic
│   └── metadata.py      # Metadata extraction
└── tests/               # Test suite
```

### Repository Pattern

The application uses the repository pattern to abstract data storage operations:

- **`PhotoGroupRepository`** - Abstract interface for data operations
- **`JsonFilePhotoGroupRepository`** - JSON file-based implementation (default)
- **Future implementations** (TODO):
  - `SqlitePhotoGroupRepository` - SQLite database storage
  - `PostgresPhotoGroupRepository` - PostgreSQL database storage
  - `MongoPhotoGroupRepository` - MongoDB document storage

This architecture provides:
- **Separation of concerns** - Each service has a single responsibility
- **Testability** - Services can be unit tested independently  
- **Maintainability** - Easy to extend and modify
- **Reusability** - Services can be used by other interfaces
- **Flexibility** - Easy to swap storage backends without changing business logic

## Development

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_photo.py
```

### Project Structure
- **CLI Layer** (`main.py`) - User interface and argument parsing
- **Service Layer** (`services/`) - Business logic and operations
- **Model Layer** (`models/`) - Data structures and core logic
- **Test Layer** (`tests/`) - Comprehensive test suite

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

[License information to be added]

## Troubleshooting

### Common Issues

**"No photos found"**
- Check if the directory contains supported photo formats
- Use `--verbose` flag to see detailed scanning information
- Verify file permissions

**"Invalid naming scheme"**
- Ensure all placeholders are spelled correctly
- Check that required metadata is available in your photos
- Use `--dry-run` to test schemes before applying

**Permission errors**
- Ensure write access to destination directory
- Check file permissions on source photos
- Run with appropriate user permissions

### Getting Help

Use the `--help` flag with any command for detailed usage information:

```bash
uv run python main.py --help
uv run python main.py build --help
uv run python main.py rename --help
```

For verbose logging and troubleshooting, add the `--verbose` flag to any command.
