import subprocess
from collections.abc import Callable

from backend.config import settings


def get_audio_duration(file_path: str) -> float:
    """Obtém a duração do áudio em segundos"""
    cmd = [
        settings.FFPROBE_PATH, '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except (ValueError, AttributeError):
        return 0


def convert_to_mp3(
    input_path: str,
    output_path: str,
    quality: str = "192k",
    progress_callback: Callable[[float], None] | None = None
) -> bool:
    """Converte arquivo de áudio para MP3"""
    duration = get_audio_duration(input_path)

    cmd = [
        settings.FFMPEG_PATH,
        '-i', input_path,
        '-vn',
        '-acodec', 'libmp3lame',
        '-ab', quality,
        '-y',
        '-progress', 'pipe:1',
        '-nostats',
        output_path
    ]

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    total_duration_us = int(duration * 1_000_000) if duration > 0 else 0

    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break

        if line.startswith('out_time_us=') and total_duration_us > 0:
            try:
                current_time_us = int(line.split('=')[1].strip())
                percent = min((current_time_us / total_duration_us) * 100, 99.9)
                if progress_callback:
                    progress_callback(percent)
            except (ValueError, IndexError):
                pass

    return process.returncode == 0
