import os

import redis.asyncio as redis

from backend.config import settings
from backend.models.download import DownloadItem, DownloadStatus, QueueStats

QUEUE_KEY = "download_queue"
ITEM_PREFIX = "download_item:"


def delete_file(file_path: str | None):
    """Remove arquivo do disco se existir"""
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


class QueueService:
    def __init__(self):
        self.redis: redis.Redis | None = None

    async def connect(self):
        if not self.redis:
            self.redis = redis.from_url(settings.REDIS_URL)

    async def disconnect(self):
        if self.redis:
            await self.redis.close()

    async def add_to_queue(self, items: list[DownloadItem]) -> list[DownloadItem]:
        """Adiciona itens à fila"""
        for item in items:
            await self.redis.hset(
                f"{ITEM_PREFIX}{item.id}",
                mapping={"data": item.model_dump_json()}
            )
            await self.redis.rpush(QUEUE_KEY, item.id)
        return items

    async def get_queue(self) -> list[DownloadItem]:
        """Retorna todos os itens da fila"""
        item_ids = await self.redis.lrange(QUEUE_KEY, 0, -1)
        items = []
        for item_id in item_ids:
            item = await self.get_item(item_id.decode() if isinstance(item_id, bytes) else item_id)
            if item:
                items.append(item)
        return items

    async def get_item(self, item_id: str) -> DownloadItem | None:
        """Retorna um item específico"""
        data = await self.redis.hget(f"{ITEM_PREFIX}{item_id}", "data")
        if data:
            return DownloadItem.model_validate_json(data)
        return None

    async def update_item(self, item_id: str, item: DownloadItem):
        """Atualiza um item"""
        await self.redis.hset(
            f"{ITEM_PREFIX}{item_id}",
            mapping={"data": item.model_dump_json()}
        )

    async def remove_item(self, item_id: str):
        """Remove um item da fila"""
        await self.redis.lrem(QUEUE_KEY, 0, item_id)
        await self.redis.delete(f"{ITEM_PREFIX}{item_id}")

    async def get_next_pending(self) -> DownloadItem | None:
        """Retorna o próximo item pendente"""
        items = await self.get_queue()
        for item in items:
            if item.status == DownloadStatus.PENDING:
                return item
        return None

    async def get_stats(self) -> QueueStats:
        """Retorna estatísticas da fila"""
        items = await self.get_queue()
        return QueueStats(
            total=len(items),
            pending=len([i for i in items if i.status == DownloadStatus.PENDING]),
            downloading=len([i for i in items if i.status in [DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING, DownloadStatus.FETCHING_INFO]]),
            completed=len([i for i in items if i.status == DownloadStatus.COMPLETED]),
            failed=len([i for i in items if i.status == DownloadStatus.FAILED])
        )

    async def clear_completed(self):
        """Remove itens concluídos da fila"""
        items = await self.get_queue()
        for item in items:
            if item.status in [DownloadStatus.COMPLETED, DownloadStatus.SKIPPED]:
                delete_file(item.file_path)
                await self.remove_item(item.id)

    async def cancel_all(self):
        """Cancela todos os downloads pendentes"""
        from backend.workers.download_worker import cancel_all_downloads
        await cancel_all_downloads()

        items = await self.get_queue()
        for item in items:
            if item.status in [DownloadStatus.PENDING, DownloadStatus.FETCHING_INFO, DownloadStatus.DOWNLOADING, DownloadStatus.CONVERTING]:
                delete_file(item.file_path)
                await self.remove_item(item.id)

    async def clear_all(self):
        """Remove todos os itens da fila"""
        from backend.workers.download_worker import cancel_all_downloads
        await cancel_all_downloads()

        items = await self.get_queue()
        for item in items:
            delete_file(item.file_path)
            await self.remove_item(item.id)

        # Limpar todos os arquivos do disco
        if os.path.exists(settings.DOWNLOAD_DIR):
            for filename in os.listdir(settings.DOWNLOAD_DIR):
                if filename.endswith('.mp3'):
                    filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass


queue_service = QueueService()
