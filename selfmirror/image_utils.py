import hashlib
import os
import tempfile
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.files.storage import default_storage


CACHE_DIR = os.path.join(tempfile.gettempdir(), "styriva_image_cache")


def _download(url):
    """Download a URL once and return the local cached file path."""

    os.makedirs(CACHE_DIR, exist_ok=True)

    extension = os.path.splitext(urlparse(url).path)[1] or ".jpg"

    cached_path = os.path.join(
        CACHE_DIR,
        hashlib.sha256(url.encode("utf-8")).hexdigest() + extension,
    )

    if os.path.isfile(cached_path):
        return cached_path

    response = requests.get(url, timeout=60)
    response.raise_for_status()

    with open(cached_path, "wb") as f:
        f.write(response.content)

    return cached_path


def local_path(source):
    """
    Return a real local file path for any of these:
      - a Django file field (e.g. consultation.top_1)
      - a Cloudinary / http(s) URL
      - a storage name (e.g. "tops/abc.jpg")
      - an ordinary local file path

    Cloudinary files have no local path, so they are downloaded
    to a temp cache first.
    """

    if source is None:
        return None

    # Django FieldFile
    if hasattr(source, "storage") and hasattr(source, "name"):

        if not source.name:
            return None

        try:
            return _download(source.url)
        except ValueError:
            return str(source.name)

    value = str(source)

    if value.startswith(("http://", "https://")):
        return _download(value)

    if os.path.isfile(value):
        return value

    media_candidate = os.path.join(settings.MEDIA_ROOT, value)

    if os.path.isfile(media_candidate):
        return media_candidate

    # Storage name that lives on Cloudinary
    try:
        return _download(default_storage.url(value))
    except Exception:
        return value