import os
import shutil
from config import MAX_INCOMING_FILESIZE, MB, USE_LOCAL_API, bot


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


async def download_tg_file(file_id: str, destination: str) -> None:
    """ Download a user's file; in local mode also remove the server's copy. """
    file = await bot.get_file(file_id)
    await bot.download_file(file.file_path, destination)
    if USE_LOCAL_API:
        # file_path is a real path on the shared volume in local mode.
        cleanup(file.file_path)

def size_text(size: int) -> str:
    return f"{size // MB}MB"
