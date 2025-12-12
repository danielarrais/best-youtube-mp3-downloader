import asyncio
import concurrent.futures

from backend.api.websocket import broadcast_item_update, broadcast_stats_update
from backend.config import settings
from backend.services.download_service import process_download
from backend.services.queue_service import queue_service

# Controle do worker
is_running = True
active_tasks: dict[str, asyncio.Task] = {}
executor = concurrent.futures.ThreadPoolExecutor(max_workers=settings.MAX_CONCURRENT_DOWNLOADS)


async def process_queue():
    """Processa itens da fila"""
    while is_running:
        try:
            # Verificar se pode processar mais downloads
            if len(active_tasks) >= settings.MAX_CONCURRENT_DOWNLOADS:
                await asyncio.sleep(1)
                continue

            # Buscar próximo item pendente
            item = await queue_service.get_next_pending()
            if not item:
                await asyncio.sleep(1)
                continue

            # Processar em background
            task = asyncio.create_task(process_item(item))
            active_tasks[item.id] = task

        except Exception as e:
            print(f"Erro no worker: {e}")
            await asyncio.sleep(1)


async def process_item(item):
    """Processa um item individual"""
    try:
        async def on_progress(updated_item):
            await broadcast_item_update(updated_item)
            stats = await queue_service.get_stats()
            await broadcast_stats_update(stats)

        await process_download(item, on_progress)
    except asyncio.CancelledError:
        # Item foi cancelado - não faz nada, já foi removido
        pass
    finally:
        active_tasks.pop(item.id, None)


async def cancel_download(item_id: str) -> bool:
    """Cancela um download em andamento"""
    task = active_tasks.get(item_id)
    if task and not task.done():
        task.cancel()
        return True
    return False


async def cancel_all_downloads():
    """Cancela todos os downloads em andamento"""
    for _item_id, task in list(active_tasks.items()):
        if not task.done():
            task.cancel()


async def start_worker():
    """Inicia o worker"""
    global is_running
    is_running = True
    await queue_service.connect()
    await process_queue()


def stop_worker():
    """Para o worker"""
    global is_running
    is_running = False
    executor.shutdown(wait=False)
