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


def is_playlist_url(url: str) -> bool:
    """Verifica se a URL é de uma playlist (e não um vídeo com playlist)"""
    # URL de playlist pura: youtube.com/playlist?list=XXX
    # URL de vídeo em playlist: youtube.com/watch?v=XXX&list=YYY
    if "youtube.com/playlist" in url:
        return True
    # Se tem list= mas não tem v=, é playlist
    if "list=" in url and "v=" not in url:
        return True
    return False


def expand_urls(urls: list[str]) -> list[str]:
    """Expande URLs de playlists para URLs de vídeos individuais"""
    result = []
    for url in urls:
        if is_playlist_url(url):
            try:
                playlist_urls = extract_playlist_urls(url)
                result.extend(playlist_urls)
            except Exception:
                # Se falhar, ignora a playlist
                pass
        else:
            result.append(url)
    return result


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
