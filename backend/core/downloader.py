import os
from collections.abc import Callable
from dataclasses import dataclass

from backend.config import settings
from backend.core.converter import convert_to_mp3
from backend.core.youtube import get_audio_stream, sanitize_filename


@dataclass
class DownloadResult:
    success: bool
    title: str = ""
    file_path: str = ""
    file_size: int = 0
    error: str = ""
    skipped: bool = False


def download_and_convert(
    url: str,
    quality: str = "192k",
    download_callback: Callable[[float, int, int, float], None] | None = None,
    convert_callback: Callable[[float], None] | None = None
) -> DownloadResult:
    """
    Baixa e converte um vídeo do YouTube para MP3.

    download_callback(percent, downloaded_bytes, total_bytes, speed)
    convert_callback(percent)
    """
    # Obter stream de áudio
    audio_stream, yt = get_audio_stream(url)

    if not audio_stream:
        return DownloadResult(success=False, error="Nenhum stream de áudio encontrado")

    title = yt.title
    safe_title = sanitize_filename(title)
    mp3_path = os.path.join(settings.DOWNLOAD_DIR, f"{safe_title}.mp3")

    # Verificar se já existe
    if os.path.exists(mp3_path):
        return DownloadResult(
            success=True,
            title=title,
            file_path=mp3_path,
            file_size=os.path.getsize(mp3_path),
            skipped=True
        )

    # Criar diretórios
    os.makedirs(settings.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    temp_file = os.path.join(settings.TEMP_DIR, f"{safe_title}.tmp")

    # Remover arquivo temporário se existir
    if os.path.exists(temp_file):
        os.remove(temp_file)

    # Configurar callback de progresso do download
    file_size = audio_stream.filesize
    last_bytes = [0]

    def on_progress(stream, chunk, bytes_remaining):
        downloaded = file_size - bytes_remaining
        percent = (downloaded / file_size) * 100
        speed = downloaded - last_bytes[0]
        last_bytes[0] = downloaded
        if download_callback:
            download_callback(percent, downloaded, file_size, speed)

    yt.register_on_progress_callback(on_progress)

    # Download
    audio_stream.download(output_path=settings.TEMP_DIR, filename=f"{safe_title}.tmp")

    # Converter para MP3
    success = convert_to_mp3(temp_file, mp3_path, quality, convert_callback)

    # Limpar arquivo temporário
    if os.path.exists(temp_file):
        os.remove(temp_file)

    if not success:
        return DownloadResult(success=False, title=title, error="Erro na conversão")

    return DownloadResult(
        success=True,
        title=title,
        file_path=mp3_path,
        file_size=os.path.getsize(mp3_path) if os.path.exists(mp3_path) else 0
    )
