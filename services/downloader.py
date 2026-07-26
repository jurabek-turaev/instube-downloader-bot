import os
import sys
import yt_dlp
import tempfile
import subprocess
from config import COOKIES_FILE, DOWNLOADS_DIR, MAX_FILESIZE


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
    })

    if os.path.exists(COOKIES_FILE):
        ydl_opts['cookiefile'] = COOKIES_FILE

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        filesize = info.get('filesize') or info.get('filesize_approx')
        if filesize and filesize > MAX_FILESIZE:
            raise ValueError("file_too_large")

        info = ydl.extract_info(url, download=True)
        
        downloads = info.get("requested_downloads")
        if downloads:
            return downloads[0]['filepath']
        
        return ydl.prepare_filename(info)


def download_images(url: str) -> list[str]:
    """Download Instagram images/carousel with gallery-dl. Returns file paths."""
    out_dir = tempfile.mkdtemp(prefix="gdl_", dir=DOWNLOADS_DIR)

    cmd = [sys.executable, "-m", "gallery_dl", "-D", out_dir, url]
    if os.path.exists(COOKIES_FILE):
        cmd[3:3] = ["--cookies", COOKIES_FILE]

    subprocess.run(cmd, check=True, capture_output=True, text=True)

    files = sorted(os.path.join(out_dir, f) for f in os.listdir(out_dir))
    return files[:10]
