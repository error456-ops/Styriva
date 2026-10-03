from pathlib import Path

from PIL import Image


class Validator:
    """
    Validates images before they enter
    the STYRIVA media pipeline.

    Supports:
    - Django UploadedFile objects
    - Filesystem paths (str / Path)
    """

    ALLOWED_EXTENSIONS = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    MIN_WIDTH = 200
    MIN_HEIGHT = 200

    # =====================================================
    # Helpers
    # =====================================================

    def _is_uploaded_file(self, file):
        """
        Check whether the object behaves like
        a Django UploadedFile.
        """
        return (
            hasattr(file, "name")
            and hasattr(file, "size")
            and hasattr(file, "read")
        )

    def _reset_file_pointer(self, file):
        """
        Reset uploaded file pointer after Pillow
        reads or verifies the image.
        """
        if hasattr(file, "seek"):
            try:
                file.seek(0)
            except Exception:
                pass

    # =====================================================
    # File Exists
    # =====================================================

    def file_exists(self, file):
        """
        Check whether the file exists.

        Uploaded files already exist in memory
        or temporary upload storage.

        Filesystem paths are checked normally.
        """

        if file is None:
            return False

        if self._is_uploaded_file(file):
            return True

        try:
            return Path(file).is_file()

        except (TypeError, ValueError):
            return False

    # =====================================================
    # Extension Validation
    # =====================================================

    def extension_allowed(self, file):
        """
        Check whether the file extension
        is supported.
        """

        if file is None:
            return False

        try:

            if self._is_uploaded_file(file):
                filename = file.name

            else:
                filename = file

            extension = Path(filename).suffix.lower()

            return extension in self.ALLOWED_EXTENSIONS

        except (TypeError, ValueError):
            return False

    # =====================================================
    # File Size Validation
    # =====================================================

    def file_size_allowed(self, file):
        """
        Check whether the file size is within
        the maximum allowed limit.
        """

        if file is None:
            return False

        try:

            if self._is_uploaded_file(file):
                size = file.size

            else:
                size = Path(file).stat().st_size

            return size <= self.MAX_FILE_SIZE

        except (OSError, TypeError, ValueError):
            return False

    # =====================================================
    # Image Integrity Validation
    # =====================================================

    def image_valid(self, file):
        """
        Verify that the image is readable
        and is not corrupted.

        Works with both Django UploadedFile
        objects and filesystem paths.
        """

        if file is None:
            return False

        try:

            if self._is_uploaded_file(file):
                self._reset_file_pointer(file)

            with Image.open(file) as image:
                image.verify()

            if self._is_uploaded_file(file):
                self._reset_file_pointer(file)

            return True

        except Exception:

            if self._is_uploaded_file(file):
                self._reset_file_pointer(file)

            return False

    # =====================================================
    # Dimension Validation
    # =====================================================

    def dimensions_valid(self, file):
        """
        Check whether image dimensions meet
        the minimum requirements.
        """

        if file is None:
            return False

        try:

            if self._is_uploaded_file(file):
                self._reset_file_pointer(file)

            with Image.open(file) as image:
                width, height = image.size

            if self._is_uploaded_file(file):
                self._reset_file_pointer(file)

            return (
                width >= self.MIN_WIDTH
                and height >= self.MIN_HEIGHT
            )

        except Exception:

            if self._is_uploaded_file(file):
                self._reset_file_pointer(file)

            return False

    # =====================================================
    # Complete Validation
    # =====================================================

    def validate(self, file):
        """
        Run all validation checks.

        Returns
        -------
        tuple
            (True, "Validation passed.")

            or

            (False, "Error message.")
        """

        if file is None:
            return False, "No file was provided."

        if not self.file_exists(file):
            return False, "File does not exist."

        if not self.extension_allowed(file):
            return False, "Unsupported file extension."

        if not self.file_size_allowed(file):
            return False, (
                "File size exceeds the maximum "
                "allowed limit of 10 MB."
            )

        if not self.image_valid(file):
            return False, "Image is corrupted or unreadable."

        if not self.dimensions_valid(file):
            return False, (
                "Image dimensions are too small. "
                "Minimum size is 200x200 pixels."
            )

        return True, "Validation passed."