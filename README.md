# YouTube MP3 Downloader

Python script to download YouTube videos and convert them to MP3. Organizes playlist downloads into separate folders.

## Features

- Download individual videos or entire playlists
- Automatic playlist folder organization
- Parallel downloads (up to 5 simultaneous)
- Automatic retries on failure
- Configurable audio quality
- Progress bar and statistics
- Metadata preservation (title and artist)
- Automatic filename sanitization
- Duplicate file detection
- No external dependencies required (FFmpeg included)

## Quick Start

### Using the Executable (Recommended)

1. Go to the [Releases](https://github.com/danielarrais/best-youtube-mp3-downloader/releases) page
2. Download the executable for your operating system:
   - Windows: `yt-mp3-downloader-windows.exe`
   - Linux: `yt-mp3-downloader-linux`
   - macOS: `yt-mp3-downloader-macos`
3. Make the file executable (Linux/macOS):
   ```bash
   chmod +x yt-mp3-downloader-linux  # or yt-mp3-downloader-macos
   ```
4. Run the program:
   ```bash
   # Windows
   yt-mp3-downloader-windows.exe -p "PLAYLIST_URL"
   
   # Linux/macOS
   ./yt-mp3-downloader-linux -p "PLAYLIST_URL"  # or yt-mp3-downloader-macos
   ```

### Using Python (Alternative)

1. Clone the repository:
```bash
git clone https://github.com/danielarrais/best-youtube-mp3-downloader
cd best-youtube-mp3-downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install FFmpeg:
   - Windows: `choco install ffmpeg`
   - macOS: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`

4. Run the script:
```bash
python main.py -p "PLAYLIST_URL"
```

## Usage

### Download via URL file
1. Create a `musics.txt` file with YouTube URLs (one per line)
2. Run:
```bash
python main.py
```

### Download via playlist
```bash
python main.py -p "PLAYLIST_URL"
```

### Options
- `-q, --quality`: Audio quality (128k, 192k, 320k)
- `-f, --file`: URL file (default: musics.txt)
- `-p, --playlist`: YouTube playlist URL
- `-r, --retries`: Number of retry attempts (default: 3)
- `-d, --delay`: Delay between retries in seconds (default: 5)

## Examples

```bash
# Download with 320k quality
python main.py -q 320k

# Download playlist with 5 retries
python main.py -p "PLAYLIST_URL" -r 5

# Use custom file
python main.py -f my_musics.txt
```

## File Organization

The script organizes downloaded files in the following structure:

```
downloads/
  ├── playlist1/          # Playlist downloads are organized in folders
  │   ├── song1.mp3
  │   ├── song2.mp3
  │   └── ...
  ├── playlist2/
  │   ├── song1.mp3
  │   └── ...
  └── individual_songs.mp3  # Individual downloads go directly in downloads/
```

## Troubleshooting

### Common Errors
1. **Download Error**
   - Check your internet connection
   - Verify if the YouTube URL is valid
   - Make sure the video is available
   - Increase number of retries with `-r`
   - Increase wait time with `-d`

2. **Conversion Error**
   - Check if there's enough disk space
   - If running from source, make sure FFmpeg is installed

3. **URL file not found**
   - Make sure `musics.txt` exists
   - Verify if the file path is correct
   - Use `-f` parameter to specify a different file

## Contributing

Contributions are welcome! Feel free to open issues or send pull requests.

## License

This project is distributed under the MIT license. 