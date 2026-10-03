"""
utils.py

Utility functions for the STYRIVA
media management system.
"""

from pathlib import Path
from datetime import datetime
from uuid import uuid4

from .constants import (
    ALLOWED_EXTENSIONS,
    SIZE_UNITS,
)


def ensure_directory_exists(directory):
    """
    Create a directory if it does not exist.

    Parameters
    ----------
    directory : str | Path

    Returns
    -------
    Path
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_file_extension(file_path):
    """
    Return the file extension in lowercase.

    Parameters
    ----------
    file_path : str | Path

    Returns
    -------
    str
    """
    return Path(file_path).suffix.lower()


def get_file_name(file_path):
    """
    Return the filename.

    Example
    -------
    media/uploads/photo.png

    Returns
    -------
    photo.png
    """
    return Path(file_path).name


def get_stem(file_path):
    """
    Return filename without extension.

    Example
    -------
    photo.png

    Returns
    -------
    photo
    """
    return Path(file_path).stem


def is_image_file(file_path):
    """
    Check whether a file is a supported image.

    Parameters
    ----------
    file_path : str | Path

    Returns
    -------
    bool
    """
    return get_file_extension(file_path) in ALLOWED_EXTENSIONS


def generate_unique_filename(filename):
    """
    Generate a unique filename while preserving
    the original extension.

    Example
    -------
    photo.png

    becomes

    e3f0f6f3f6a7482c9dbdb7f65db5b15d.png
    """
    filename = Path(filename)

    unique_name = uuid4().hex

    return f"{unique_name}{filename.suffix.lower()}"


def current_timestamp():
    """
    Return the current timestamp.

    Returns
    -------
    str
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_file_size(size):
    """
    Convert bytes into a human-readable format.

    Parameters
    ----------
    size : int

    Returns
    -------
    str
    """
    size = float(size)

    for unit in SIZE_UNITS:
        if size < 1024:
            return f"{size:.2f} {unit}"

        size /= 1024

    return f"{size:.2f} PB"


def file_exists(file_path):
    """
    Check whether a file exists.

    Parameters
    ----------
    file_path : str | Path

    Returns
    -------
    bool
    """
    return Path(file_path).is_file()


def directory_exists(directory):
    """
    Check whether a directory exists.

    Parameters
    ----------
    directory : str | Path

    Returns
    -------
    bool
    """
    return Path(directory).is_dir()


def get_file_size(file_path):
    """
    Return file size in bytes.

    Parameters
    ----------
    file_path : str | Path

    Returns
    -------
    int
    """
    file_path = Path(file_path)

    if not file_path.is_file():
        return 0

    return file_path.stat().st_size


def get_directory_size(directory):
    """
    Calculate the total size of a directory.

    Parameters
    ----------
    directory : str | Path

    Returns
    -------
    int
    """
    directory = Path(directory)

    if not directory.exists():
        return 0

    total = 0

    for file in directory.rglob("*"):
        if file.is_file():
            total += file.stat().st_size

    return total


def list_files(directory):
    """
    Return all files inside a directory.

    Parameters
    ----------
    directory : str | Path

    Returns
    -------
    list[Path]
    """
    directory = Path(directory)

    if not directory.exists():
        return []

    return [
        file
        for file in directory.rglob("*")
        if file.is_file()
    ]


def list_directories(directory):
    """
    Return all subdirectories.

    Parameters
    ----------
    directory : str | Path

    Returns
    -------
    list[Path]
    """
    directory = Path(directory)

    if not directory.exists():
        return []

    return [
        folder
        for folder in directory.rglob("*")
        if folder.is_dir()
    ]