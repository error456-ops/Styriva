"""
cleanup.py

Responsible for cleaning up files and directories
used by the STYRIVA media pipeline.
"""

from pathlib import Path
import shutil
import time


class Cleanup:
    """
    Handles cleanup operations for uploaded,
    generated and temporary media files.
    """

    def delete_file(self, file_path):
        """
        Delete a single file.

        Returns
        -------
        bool
            True if deleted successfully,
            False otherwise.
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return False

        if not file_path.is_file():
            return False

        file_path.unlink()

        return True

    def delete_directory(self, directory_path):
        """
        Delete a directory recursively.

        Returns
        -------
        bool
            True if deleted successfully,
            False otherwise.
        """
        directory_path = Path(directory_path)

        if not directory_path.exists():
            return False

        if not directory_path.is_dir():
            return False

        shutil.rmtree(directory_path)

        return True

    def remove_empty_directories(self, root_directory):
        """
        Remove all empty directories
        under the given root.

        Returns
        -------
        int
            Number of directories removed.
        """
        root_directory = Path(root_directory)

        if not root_directory.exists():
            return 0

        removed = 0

        for directory in sorted(root_directory.rglob("*"), reverse=True):
            if directory.is_dir():
                try:
                    directory.rmdir()
                    removed += 1
                except OSError:
                    pass

        return removed

    def cleanup_temp(self, temp_directory):
        """
        Delete every file inside
        the temporary directory.

        Returns
        -------
        int
            Number of deleted files.
        """
        temp_directory = Path(temp_directory)

        if not temp_directory.exists():
            return 0

        deleted = 0

        for file in temp_directory.rglob("*"):
            if file.is_file():
                file.unlink()
                deleted += 1

        return deleted

    def cleanup_old_files(self, directory, days=30):
        """
        Delete files older than
        the specified number of days.

        Returns
        -------
        int
            Number of deleted files.
        """
        directory = Path(directory)

        if not directory.exists():
            return 0

        cutoff = time.time() - (days * 24 * 60 * 60)

        deleted = 0

        for file in directory.rglob("*"):
            if file.is_file():
                if file.stat().st_mtime < cutoff:
                    file.unlink()
                    deleted += 1

        return deleted

    def cleanup_orphans(self):
        """
        Placeholder for future orphan cleanup.

        This will compare files on disk with
        database records and remove files that
        no longer belong to any model.

        Returns
        -------
        int
            Number of orphaned files removed.
        """
        return 0