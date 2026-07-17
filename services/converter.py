import subprocess
from config import VIDEO_NOTE_MAX_DURATION, VIDEO_NOTE_SIZE


def convert_audio(input_path: str, output_path: str, codec: str) -> None:
    """Convert an audio file to the given codec using ffmpeg."""
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error",
         "-i", input_path, "-c:a", codec, output_path, "-y"],
        check=True
    )


def convert_to_video_note(input_path: str, output_path: str) -> None:
    """Crop a video to a centered square and scale it to video note format."""
    video_filter = (
        f"crop=min(iw\\,ih):min(iw\\,ih),"
        f"scale={VIDEO_NOTE_SIZE}:{VIDEO_NOTE_SIZE}"
    )
    subprocess.run(
        ['ffmpeg', '-hide_banner', '-loglevel', 'error',
         '-i', input_path,
         '-vf', video_filter,
         '-t', str(VIDEO_NOTE_MAX_DURATION),
         '-c:v', 'libx264', '-c:a', 'aac', '-pix_fmt', 'yuv420p',
         output_path, '-y'],
        check=True,
    )

