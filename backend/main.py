import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import downloads, files, queue
from backend.api.websocket import router as websocket_router
from backend.config import settings
from backend.workers.download_worker import start_worker, stop_worker


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: iniciar worker
    worker_task = asyncio.create_task(start_worker())
    yield
    # Shutdown: parar worker
    stop_worker()
    worker_task.cancel()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(downloads.router, prefix="/api/downloads", tags=["downloads"])
app.include_router(queue.router, prefix="/api/queue", tags=["queue"])
app.include_router(files.router, prefix="/api/files", tags=["files"])
app.include_router(websocket_router)


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
