import os
import shutil
from config import MAX_INCOMING_FILESIZE


def is_too_large(file_size: int | None) -> bool:
    """Check whether a file sent by a user is over the Bot API download limit."""
    return bool(file_size and file_size > MAX_INCOMING_FILESIZE)


def cleanup(*paths: str) -> None:
    """Remove temporary files, ignoring the ones already gone."""
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)


def cleanup_dir(path: str) -> None:
    """Remove a directory and everyting in it, if it exists."""
    if path and os.path.exists(path):
        shutil.rmtree(path, ignore_errors=True)
