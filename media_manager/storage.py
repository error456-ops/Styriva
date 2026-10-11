
import shutil
import tempfile
import uuid
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


class Storage:
    """Cloudinary-backed storage for STYRIVA."""

    def __init__(self):
        self.storage = default_storage
        self.media_root = Path(settings.MEDIA_ROOT)

    def save(self, path, file):
        """Save a file through Django's configured storage."""
        return self.storage.save(str(path), file)

    
    def delete(self, path):
        """Delete a file through Django's configured storage."""
        self.storage.delete(str(path))
        return not self.storage.exists(str(path))

    def exists(self, path):
        return self.storage.exists(path)

    def open(self, path, mode="rb"):
        return self.storage.open(path, mode)

    def url(self, path):
        return self.storage.url(path)

    def path(self, path):
        """
        Cloudinary assets do not have a permanent local path.
        Download the asset to a temporary file instead.
        The caller is responsible for deleting that file.
        """
        suffix = Path(str(path)).suffix or ".tmp"

        with self.storage.open(path, "rb") as source:
            with tempfile.NamedTemporaryFile(
                suffix=suffix,
                delete=False,
            ) as destination:
                shutil.copyfileobj(source, destination)
                return destination.name

    def size(self, path):
        return self.storage.size(path)

    def copy(self, source, destination):
        """Copy a stored file by reading and saving its contents."""
        with self.storage.open(source, "rb") as source_file:
            saved_path = self.storage.save(
                destination,
                ContentFile(
                    source_file.read(),
                    name=Path(destination).name,
                ),
            )
        return saved_path

    def move(self, source, destination):
        """Copy to the destination, then delete the source."""
        saved_path = self.copy(source, destination)
        self.storage.delete(source)
        return saved_path

    def rename(self, source, new_name):
        """Rename by copying to a new path and deleting the old asset."""
        destination = str(Path(source).parent / new_name)
        return self.move(source, destination)

    def create_directory(self, directory):
        """
        Cloudinary folders are virtual.
        Return the intended folder name without creating a local folder.
        """
        return str(directory).strip("/")

    def directory_exists(self, directory):
        """Cloudinary folders are virtual; local folder checks are not valid."""
        return False

    def list_files(self, directory):
        """
        Local directory enumeration is unavailable for Cloudinary.
        """
        return []

    def list_directories(self, directory):
        """
        Local directory enumeration is unavailable for Cloudinary.
        """
        return []

    def directory_size(self, directory):
        """
        Local filesystem size is not Cloudinary storage usage.
        """
        return 0

    def unique_filename(self, filename):
        extension = Path(filename).suffix
        return f"{uuid.uuid4().hex}{extension}"
