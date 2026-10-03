"""
exceptions.py

Custom exceptions used throughout the
STYRIVA media management system.
"""


class MediaManagerError(Exception):
    """
    Base exception for all media-related errors.
    """
    pass


class ValidationError(MediaManagerError):
    """
    Raised when uploaded media fails validation.
    """
    pass


class StorageError(MediaManagerError):
    """
    Raised when saving, moving,
    copying or deleting media fails.
    """
    pass


class CleanupError(MediaManagerError):
    """
    Raised when cleanup operations fail.
    """
    pass


class StatisticsError(MediaManagerError):
    """
    Raised when media statistics
    cannot be calculated.
    """
    pass


class FileNotFoundError(MediaManagerError):
    """
    Raised when an expected media
    file cannot be found.
    """
    pass


class InvalidMediaError(MediaManagerError):
    """
    Raised when media is invalid or
    unsupported.
    """
    pass


class DirectoryNotFoundError(MediaManagerError):
    """
    Raised when a directory
    does not exist.
    """
    pass


class PermissionDeniedError(MediaManagerError):
    """
    Raised when the application
    does not have permission to
    access a file or directory.
    """
    pass