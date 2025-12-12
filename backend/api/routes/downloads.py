import os

from fastapi import APIRouter, HTTPException

from backend.models.download import DownloadItem, DownloadRequest, DownloadStatus
from backend.services.queue_service import queue_service
from backend.workers.download_worker import cancel_download as cancel_download_task

router = APIRouter()


@router.post("", response_model=list[DownloadItem])
async def add_downloads(request: DownloadRequest):
    """Adiciona URLs à fila de download"""
    items = [
        DownloadItem(url=url, quality=request.quality)
        for url in request.urls
    ]
    return await queue_service.add_to_queue(items)


@router.get("", response_model=list[DownloadItem])
async def get_downloads():
    """Lista todos os downloads"""
    return await queue_service.get_queue()


@router.get("/{item_id}", response_model=DownloadItem)
async def get_download(item_id: str):
    """Obtém detalhes de um download"""
    item = await queue_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Download não encontrado")
    return item


@router.delete("/{item_id}")
async def cancel_download(item_id: str):
    """Cancela/remove um download"""
    item = await queue_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Download não encontrado")

    # Cancelar task se estiver em andamento
    await cancel_download_task(item_id)

    # Remover arquivo
    if item.file_path and os.path.exists(item.file_path):
        try:
            os.remove(item.file_path)
        except OSError:
            pass

    # Remover da fila (sem atualizar status, só remove)
    await queue_service.remove_item(item_id)
    return {"message": "Download removido"}


@router.post("/{item_id}/retry", response_model=DownloadItem)
async def retry_download(item_id: str):
    """Retenta um download que falhou"""
    item = await queue_service.get_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Download não encontrado")

    if item.status not in [DownloadStatus.FAILED, DownloadStatus.CANCELLED]:
        raise HTTPException(status_code=400, detail="Só é possível retentar downloads que falharam")

    item.status = DownloadStatus.PENDING
    item.error = None
    item.attempt += 1
    await queue_service.update_item(item_id, item)
    return item
