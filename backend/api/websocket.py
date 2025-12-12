import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.models.download import DownloadItem, QueueStats

router = APIRouter()

# Lista de conexões ativas
connections: list[WebSocket] = []


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            # Mantém a conexão aberta
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.remove(websocket)


async def broadcast_item_update(item: DownloadItem):
    """Envia atualização de item para todos os clientes"""
    message = {
        "type": "download:update",
        "data": json.loads(item.model_dump_json())
    }
    await broadcast(message)


async def broadcast_stats_update(stats: QueueStats):
    """Envia atualização de estatísticas para todos os clientes"""
    message = {
        "type": "queue:stats",
        "data": json.loads(stats.model_dump_json())
    }
    await broadcast(message)


async def broadcast(message: dict):
    """Envia mensagem para todos os clientes conectados"""
    disconnected = []
    for connection in connections:
        try:
            await connection.send_json(message)
        except Exception:
            disconnected.append(connection)

    # Remove conexões desconectadas
    for conn in disconnected:
        if conn in connections:
            connections.remove(conn)
