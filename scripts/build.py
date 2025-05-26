#!/usr/bin/env python3
import os
import platform
import subprocess
import shutil

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
    
    # Build command
    cmd = [
        'pyinstaller',
        '--onefile',
        '--name', 'yt-mp3-downloader',
        'main.py'
    ]
    
    # Run PyInstaller
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
    print("🚀 Building executable...")
    build_executable()

if __name__ == "__main__":
    main() 