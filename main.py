#!/usr/bin/env python3
import os
import time
import concurrent.futures
import argparse
from pytubefix import YouTube, Playlist
from pydub import AudioSegment
from tqdm import tqdm
import re
import random
from urllib.error import HTTPError, URLError
import socket
import sys

def get_ffmpeg_path():
    """Get the path to the embedded ffmpeg binary"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = sys._MEIPASS
    else:
        # Running as script
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    # Determine the correct ffmpeg binary name based on platform
    if sys.platform == 'win32':
        ffmpeg_name = 'ffmpeg.exe'
    else:
        ffmpeg_name = 'ffmpeg'
    
    ffmpeg_path = os.path.join(base_path, ffmpeg_name)
    
    # Make sure the binary is executable on Unix-like systems
    if sys.platform != 'win32':
        os.chmod(ffmpeg_path, 0o755)
    
    return ffmpeg_path

# Configure pydub to use the embedded ffmpeg
AudioSegment.converter = get_ffmpeg_path()

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

# Output folder
output_folder = "downloads"
os.makedirs(output_folder, exist_ok=True)

# Function to sanitize filenames
def sanitize_filename(filename):
    # Remove invalid characters for filenames
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def get_skip_reason(url, mp3_path):
    """Determines why a music was skipped"""
    if os.path.exists(mp3_path):
        file_size = os.path.getsize(mp3_path)
        if file_size == 0:
            return "empty file"
        return "file already exists"
    return "unknown error"

def download_with_retry(url, quality, max_retries=3, delay=5, download_dir=None):
    """Attempts to download the video with retries in case of failure"""
    for attempt in range(max_retries):
        try:
            yt = YouTube(url)
            title = yt.title
            safe_title = sanitize_filename(title)
            
            # Use provided download directory or default to output_folder
            mp3_path = os.path.join(download_dir, f"{safe_title}.mp3") if download_dir else os.path.join(output_folder, f"{safe_title}.mp3")
            
            # Check if file already exists
            if os.path.exists(mp3_path):
                return {
                    "success": True,
                    "status": "skipped",
                    "title": title,
                    "reason": "File already exists"
                }

            # Get audio stream
            audio_stream = yt.streams.filter(only_audio=True).first()
            if not audio_stream:
                return {
                    "success": False,
                    "url": url,
                    "error": "No audio stream found"
                }

            # Download and convert
            temp_file = audio_stream.download()
            audio = AudioSegment.from_file(temp_file)
            
            # Convert to MP3 with specified quality
            audio.export(mp3_path, format="mp3", bitrate=quality)
            
            # Clean up temporary file
            os.remove(temp_file)
            
            return {
                "success": True,
                "title": title
            }
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(delay)
            else:
                return {
                    "success": False,
                    "url": url,
                    "error": str(e)
                }
    
    return {
        "success": False,
        "url": url,
        "error": "Max retries exceeded"
    }

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
    # Parse arguments
    args = parse_arguments()
    
    # Get URLs from file or playlist
    if args.playlist:
        links = extract_playlist_urls(args.playlist)
        playlist_name = get_playlist_name(args.playlist)
        download_dir = ensure_download_dir(playlist_name)
        print(f"\nDownloading playlist: {playlist_name}")
    else:
        links = read_urls_from_file(args.file)
        download_dir = ensure_download_dir()
    
    if not links:
        print("No URLs found. Add URLs to the file or provide a valid playlist.")
        return
    
    # Statistics counter
    total = len(links)
    start_time = time.time()

    # Initialize counters
    results = {"success": 0, "failed": 0, "skipped": 0}

    print(f"\nStarting download with audio quality: {args.quality}")
    print(f"Total URLs found: {total}")
    print(f"Number of attempts per download: {args.retries}")
    print(f"Wait time between attempts: {args.delay} seconds")
    print(f"Download directory: {download_dir}\n")

    # Use multithreading for parallel processing
    with tqdm(total=total, desc="Progress") as pbar:
        # Define number of workers (adjust based on your system)
        max_workers = min(5, len(links))  # Reduced to 5 to avoid overload
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(
                    download_with_retry, 
                    url, 
                    args.quality,
                    args.retries,
                    args.delay,
                    download_dir
                ): url for url in links
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                result = future.result()
                
                if result["success"]:
                    if result.get("status") == "skipped":
                        reason = result.get("reason", "unknown")
                        print(f"⏭ Skipped: {result['title']} - Reason: {reason}")
                        results["skipped"] += 1
                    else:
                        print(f"✓ Downloaded: {result['title']}")
                        results["success"] += 1
                else:
                    print(f"❌ Error: {result['error']} - {result['url']}")
                    results["failed"] += 1
                    
                pbar.update(1)

    # Final statistics
    elapsed_time = time.time() - start_time
    print(f"\nSummary:")
    print(f"✓ Downloaded: {results['success']} / {total}")
    print(f"⏭ Skipped: {results['skipped']} / {total}")
    print(f"❌ Failed: {results['failed']} / {total}")
    print(f"⏱️ Total time: {elapsed_time:.1f} seconds")
    print(f"📁 Files saved in: {download_dir}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1) 