import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.config import settings

router = APIRouter()


@router.get("")
async def list_files() -> list[dict]:
    """Lista arquivos MP3 baixados"""
    files = []
    if os.path.exists(settings.DOWNLOAD_DIR):
        for filename in os.listdir(settings.DOWNLOAD_DIR):
            if filename.endswith('.mp3'):
                filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
                files.append({
                    "filename": filename,
                    "size": os.path.getsize(filepath)
                })
    return files


@router.get("/{filename}")
async def download_file(filename: str):
    """Download de arquivo MP3"""
    filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(filepath, filename=filename, media_type="audio/mpeg")


@router.delete("/{filename}")
async def delete_file(filename: str):
    """Remove arquivo MP3"""
    filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    os.remove(filepath)
    return {"message": "Arquivo removido"}


@router.delete("")
async def delete_all_files():
    """Remove todos os arquivos MP3"""
    deleted = 0
    if os.path.exists(settings.DOWNLOAD_DIR):
        for filename in os.listdir(settings.DOWNLOAD_DIR):
            if filename.endswith('.mp3'):
                filepath = os.path.join(settings.DOWNLOAD_DIR, filename)
                try:
                    os.remove(filepath)
                    deleted += 1
                except OSError:
                    pass
    return {"message": f"{deleted} arquivos removidos"}
