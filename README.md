# YouTube MP3 Downloader

Python script to download YouTube videos and convert them to MP3.

## Requirements

- Python 3.6 or higher
- Dependencies:
  - pytubefix
  - pydub
  - tqdm

## Installation

1. Clone the repository:
```bash
git clone https://github.com/danielarrais/best-youtube-mp3-downloader
cd best-youtube-mp3-downloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
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

MP3 files will be saved in the `downloads/` folder.

## Detailed Features

### Parallel Download
- Uses `ThreadPoolExecutor` for simultaneous downloads
- Maximum workers limited to 5 to prevent overload
- Optimized for better performance and stability

### Retry System
- Automatic retries on failure
- Configurable wait time between attempts
- Specific handling for network errors
- Detailed feedback on attempts and errors

### File Handling
- Automatic filename sanitization
- Duplicate file detection
- Automatic temporary file cleanup
- Dedicated folder organization
- Support for text files with URLs
- Automatic playlist folder organization

### Metadata
- Music title
- Artist/channel name
- Configurable audio quality

### Feedback and Monitoring
- Real-time progress bar
- Detailed statistics:
  - Total downloads
  - Successful downloads
  - Skipped files (already exist)
  - Failures
  - Total processing time
- Informative messages about attempts and errors
- Detailed summary at the end of the process

## Customization

### Change Audio Quality
You can specify audio quality in two ways:

1. Via command line:
```bash
python main.py -q 320k
# or
python playlist_downloader.py "PLAYLIST_URL" -q 320k
```

2. By modifying the code:
```python
audio.export(mp3_path, format="mp3", bitrate="320k")
```

### Configure Retries
Adjust number of attempts and wait time:
```bash
python main.py -r 5 -d 10
# or
python playlist_downloader.py "PLAYLIST_URL" -r 5 -d 10
```

### Change Output Directory
For playlists, use the `-o` parameter:
```bash
python playlist_downloader.py "PLAYLIST_URL" -o "My Playlist"
```

### Adjust Parallel Downloads
Modify the `max_workers` variable:
```python
max_workers = min(5, len(links))
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
   - Verify if all dependencies are installed
   - Check if there's enough disk space

3. **URL file not found**
   - Make sure `musics.txt` exists
   - Verify if the file path is correct
   - Use `-f` parameter to specify a different file

4. **Downloads stopping unexpectedly**
   - Reduce number of parallel downloads
   - Increase wait time between attempts
   - Check your internet connection
   - Use `-r` parameter to increase retry attempts

5. **Playlist download error**
   - Verify if the playlist URL is correct
   - Make sure the playlist is public
   - Check if you have permission to access the playlist

### Logs and Debug
- Script displays detailed messages for each operation
- Errors are caught and displayed with corresponding URL
- Final statistics show complete process results
- Information about attempts and wait times is displayed

## Contributing

Contributions are welcome! Feel free to open issues or send pull requests.

## License

This project is distributed under the MIT license. 