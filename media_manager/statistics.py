"""
statistics.py

Collects storage statistics for the STYRIVA media system.
"""

from pathlib import Path
import shutil


class Statistics:
    """
    Provides statistics about media storage.
    """

    def get_file_count(self, directory):
        """
        Count all files inside a directory.

        Returns
        -------
        int
            Total number of files.
        """
        directory = Path(directory)

        if not directory.exists():
            return 0

        return sum(
            1
            for item in directory.rglob("*")
            if item.is_file()
        )

    def get_directory_size(self, directory):
        """
        Calculate the total size of a directory.

        Returns
        -------
        int
            Size in bytes.
        """
        directory = Path(directory)

        if not directory.exists():
            return 0

        return sum(
            file.stat().st_size
            for file in directory.rglob("*")
            if file.is_file()
        )

    def get_storage_usage(self, directory):
        """
        Alias for directory size.

        Returns
        -------
        int
            Storage used in bytes.
        """
        return self.get_directory_size(directory)

    def get_free_space(self, directory):
        """
        Return available disk space.

        Returns
        -------
        int
            Free space in bytes.
        """
        directory = Path(directory)

        usage = shutil.disk_usage(directory)

        return usage.free

    def get_summary(self, directory):
        """
        Return a summary of media statistics.

        Returns
        -------
        dict
        """
        return {
            "files": self.get_file_count(directory),
            "storage_used": self.get_storage_usage(directory),
            "free_space": self.get_free_space(directory),
        }