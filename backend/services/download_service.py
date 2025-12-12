import asyncio
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from backend.core.downloader import download_and_convert
from backend.core.youtube import get_video_info
from backend.models.download import DownloadItem, DownloadProgress, DownloadStatus
from backend.services.queue_service import queue_service

executor = ThreadPoolExecutor(max_workers=3)


async def process_download(
    item: DownloadItem,
    progress_callback: Callable[[DownloadItem], None] | None = None
) -> DownloadItem:
    """Processa o download de um item"""

    # Atualizar status para fetching
    item.status = DownloadStatus.FETCHING_INFO
    item.started_at = datetime.utcnow()
    await queue_service.update_item(item.id, item)
    if progress_callback:
        await progress_callback(item)

    try:
        # Obter informações do vídeo (em thread separada)
        loop = asyncio.get_event_loop()
        video_info = await loop.run_in_executor(executor, get_video_info, item.url)
        item.title = video_info.title

        # Atualizar status para downloading
        item.status = DownloadStatus.DOWNLOADING
        await queue_service.update_item(item.id, item)
        if progress_callback:
            await progress_callback(item)

        # Callbacks de progresso
        def on_download_progress(percent, downloaded, total, speed):
            item.progress = DownloadProgress(
                percent=percent,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=f"{speed / 1024:.1f} KB/s" if speed > 0 else ""
            )

        def on_convert_progress(percent):
            item.status = DownloadStatus.CONVERTING
            item.progress.percent = percent

        # Executar download em thread separada (pode ser cancelado)
        result = await loop.run_in_executor(
            executor,
            lambda: download_and_convert(
                url=item.url,
                quality=item.quality,
                download_callback=on_download_progress,
                convert_callback=on_convert_progress
            )
        )

        if result.success:
            if result.skipped:
                item.status = DownloadStatus.SKIPPED
            else:
                item.status = DownloadStatus.COMPLETED
            item.file_path = result.file_path
            item.file_size = result.file_size
            item.progress.percent = 100
        else:
            item.status = DownloadStatus.FAILED
            item.error = result.error

    except asyncio.CancelledError:
        # Item foi cancelado - não atualiza nada
        raise
    except Exception as e:
        item.status = DownloadStatus.FAILED
        item.error = str(e)

    item.completed_at = datetime.utcnow()
    await queue_service.update_item(item.id, item)
    if progress_callback:
        await progress_callback(item)

    return item
