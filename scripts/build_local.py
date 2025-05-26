#!/usr/bin/env python3
import os
import platform
import subprocess
import shutil

def get_ffmpeg_path():
    """Get the path to the system ffmpeg binary"""
    if platform.system() == 'Windows':
        return subprocess.check_output('where ffmpeg', shell=True).decode().strip()
    else:
        return subprocess.check_output('which ffmpeg', shell=True).decode().strip()

def clean_build():
    """Clean build directories"""
    dirs_to_clean = ['build', 'dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    if os.path.exists('yt-mp3-downloader.spec'):
        os.remove('yt-mp3-downloader.spec')

def build_executable():
    """Build executable for current platform"""
    system = platform.system().lower()
    
    # Clean previous builds
    clean_build()
    
    # Get ffmpeg path
    ffmpeg_path = get_ffmpeg_path()
    print(f"Found FFmpeg at: {ffmpeg_path}")
    
    # Build command
    if system == 'windows':
        cmd = [
            'pyinstaller',
            '--onefile',
            '--name', 'yt-mp3-downloader',
            f'--add-binary', f'{ffmpeg_path};.',
            'main.py'
        ]
    else:
        cmd = [
            'pyinstaller',
            '--onefile',
            '--name', 'yt-mp3-downloader',
            f'--add-binary', f'{ffmpeg_path}:.',
            'main.py'
        ]
    
    # Run PyInstaller
    print("\n🚀 Building executable...")
    subprocess.run(cmd, check=True)
    
    # Rename executable based on platform
    if system == 'windows':
        os.rename(
            'dist/yt-mp3-downloader.exe',
            'dist/yt-mp3-downloader-windows.exe'
        )
    elif system == 'darwin':  # macOS
        os.rename(
            'dist/yt-mp3-downloader',
            'dist/yt-mp3-downloader-macos'
        )
    else:  # Linux
        os.rename(
            'dist/yt-mp3-downloader',
            'dist/yt-mp3-downloader-linux'
        )
    
    print(f"\n✅ Executable built successfully for {system}")
    print(f"📦 Output: dist/yt-mp3-downloader-{system}")

def main():
    print("🔍 Checking system...")
    system = platform.system()
    print(f"Operating System: {system}")
    
    try:
        build_executable()
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Build failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 