#!/bin/bash
# setup.sh - One-shot installation script for Arabic Subtitle Tool

set -e  # Exit on any error

echo "🚀 Setting up Arabic Video Subtitle Tool..."

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "📋 Detected OS: $OS"

# Check Python version
python_cmd="python3"
if ! command -v python3 &> /dev/null; then
    if command -v python &> /dev/null; then
        python_cmd="python"
    else
        echo "❌ Python not found. Please install Python 3.9+ first."
        exit 1
    fi
fi

# Check Python version is 3.9+
python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ $(echo "$python_version < 3.9" | bc -l) ]]; then
    echo "❌ Python 3.9+ required. Found: $python_version"
    exit 1
fi

echo "✅ Python $python_version found"

# Create virtual environment
echo "📦 Creating virtual environment..."
$python_cmd -m venv .venv

# Activate virtual environment
if [[ "$OS" == "windows" ]]; then
    source .venv/Scripts/activate
else
    source .venv/bin/activate
fi

echo "✅ Virtual environment activated"

# Upgrade pip
echo "⬆️ Upgrading pip..."
python -m pip install --upgrade pip

# Install system dependencies based on OS
echo "🔧 Installing system dependencies..."

if [[ "$OS" == "linux" ]]; then
    # Try to detect package manager and install ffmpeg
    if command -v apt-get &> /dev/null; then
        echo "Installing dependencies with apt..."
        sudo apt-get update
        sudo apt-get install -y ffmpeg imagemagick fonts-noto-arabic
        # Fix ImageMagick policy for MoviePy
        sudo sed -i 's/rights="none" pattern="@\*"/rights="read|write" pattern="@*"/g' /etc/ImageMagick-6/policy.xml 2>/dev/null || true
    elif command -v yum &> /dev/null; then
        echo "Installing dependencies with yum..."
        sudo yum install -y ffmpeg ImageMagick google-noto-sans-arabic-fonts
    elif command -v pacman &> /dev/null; then
        echo "Installing dependencies with pacman..."
        sudo pacman -S --noconfirm ffmpeg imagemagick noto-fonts-arabic
    else
        echo "⚠️ Please install ffmpeg and imagemagick manually"
    fi
elif [[ "$OS" == "macos" ]]; then
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        echo "Installing dependencies with Homebrew..."
        brew install ffmpeg imagemagick
        # Install Arabic fonts
        brew tap homebrew/cask-fonts
        brew install --cask font-noto-sans-arabic
    else
        echo "⚠️ Please install Homebrew and then run: brew install ffmpeg imagemagick"
    fi
elif [[ "$OS" == "windows" ]]; then
    echo "⚠️ On Windows, please ensure you have:"
    echo "   - FFmpeg installed and in PATH"
    echo "   - ImageMagick installed"
    echo "   - Arabic fonts installed (Noto Sans Arabic, etc.)"
fi

# Install Python packages
echo "📚 Installing Python packages..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p assets/fonts
mkdir -p output
mkdir -p temp

# Download recommended fonts
echo "🔤 Setting up Arabic fonts..."
python -c "
from fonts import FontManager
fm = FontManager()
fm.setup_fonts()
print('✅ Arabic fonts setup complete')
"

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To run the application:"
echo "  1. Activate the virtual environment:"
if [[ "$OS" == "windows" ]]; then
    echo "     .venv\\Scripts\\activate"
else
    echo "     source .venv/bin/activate"
fi
echo "  2. Start the application:"
echo "     python app.py"
echo ""
echo "The web interface will be available at: http://127.0.0.1:7860"
echo ""
echo "For CLI usage, run: python app.py --help"
