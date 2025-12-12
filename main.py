#!/usr/bin/env python3
import os
import sys
import time
import argparse
import re
import shutil
import subprocess
from pytubefix import YouTube, Playlist


def get_ffmpeg_path():
    """Get the path to the embedded ffmpeg binary or system ffmpeg"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
        # Determine the correct ffmpeg binary name based on platform
        if sys.platform == 'win32':
            ffmpeg_name = 'ffmpeg.exe'
        else:
            ffmpeg_name = 'ffmpeg'
        
        ffmpeg_path = os.path.join(base_path, ffmpeg_name)
        
        # Make sure the binary is executable on Unix-like systems
        if sys.platform != 'win32' and os.path.exists(ffmpeg_path):
            os.chmod(ffmpeg_path, 0o755)
        
        return ffmpeg_path
    else:
        # Running as script - try to find ffmpeg in project directory first
        base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Determine the correct ffmpeg binary name based on platform
        if sys.platform == 'win32':
            ffmpeg_name = 'ffmpeg.exe'
        else:
            ffmpeg_name = 'ffmpeg'
        
        ffmpeg_path = os.path.join(base_path, ffmpeg_name)
        
        # If ffmpeg exists in project directory, use it
        if os.path.exists(ffmpeg_path):
            # Make sure the binary is executable on Unix-like systems
            if sys.platform != 'win32':
                os.chmod(ffmpeg_path, 0o755)
            return ffmpeg_path
        
        # Otherwise, try to use system ffmpeg
        system_ffmpeg = shutil.which('ffmpeg')
        if system_ffmpeg:
            return system_ffmpeg
        
        # If no ffmpeg found, raise an error
        raise FileNotFoundError(
            "FFmpeg not found. Please install FFmpeg:\n"
            "  - Linux: sudo apt install ffmpeg (or use your package manager)\n"
            "  - macOS: brew install ffmpeg\n"
            "  - Windows: Download from https://ffmpeg.org/download.html\n"
            "Or run: bash scripts/install_ffmpeg.sh"
        )


# Caminho do ffmpeg (configurado uma vez)
FFMPEG_PATH = get_ffmpeg_path()
FFPROBE_PATH = FFMPEG_PATH.replace('ffmpeg', 'ffprobe')

# Largura fixa para limpar linha de progresso
CLEAR_LINE = "\r" + " " * 80 + "\r"


def print_progress(text):
    """Imprime progresso na mesma linha, limpando antes"""
    print(f"{CLEAR_LINE}{text}", end="", flush=True)


def print_progress_done(text):
    """Imprime progresso finalizado e vai para próxima linha"""
    print(f"{CLEAR_LINE}{text}")


def parse_arguments():
    parser = argparse.ArgumentParser(description='Download and convert YouTube videos to MP3')
    parser.add_argument('-q', '--quality', type=str, default='128k',
                      help='Audio quality in kbps (ex: 128k, 192k, 320k)')
    parser.add_argument('-f', '--file', type=str, default='musics.txt',
                      help='File containing YouTube URLs (one per line)')
    parser.add_argument('-p', '--playlist', type=str,
                      help='YouTube playlist URL to download')
    parser.add_argument('-r', '--retries', type=int, default=3,
                      help='Number of download attempts (default: 3)')
    parser.add_argument('-d', '--delay', type=int, default=5,
                      help='Wait time between attempts in seconds (default: 5)')
    return parser.parse_args()


def read_urls_from_file(filename):
    urls = set()
    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    urls.add(line)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        print("Create a 'musics.txt' file with YouTube URLs (one per line).")
        exit(1)
    return list(urls)


def extract_playlist_urls(playlist_url):
    """Extracts video URLs from a YouTube playlist"""
    try:
        playlist = Playlist(playlist_url)
        print(f"\nPlaylist found: {playlist.title}")
        print(f"Total videos in playlist: {len(playlist.video_urls)}")
        return list(playlist.video_urls)
    except Exception as e:
        print(f"Error extracting playlist URLs: {str(e)}")
        return []


def sanitize_filename(filename):
    # Remove invalid characters for filenames
    return re.sub(r'[\\/*?:"<>|]', "_", filename)


def format_size(bytes_value):
    """Formata bytes para exibição legível"""
    if bytes_value < 1024:
        return f"{bytes_value} B"
    elif bytes_value < 1024 * 1024:
        return f"{bytes_value / 1024:.1f} KB"
    else:
        return f"{bytes_value / (1024 * 1024):.2f} MB"


def format_speed(bytes_per_second):
    """Formata velocidade para exibição legível"""
    if bytes_per_second < 1024:
        return f"{bytes_per_second:.0f} B/s"
    elif bytes_per_second < 1024 * 1024:
        return f"{bytes_per_second / 1024:.1f} KB/s"
    else:
        return f"{bytes_per_second / (1024 * 1024):.2f} MB/s"


def download_video(url, quality, max_retries=3, delay=5, download_dir="downloads"):
    """Baixa e converte um vídeo do YouTube para MP3"""
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"\n{'='*60}")
            print(f"📎 URL: {url}")
            
            if attempt > 1:
                print(f"🔄 Tentativa {attempt}/{max_retries}")
            
            # Obter informações do vídeo
            print("📡 Obtendo informações do vídeo...")
            yt = YouTube(url)
            title = yt.title
            safe_title = sanitize_filename(title)
            mp3_path = os.path.join(download_dir, f"{safe_title}.mp3")
            
            print(f"🎵 Título: {title}")
            print(f"📁 Saída: {mp3_path}")
            
            # Verificar se já existe
            if os.path.exists(mp3_path):
                print(f"⏭️  Arquivo já existe, pulando...")
                return {"success": True, "status": "skipped", "title": title, "path": mp3_path}
            
            # Obter stream de áudio
            print("🔍 Buscando stream de áudio...")
            audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                print("❌ Nenhum stream de áudio encontrado!")
                return {"success": False, "url": url, "error": "Sem stream de áudio"}
            
            file_size_mb = audio_stream.filesize / (1024 * 1024)
            print(f"📦 Tamanho do stream: {file_size_mb:.2f} MB")
            
            # Download para diretório temporário
            print("📥 Baixando áudio...")
            temp_dir = "/tmp/yt-mp3-downloader"
            os.makedirs(temp_dir, exist_ok=True)
            temp_file_path = os.path.join(temp_dir, f"{safe_title}.tmp")
            
            # Remover arquivo temporário se já existir
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                print("   🗑️  Arquivo temporário anterior removido")
            
            # Variáveis para progresso do download
            file_size = audio_stream.filesize
            download_start_time = time.time()
            last_bytes = [0]
            last_time = [download_start_time]
            
            def on_progress(stream, chunk, bytes_remaining):
                """Callback de progresso do download"""
                current_time = time.time()
                bytes_downloaded = file_size - bytes_remaining
                percent = (bytes_downloaded / file_size) * 100
                
                # Calcular velocidade
                time_diff = current_time - last_time[0]
                if time_diff > 0.5:  # Atualizar a cada 0.5s
                    bytes_diff = bytes_downloaded - last_bytes[0]
                    speed = bytes_diff / time_diff
                    last_bytes[0] = bytes_downloaded
                    last_time[0] = current_time
                    
                    # Exibir progresso
                    print_progress(f"   📥 {percent:.1f}% | {format_size(bytes_downloaded)}/{format_size(file_size)} | {format_speed(speed)}")
            
            yt.register_on_progress_callback(on_progress)
            
            start_download = time.time()
            temp_file = audio_stream.download(output_path=temp_dir, filename=f"{safe_title}.tmp")
            download_time = time.time() - start_download
            print_progress_done(f"   📥 100% | {format_size(file_size)} | Concluído em {download_time:.1f}s")
            print(f"📄 Arquivo temporário: {temp_file}")
            
            # Conversão usando ffmpeg
            print(f"\n🔄 Convertendo para MP3 ({quality})...")
            print(f"   Entrada: {os.path.basename(temp_file)}")
            print(f"   Saída: {os.path.basename(mp3_path)}")
            
            start_convert = time.time()
            
            # Obter duração do arquivo usando ffprobe
            try:
                duration_cmd = [
                    FFPROBE_PATH, '-v', 'error',
                    '-show_entries', 'format=duration',
                    '-of', 'default=noprint_wrappers=1:nokey=1',
                    temp_file
                ]
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True)
                duration_seconds = float(duration_result.stdout.strip())
            except:
                duration_seconds = 0
            
            if duration_seconds > 0:
                duration_hours = int(duration_seconds // 3600)
                duration_min = int((duration_seconds % 3600) // 60)
                duration_sec = int(duration_seconds % 60)
                if duration_hours > 0:
                    print(f"   Duração: {duration_hours}h {duration_min}m {duration_sec}s")
                else:
                    print(f"   Duração: {duration_min}m {duration_sec}s")
            
            # Converter usando ffmpeg diretamente com progresso
            bitrate_num = int(re.sub(r'[^0-9]', '', quality))
            
            # Comando ffmpeg com progresso e multi-threading
            ffmpeg_cmd = [
                FFMPEG_PATH,
                '-i', temp_file,
                '-vn',  # Sem vídeo
                '-acodec', 'libmp3lame',
                '-ab', quality,
                '-threads', '0',  # 0 = usar todos os cores disponíveis
                '-y',  # Sobrescrever sem perguntar
                '-progress', 'pipe:1',  # Progresso para stdout
                '-nostats',
                mp3_path
            ]
            
            print(f"   Convertendo...")
            
            # Executar ffmpeg e monitorar progresso
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            current_time_us = 0
            total_duration_us = int(duration_seconds * 1_000_000) if duration_seconds > 0 else 0
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line.startswith('out_time_us='):
                    try:
                        current_time_us = int(line.split('=')[1].strip())
                        if total_duration_us > 0:
                            percent = min((current_time_us / total_duration_us) * 100, 99.9)
                            current_sec = current_time_us / 1_000_000
                            current_min = int(current_sec // 60)
                            current_sec_rem = int(current_sec % 60)
                            total_min = int(duration_seconds // 60)
                            total_sec_rem = int(duration_seconds % 60)
                            print_progress(f"   🔄 {percent:.1f}% | {current_min}:{current_sec_rem:02d}/{total_min}:{total_sec_rem:02d}")
                    except:
                        pass
            
            # Verificar se ffmpeg terminou com sucesso
            return_code = process.wait()
            stderr_output = process.stderr.read()
            
            if return_code != 0:
                print_progress_done("")  # Limpar linha de progresso
                print(f"❌ Erro na conversão ffmpeg (código {return_code})")
                print(f"   Detalhes: {stderr_output[:500]}")
                raise Exception(f"ffmpeg falhou com código {return_code}: {stderr_output[:200]}")
            
            convert_time = time.time() - start_convert
            
            # Verificar se o arquivo foi criado
            if not os.path.exists(mp3_path):
                raise Exception("Arquivo MP3 não foi criado")
            
            # Tamanho final
            final_size = os.path.getsize(mp3_path)
            print_progress_done(f"   🔄 100% | {format_size(final_size)} | Concluído em {convert_time:.1f}s")
            print(f"✅ Conversão concluída!")
            
            # Limpar arquivo temporário
            os.remove(temp_file)
            print("🗑️  Arquivo temporário removido")
            
            return {"success": True, "title": title, "path": mp3_path}
            
        except Exception as e:
            print_progress_done("")  # Limpar linha de progresso se houver
            print(f"❌ Erro: {str(e)}")
            
            if attempt < max_retries:
                print(f"⏳ Aguardando {delay}s antes de tentar novamente...")
                time.sleep(delay)
            else:
                return {"success": False, "url": url, "error": str(e)}
    
    return {"success": False, "url": url, "error": "Máximo de tentativas excedido"}


def get_playlist_name(playlist_url):
    """Extract playlist name from URL or use a default name."""
    try:
        playlist = Playlist(playlist_url)
        # Sanitize playlist name for filesystem
        name = "".join(c for c in playlist.title if c.isalnum() or c in (' ', '-', '_')).strip()
        return name if name else "playlist"
    except Exception:
        return "playlist"


def ensure_download_dir(playlist_name=None):
    """Create and return the download directory path."""
    base_dir = "downloads"
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
    
    if playlist_name:
        playlist_dir = os.path.join(base_dir, playlist_name)
        if not os.path.exists(playlist_dir):
            os.makedirs(playlist_dir)
        return playlist_dir
    return base_dir


def main():
    args = parse_arguments()
    
    # Obter URLs
    if args.playlist:
        links = extract_playlist_urls(args.playlist)
        playlist_name = get_playlist_name(args.playlist)
        download_dir = ensure_download_dir(playlist_name)
    else:
        links = read_urls_from_file(args.file)
        download_dir = ensure_download_dir()
    
    if not links:
        print("❌ Nenhuma URL encontrada.")
        return
    
    total = len(links)
    start_time = time.time()
    results = {"success": 0, "failed": 0, "skipped": 0}
    
    print("\n" + "="*60)
    print("🎵 YT-MP3 Downloader")
    print("="*60)
    print(f"📊 Total de vídeos: {total}")
    print(f"🎚️  Qualidade: {args.quality}")
    print(f"🔁 Tentativas: {args.retries}")
    print(f"📁 Diretório: {download_dir}")
    
    # Processar um por vez
    for i, url in enumerate(links, 1):
        print(f"\n[{i}/{total}] Processando...")
        
        result = download_video(
            url=url,
            quality=args.quality,
            max_retries=args.retries,
            delay=args.delay,
            download_dir=download_dir
        )
        
        if result["success"]:
            if result.get("status") == "skipped":
                results["skipped"] += 1
            else:
                results["success"] += 1
        else:
            results["failed"] += 1
    
    # Resumo final
    elapsed = time.time() - start_time
    print("\n" + "="*60)
    print("📋 RESUMO FINAL")
    print("="*60)
    print(f"✅ Baixados: {results['success']}/{total}")
    print(f"⏭️  Pulados: {results['skipped']}/{total}")
    print(f"❌ Falhas: {results['failed']}/{total}")
    print(f"⏱️  Tempo total: {elapsed:.1f}s")
    print(f"📁 Arquivos em: {download_dir}")
    print("="*60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro inesperado: {str(e)}")
        sys.exit(1)
