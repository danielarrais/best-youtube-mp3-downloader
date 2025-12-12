from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App
    APP_NAME: str = "YT-MP3 Downloader"
    DEBUG: bool = False

    # Paths
    DOWNLOAD_DIR: str = "/app/downloads"
    TEMP_DIR: str = "/tmp/yt-mp3-downloader"

    # FFmpeg
    FFMPEG_PATH: str = "/usr/bin/ffmpeg"
    FFPROBE_PATH: str = "/usr/bin/ffprobe"

    # Download settings
    DEFAULT_QUALITY: str = "192k"
    MAX_RETRIES: int = 3
    RETRY_DELAY: int = 5
    MAX_CONCURRENT_DOWNLOADS: int = 3

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]

    class Config:
        env_file = ".env"


settings = Settings()
