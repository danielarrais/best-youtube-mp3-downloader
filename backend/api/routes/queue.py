from fastapi import APIRouter

from backend.models.download import QueueStats
from backend.services.queue_service import queue_service

router = APIRouter()


@router.get("/stats", response_model=QueueStats)
async def get_stats():
    """Retorna estatísticas da fila"""
    return await queue_service.get_stats()


@router.post("/clear")
async def clear_completed():
    """Limpa downloads concluídos"""
    await queue_service.clear_completed()
    return {"message": "Downloads concluídos removidos"}


@router.post("/cancel-all")
async def cancel_all():
    """Cancela todos os downloads pendentes"""
    await queue_service.cancel_all()
    return {"message": "Todos os downloads cancelados"}


@router.post("/clear-all")
async def clear_all():
    """Remove todos os downloads da fila"""
    await queue_service.clear_all()
    return {"message": "Fila limpa"}
