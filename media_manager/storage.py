import shutil
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage


class Storage:
    """
    Handles all file storage operations for STYRIVA.
    """

    def __init__(self):
        self.storage = default_storage
        self.media_root = Path(settings.MEDIA_ROOT)

    def save(self, path, file):
        """
        Save a file and return its relative path.
        """
        return self.storage.save(path, file)

    def delete(self, path):
        """
        Delete a file if it exists.
        """
        if self.storage.exists(path):
            self.storage.delete(path)

    def exists(self, path):
        """
        Check whether a file exists.
        """
        return self.storage.exists(path)

    def open(self, path, mode="rb"):
        """
        Open a stored file.
        """
        return self.storage.open(path, mode)

    def url(self, path):
        """
        Return the public URL of a file.
        """
        return self.storage.url(path)

    def path(self, path):
        """
        Return the absolute filesystem path.
        """
        return self.storage.path(path)

    def size(self, path):
        """
        Return the file size in bytes.
        """
        return self.storage.size(path)

    def copy(self, source, destination):
        """
        Copy a file to another location.
        """
        source_path = Path(self.path(source))
        destination_path = Path(self.path(destination))

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(source_path, destination_path)

        return destination

    def move(self, source, destination):
        """
        Move a file to another location.
        """
        source_path = Path(self.path(source))
        destination_path = Path(self.path(destination))

        destination_path.parent.mkdir(parents=True, exist_ok=True)

        shutil.move(source_path, destination_path)

        return destination

    def rename(self, source, new_name):
        """
        Rename a file while keeping it in the same folder.
        """
        source_path = Path(self.path(source))

        destination = source_path.parent / new_name

        shutil.move(source_path, destination)

        return str(destination)

    def create_directory(self, directory):
        """
        Create a directory if it doesn't exist.
        """
        directory_path = self.media_root / directory

        directory_path.mkdir(parents=True, exist_ok=True)

        return directory_path

    def directory_exists(self, directory):
        """
        Check whether a directory exists.
        """
        return (self.media_root / directory).exists()

    def list_files(self, directory):
        """
        Return all files inside a directory.
        """
        directory_path = self.media_root / directory

        if not directory_path.exists():
            return []

        return [
            file
            for file in directory_path.iterdir()
            if file.is_file()
        ]

    def list_directories(self, directory):
        """
        Return all subdirectories inside a directory.
        """
        directory_path = self.media_root / directory

        if not directory_path.exists():
            return []

        return [
            folder
            for folder in directory_path.iterdir()
            if folder.is_dir()
        ]

    def directory_size(self, directory):
        """
        Return the total size of a directory in bytes.
        """
        directory_path = self.media_root / directory

        total = 0

        if not directory_path.exists():
            return total

        for file in directory_path.rglob("*"):
            if file.is_file():
                total += file.stat().st_size

        return total

    def unique_filename(self, filename):
        """
        Generate a unique filename while preserving its extension.
        """
        extension = Path(filename).suffix

        return f"{uuid.uuid4().hex}{extension}"