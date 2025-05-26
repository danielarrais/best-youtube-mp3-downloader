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

def download_with_retry(url, quality, max_retries=3, delay=5):
    """Attempts to download the video with retries in case of failure"""
    for attempt in range(max_retries):
        try:
            # Create YouTube object
            yt = YouTube(url)
            
            # Get video title
            title = yt.title
            safe_title = sanitize_filename(title)
            mp3_path = os.path.join(output_folder, f"{safe_title}.mp3")
            
            # Check if file already exists
            if os.path.exists(mp3_path):
                skip_reason = get_skip_reason(url, mp3_path)
                return {
                    "success": True, 
                    "title": title, 
                    "status": "skipped",
                    "reason": skip_reason,
                    "path": mp3_path
                }
            
            # Download only the audio stream with best quality
            audio_stream = yt.streams.filter(only_audio=True).first()
            if not audio_stream:
                raise Exception("No audio stream found")
                
            temp_file = audio_stream.download(output_path=output_folder, filename=f"{safe_title}.tmp")
            
            # Convert to MP3 using pydub
            audio = AudioSegment.from_file(temp_file)
            
            # Export with specified quality
            audio.export(mp3_path, format="mp3", bitrate=quality, 
                        tags={
                            "title": title,
                            "artist": yt.author
                        })
            
            # Remove temporary file
            if os.path.exists(temp_file):
                os.remove(temp_file)
                
            return {"success": True, "title": title, "status": "downloaded"}
            
        except (HTTPError, URLError, socket.error) as e:
            if attempt < max_retries - 1:
                wait_time = delay + random.uniform(0, 2)  # Add some randomness
                print(f"\nNetwork error downloading {url}. Attempt {attempt + 1}/{max_retries}")
                print(f"Waiting {wait_time:.1f} seconds before trying again...")
                time.sleep(wait_time)
                continue
            return {"success": False, "url": url, "error": f"Network error after {max_retries} attempts: {str(e)}"}
            
        except Exception as e:
            return {"success": False, "url": url, "error": str(e)}

def main():
    # Parse arguments
    args = parse_arguments()
    
    # Get URLs from file or playlist
    if args.playlist:
        links = extract_playlist_urls(args.playlist)
    else:
        links = read_urls_from_file(args.file)
    
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
    print(f"Wait time between attempts: {args.delay} seconds\n")

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
                    args.delay
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

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        sys.exit(1) 