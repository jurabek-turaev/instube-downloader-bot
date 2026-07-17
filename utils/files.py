import os
from config import MAX_FILESIZE

def is_too_large(file_size: int | None) -> bool:
    """Check whether a Telegram file exceeds the size we can handle."""
    return bool(file_size and file_size > MAX_FILESIZE)


def cleanup(*paths: str) -> None:
    """Remove temporary files, ignoring the ones already gone."""
    for path in paths:
        if path and os.path.exists(path):
            os.remove(path)

