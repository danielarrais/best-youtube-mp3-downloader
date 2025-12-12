import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DownloadStatus(str, Enum):
    PENDING = "pending"
    FETCHING_INFO = "fetching"
    DOWNLOADING = "downloading"
    CONVERTING = "converting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class DownloadProgress(BaseModel):
    percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed: str = ""
    eta: str = ""


class DownloadRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1)
    quality: str = "192k"


class DownloadItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: str | None = None
    status: DownloadStatus = DownloadStatus.PENDING
    progress: DownloadProgress = Field(default_factory=DownloadProgress)
    quality: str = "192k"
    file_path: str | None = None
    file_size: int | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    attempt: int = 1


class QueueStats(BaseModel):
    total: int
    pending: int
    downloading: int
    completed: int
    failed: int
