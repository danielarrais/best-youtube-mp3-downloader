# YT-MP3 Downloader

Aplicação web para download e conversão de vídeos do YouTube para MP3.

## Arquitetura

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

## Uso com Docker

```bash
# Iniciar aplicação
docker-compose up -d

# Acessar interface
# http://localhost:3000
```

## Uso CLI (original)

```bash
# Instalar dependências
pip install -r requirements.txt

# Baixar de arquivo de URLs
python main.py -f musics.txt -q 192k

# Baixar playlist
python main.py -p "URL_DA_PLAYLIST" -q 320k
```

## Funcionalidades

- Interface web moderna com React
- Progresso em tempo real via WebSocket
- Fila de downloads com Redis
- Múltiplos downloads simultâneos
- Qualidade configurável (128k, 192k, 320k)
- Docker para fácil deploy

## Variáveis de Ambiente

```env
# Backend
DEBUG=false
DOWNLOAD_DIR=/app/downloads
DEFAULT_QUALITY=192k
MAX_CONCURRENT_DOWNLOADS=3
REDIS_URL=redis://redis:6379/0

# Frontend (build time)
VITE_API_URL=http://localhost:3000
```
