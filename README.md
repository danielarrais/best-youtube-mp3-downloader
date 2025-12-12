# YouTube to MP3 Downloader - Free Online Converter

A free, open-source web application to download and convert YouTube videos to MP3 audio files. Features a modern React frontend, FastAPI backend, and Docker support for easy deployment.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<img width="1134" height="690" alt="image" src="https://github.com/user-attachments/assets/165bc6c4-7c89-4b3a-a64d-e44fd129d153" />

## Features

- 🎵 **YouTube to MP3 Conversion** - Convert any YouTube video to high-quality MP3
- 📋 **Playlist Support** - Download entire YouTube playlists at once
- ⚡ **Real-time Progress** - Live download progress via WebSocket
- 🔄 **Queue System** - Redis-powered download queue with concurrent downloads
- 🎚️ **Quality Options** - Choose between 128kbps, 192kbps, or 320kbps
- 🌐 **Multi-language** - Interface available in English and Portuguese
- 🐳 **Docker Ready** - One-command deployment with Docker Compose
- 📱 **Responsive UI** - Modern React interface works on desktop and mobile

## Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/yourusername/yt-mp3-downloader.git
cd yt-mp3-downloader

# Start the application
docker compose up -d

# Open in browser
# http://localhost:3000
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend      │────▶│   Backend API   │────▶│   Redis Queue   │
│   (React)       │ WS  │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Downloads     │
                        │   (Volume)      │
                        └─────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|------------|
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| Backend | Python 3.11, FastAPI, Pydantic |
| Queue | Redis |
| Audio | FFmpeg, pytubefix |
| Deploy | Docker, Docker Compose, Nginx |

## CLI Usage (Standalone)

You can also use the original CLI tool without Docker:

```bash
# Install dependencies
pip install -r requirements.txt

# Download from a file with URLs
python main.py -f musics.txt -q 192k

# Download a playlist
python main.py -p "PLAYLIST_URL" -q 320k
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEBUG` | `false` | Enable debug mode |
| `DOWNLOAD_DIR` | `/app/downloads` | Directory for downloaded files |
| `DEFAULT_QUALITY` | `192k` | Default audio quality |
| `MAX_CONCURRENT_DOWNLOADS` | `3` | Maximum parallel downloads |
| `REDIS_URL` | `redis://redis:6379/0` | Redis connection URL |

## Development

```bash
# Backend
cd backend
pip install -r ../requirements.txt
uvicorn backend.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/downloads` | Add URLs to download queue |
| `GET` | `/api/downloads` | List all downloads |
| `DELETE` | `/api/downloads/{id}` | Cancel/remove a download |
| `POST` | `/api/downloads/{id}/retry` | Retry a failed download |
| `GET` | `/api/queue/stats` | Get queue statistics |
| `POST` | `/api/queue/clear` | Clear completed downloads |
| `GET` | `/api/files` | List downloaded MP3 files |
| `GET` | `/api/files/{filename}` | Download an MP3 file |
| `WS` | `/ws` | WebSocket for real-time updates |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for personal use only. Respect YouTube's Terms of Service and copyright laws. Only download content you have permission to download.

---

**Keywords**: youtube to mp3, youtube mp3 converter, youtube downloader, mp3 converter, audio extractor, youtube audio download, free youtube converter, open source youtube downloader
