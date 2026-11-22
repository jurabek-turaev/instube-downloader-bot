import os
import sys
import yt_dlp
import tempfile
import subprocess
from config import COOKIES_FILE, DOWNLOADS_DIR, MAX_FILESIZE
from yt_dlp.extractor import get_info_extractor

CACHEABLE_EXTRACTORS = ("Youtube", "Instagram")

def get_media_key(url: str, media_type: str) -> str | None:
    """ Build a cache key like 'Youtube:<id>:video' from the URL, without network. """
    for name in CACHEABLE_EXTRACTORS:
        ie = get_info_extractor(name)
        if ie.suitable(url):
            video_id = ie.get_temp_id(url)
            return f"{name}:{video_id}:{media_type}" if video_id else None
    return None

def download_video(url: str, media_type: str) -> str:
    """Download a link as video or audio and return the final file path."""
    if media_type == "audio":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'{DOWNLOADS_DIR}/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:  # video
        ydl_opts = {
            'format': 'bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b',
            'outtmpl': f'{DOWNLOADS_DIR}/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
        }

    ydl_opts.update({
        'quiet': True,
        'no_warnings': True,
        'noprogress': True,
        # "watch?v=...&list=..." -> just the video, not the whole playlist.
        'noplaylist': True,
    })

    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

        # A multi-item post (e.g. an Instagram carousel): yt-dlp would only
        # give us one of the items, so let the caller use gallery-dl instead.
        if info.get('_type') == 'playlist' or info.get('entries'):
            raise MultipleMediaError(url)

        filesize = _estimate_size(info, media_type)
        if filesize and filesize > MAX_FILESIZE:
            raise ValueError("file_too_large")

        info = ydl.extract_info(url, download=True)

        downloads = info.get("requested_downloads")
        filepath = downloads[0]['filepath'] if downloads else ydl.prepare_filename(info)

    # The estimate can be missing or wrong, so check the real file too.
    if os.path.getsize(filepath) > MAX_FILESIZE:
        os.remove(filepath)
        raise ValueError("file_too_large")

    return filepath


class MultipleMediaError(Exception):
    """The link holds several media items; download it with gallery-dl."""


def _estimate_size(info: dict, media_type: str) -> int | None:
    """Best-effort size estimate in bytes, before downloading."""
    if media_type == "audio":
        # The result is re-encoded to 192 kbps mp3, so duration decides it.
        duration = info.get('duration')
        if duration:
            return int(duration * 192_000 / 8)

    size = info.get('filesize') or info.get('filesize_approx')
    if size:
        return size

    # Separate video + audio streams that get merged: add up their sizes.
    formats = info.get('requested_formats') or []
    sizes = [f.get('filesize') or f.get('filesize_approx') for f in formats]
    if sizes and all(sizes):
        return sum(sizes)

    return None


def download_images(url: str) -> list[str]:
    """Download an Instagram post/carousel/story with gallery-dl.

    Returns the paths of every downloaded item, photos and videos alike.
    """
    out_dir = tempfile.mkdtemp(prefix="gdl_", dir=DOWNLOADS_DIR)

    cmd = [sys.executable, "-m", "gallery_dl", "-D", out_dir, url]
    if os.path.exists(COOKIES_FILE):
        cmd[3:3] = ["--cookies", COOKIES_FILE]

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    files = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir))
    return files
