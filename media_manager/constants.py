"""
constants.py

Shared constants used throughout the
STYRIVA media management system.
"""

from pathlib import Path


# ==========================================================
# Media Directories
# ==========================================================

MEDIA_ROOT = Path("media")

UPLOAD_DIRECTORY = MEDIA_ROOT / "uploads"

GENERATED_DIRECTORY = MEDIA_ROOT / "generated"

TEMP_DIRECTORY = MEDIA_ROOT / "temp"

THUMBNAIL_DIRECTORY = MEDIA_ROOT / "thumbnails"

LOG_DIRECTORY = MEDIA_ROOT / "logs"


# ==========================================================
# File Validation
# ==========================================================

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

MAX_FILENAME_LENGTH = 255

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ==========================================================
# Supported Image Formats (Pillow)
# ==========================================================

SUPPORTED_IMAGE_FORMATS = {
    "JPEG",
    "PNG",
    "WEBP",
}


# ==========================================================
# Default File Names
# ==========================================================

DEFAULT_IMAGE_EXTENSION = ".png"

GENERATED_PREFIX = "generated_"

TEMP_PREFIX = "temp_"

THUMBNAIL_PREFIX = "thumb_"


# ==========================================================
# Cleanup Settings
# ==========================================================

DEFAULT_CLEANUP_DAYS = 30


# ==========================================================
# Statistics
# ==========================================================

SIZE_UNITS = (
    "B",
    "KB",
    "MB",
    "GB",
    "TB",
    "PB",
)


# ==========================================================
# File Permissions
# ==========================================================

READ_MODE = "rb"

WRITE_MODE = "wb"


# ==========================================================
# Encoding
# ==========================================================

DEFAULT_ENCODING = "utf-8"


# ==========================================================
# Image Quality
# ==========================================================

DEFAULT_IMAGE_QUALITY = 95


# ==========================================================
# Temporary Files
# ==========================================================

TEMP_FILE_SUFFIX = ".tmp"


# ==========================================================
# Miscellaneous
# ==========================================================

UNKNOWN_FILE_NAME = "unknown"

EMPTY_STRING = ""