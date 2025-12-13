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

        # Fila para comunicar progresso da thread para o asyncio
        progress_queue: asyncio.Queue = asyncio.Queue()

        # Callbacks de progresso (executados na thread)
        def on_download_progress(percent, downloaded, total, speed):
            item.progress = DownloadProgress(
                percent=percent,
                downloaded_bytes=downloaded,
                total_bytes=total,
                speed=f"{speed / 1024:.1f} KB/s" if speed > 0 else ""
            )
            # Envia para a fila de forma thread-safe
            loop.call_soon_threadsafe(progress_queue.put_nowait, ("download", item.progress))

        def on_convert_progress(percent):
            item.status = DownloadStatus.CONVERTING
            item.progress.percent = percent
            loop.call_soon_threadsafe(progress_queue.put_nowait, ("convert", percent))

        # Task para processar atualizações de progresso
        async def process_progress():
            last_update = 0
            while True:
                try:
                    msg = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                    # Limitar updates a cada 500ms
                    now = asyncio.get_event_loop().time()
                    if now - last_update >= 0.5:
                        await queue_service.update_item(item.id, item)
                        if progress_callback:
                            await progress_callback(item)
                        last_update = now
                except asyncio.TimeoutError:
                    continue
                except asyncio.CancelledError:
                    break

        # Iniciar task de progresso
        progress_task = asyncio.create_task(process_progress())

        try:
            # Executar download em thread separada
            result = await loop.run_in_executor(
                executor,
                lambda: download_and_convert(
                    url=item.url,
                    quality=item.quality,
                    download_callback=on_download_progress,
                    convert_callback=on_convert_progress
                )
            )
        finally:
            progress_task.cancel()
            try:
                await progress_task
            except asyncio.CancelledError:
                pass

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
