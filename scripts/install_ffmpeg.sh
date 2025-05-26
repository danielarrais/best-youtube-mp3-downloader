#!/bin/bash

# Detect operating system
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if [ -f /etc/debian_version ]; then
        # Debian/Ubuntu
        echo "Installing FFmpeg on Debian/Ubuntu..."
        sudo apt update
        sudo apt install -y ffmpeg
    elif [ -f /etc/fedora-release ]; then
        # Fedora
        echo "Installing FFmpeg on Fedora..."
        sudo dnf install -y ffmpeg
    elif [ -f /etc/arch-release ]; then
        # Arch Linux
        echo "Installing FFmpeg on Arch Linux..."
        sudo pacman -S --noconfirm ffmpeg
    else
        echo "Unsupported Linux distribution. Please install FFmpeg manually."
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew &> /dev/null; then
        echo "Installing FFmpeg on macOS..."
        brew install ffmpeg
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    if command -v choco &> /dev/null; then
        echo "Installing FFmpeg on Windows..."
        choco install ffmpeg -y
    else
        echo "Chocolatey not found. Please install Chocolatey first:"
        echo "https://chocolatey.org/install"
        exit 1
    fi
else
    echo "Unsupported operating system. Please install FFmpeg manually."
    exit 1
fi

# Verify installation
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg installed successfully!"
    ffmpeg -version | head -n 1
else
    echo "❌ FFmpeg installation failed. Please install manually."
    exit 1
fi 