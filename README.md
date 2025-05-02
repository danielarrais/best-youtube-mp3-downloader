# YouTube MP3 Downloader

Ferramentas simples para baixar músicas do YouTube e convertê-las em arquivos MP3.

## Requisitos

- Python 3.6 ou superior
- Dependências listadas em `requirements.txt`
- FFmpeg (para o script `ytmp3_ffmpeg.py`)

## Instalação

1. Clone o repositório ou baixe os arquivos
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Para o script `ytmp3_ffmpeg.py`, instale o FFmpeg:
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - Fedora/RHEL: `sudo dnf install ffmpeg`
   - Windows: [Baixe aqui](https://ffmpeg.org/download.html)

## Scripts Disponíveis

### 1. yt_mp3_downloader.py (Recomendado)

Script moderno que usa `pytubefix` e processamento paralelo para downloads mais rápidos.

**Recursos:**
- Download paralelo (múltiplos vídeos simultaneamente)
- Qualidade de áudio configurável (128kbps padrão)
- Metadados da música (título, artista)
- Interface com barra de progresso

**Uso:**
```bash
python yt_mp3_downloader.py
```

### 2. ytmp3_ffmpeg.py (Alternativa)

Script baseado em `yt-dlp` e FFmpeg.

**Recursos:**
- Download sequencial
- Qualidade de áudio média (configurável)
- Incorporação de metadados e capas de álbum
- Interface com barra de progresso

**Uso:**
```bash
python ytmp3_ffmpeg.py
```

## Personalização

### Adicionar novos vídeos

Edite a lista `links` em qualquer um dos scripts para adicionar/remover URLs do YouTube.

### Alterar a qualidade do áudio

- Em `yt_mp3_downloader.py`: modifique o parâmetro `bitrate` na função `audio.export()` 
- Em `ytmp3_ffmpeg.py`: altere o valor do parâmetro `--audio-quality` (0=melhor, 9=pior)

### Alterar o diretório de saída

Modifique a variável `output_folder` em qualquer um dos scripts.

## Solução de Problemas

### Erro HTTP 400

Se encontrar erro "HTTP Error 400: Bad Request", certifique-se de usar o script `yt_mp3_downloader.py` com a biblioteca `pytubefix`.

### Problemas com caracteres especiais nos nomes de arquivos

Ambos os scripts possuem funções para sanitizar os nomes dos arquivos e remover caracteres problemáticos.

## Licença

Este projeto é distribuído sob a licença MIT. 