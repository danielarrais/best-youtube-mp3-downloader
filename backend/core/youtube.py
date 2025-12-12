import re
from dataclasses import dataclass

from pytubefix import Playlist, YouTube


@dataclass
class VideoInfo:
    title: str
    url: str
    duration: int  # seconds


def sanitize_filename(filename: str) -> str:
    """Remove caracteres inválidos para nomes de arquivo"""
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def get_video_info(url: str) -> VideoInfo:
    """Obtém informações de um vídeo do YouTube"""
    yt = YouTube(url)
    return VideoInfo(
        title=yt.title,
        url=url,
        duration=yt.length or 0
    )


def extract_playlist_urls(playlist_url: str) -> list[str]:
    """Extrai URLs de uma playlist do YouTube"""
    playlist = Playlist(playlist_url)
    return list(playlist.video_urls)


def get_audio_stream(url: str):
    """Obtém o stream de áudio de um vídeo"""
    yt = YouTube(url)
    return yt.streams.filter(only_audio=True).first(), yt
