"""
manager.py

High-level interface for the STYRIVA media system.

This module provides a single entry point for all media operations,
including validation, storage, cleanup, and statistics.
"""

from .storage import Storage
from .validator import Validator
from .cleanup import Cleanup
from .statistics import Statistics


class MediaManager:
    """
    Central interface for all media-related operations.

    Instead of interacting directly with Storage, Validator,
    Cleanup, or Statistics, the rest of STYRIVA should only
    communicate with this class.
    """

    def __init__(self):
        self.storage = Storage()
        self.validator = Validator()
        self.cleanup = Cleanup()
        self.stats = Statistics()

    # =====================================================
    # Validation
    # =====================================================

    def validate_upload(self, image):
        """
        Validate an uploaded image before processing.

        Runs complete validation including:
        - file existence
        - allowed extension
        - maximum file size
        - image integrity
        - minimum dimensions

        Supports both Django UploadedFile objects
        and filesystem paths.

        Parameters
        ----------
        image : UploadedFile | str | Path

        Returns
        -------
        tuple
            (True, "Validation passed.")
            or
            (False, "Error message.")
        """
        return self.validator.validate(image)

    # =====================================================
    # Storage
    # =====================================================

    def save(self, *args, **kwargs):
        """
        Save media using the Storage module.

        Returns
        -------
        Depends on Storage.save()
        """
        return self.storage.save(*args, **kwargs)

    def delete(self, file_path):
        """
        Delete a media file.

        Parameters
        ----------
        file_path : str | Path

        Returns
        -------
        bool
        """
        return self.storage.delete(file_path)

    # =====================================================
    # Cleanup
    # =====================================================

    def delete_file(self, file_path):
        """
        Delete a single file.
        """
        return self.cleanup.delete_file(file_path)

    def delete_directory(self, directory_path):
        """
        Delete a directory.
        """
        return self.cleanup.delete_directory(directory_path)

    def remove_empty_directories(self, root_directory):
        """
        Remove all empty directories.
        """
        return self.cleanup.remove_empty_directories(root_directory)

    def cleanup_temp(self, temp_directory):
        """
        Delete temporary files.
        """
        return self.cleanup.cleanup_temp(temp_directory)

    def cleanup_old_files(self, directory, days=30):
        """
        Delete files older than the specified number of days.
        """
        return self.cleanup.cleanup_old_files(
            directory,
            days
        )

    def cleanup_orphans(self):
        """
        Delete orphaned media files.

        Placeholder until orphan detection
        is implemented.
        """
        return self.cleanup.cleanup_orphans()

    # =====================================================
    # Statistics
    # =====================================================

    def get_file_count(self, directory):
        """
        Return total number of files.
        """
        return self.stats.get_file_count(directory)

    def get_directory_size(self, directory):
        """
        Return directory size in bytes.
        """
        return self.stats.get_directory_size(directory)

    def get_storage_usage(self, directory):
        """
        Return storage usage in bytes.
        """
        return self.stats.get_storage_usage(directory)

    def get_free_space(self, directory):
        """
        Return available disk space in bytes.
        """
        return self.stats.get_free_space(directory)

    def get_statistics(self, directory):
        """
        Return a summary of storage statistics.

        Returns
        -------
        dict
        """
        return self.stats.get_summary(directory)