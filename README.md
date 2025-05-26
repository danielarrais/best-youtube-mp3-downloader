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

## Features

- Parallel downloads (up to 5 simultaneous)
- Automatic retries on failure
- Configurable audio quality
- Playlist support
- Progress bar and statistics
- Metadata preservation (title and artist)
- Automatic filename sanitization
- Duplicate file detection

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

## Contributing

Contributions are welcome! Feel free to open issues or send pull requests.

## License

This project is distributed under the MIT license. 