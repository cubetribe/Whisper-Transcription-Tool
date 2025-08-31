#!/bin/bash

#########################################
# Whisper Transcription Tool
# Installation Script for macOS
# Version: 0.9.5.1
# Copyright © 2025 Dennis Westermann
#########################################

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_ROOT"

clear
echo "╔══════════════════════════════════════════════════════════╗"
echo "║     WHISPER TRANSCRIPTION TOOL - INSTALLATION           ║"
echo "║                   Version 0.9.5.1                        ║"
echo "║           Copyright © 2025 Dennis Westermann            ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installation script is designed for macOS only."
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Check Python version
print_status "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_success "Python $PYTHON_VERSION found"
    
    # Check if Python version is 3.8 or higher
    if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
        print_success "Python version is compatible"
    else
        print_error "Python 3.8 or higher is required"
        echo "Please upgrade Python and try again"
        echo "Press any key to exit..."
        read -n 1
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    echo "Please install Python 3.8 or higher from python.org"
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Step 1: Create virtual environment
print_status "Creating virtual environment..."
if [ -d "venv_new" ]; then
    print_warning "Virtual environment already exists"
    echo -n "Do you want to recreate it? (y/n): "
    read -r response
    if [[ "$response" == "y" ]]; then
        rm -rf venv_new
        python3 -m venv venv_new
        print_success "Virtual environment recreated"
    else
        print_status "Using existing virtual environment"
    fi
else
    python3 -m venv venv_new
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv_new/bin/activate

# Step 2: Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip --quiet
print_success "pip upgraded"

# Step 3: Install Python dependencies
print_status "Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt --quiet
    print_success "Python dependencies installed"
else
    print_error "requirements.txt not found"
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

# Step 4: Install package in development mode
print_status "Installing Whisper Transcription Tool package..."
pip install -e ".[full]" --quiet
print_success "Package installed"

# Step 5: Check for Homebrew and install if needed
print_status "Checking for Homebrew..."
if ! command -v brew &> /dev/null; then
    print_warning "Homebrew not found"
    echo -n "Do you want to install Homebrew? (y/n): "
    read -r response
    if [[ "$response" == "y" ]]; then
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        print_success "Homebrew installed"
    else
        print_warning "Skipping Homebrew installation"
    fi
else
    print_success "Homebrew is installed"
fi

# Step 6: Install FFmpeg
print_status "Checking for FFmpeg..."
if ! command -v ffmpeg &> /dev/null; then
    if command -v brew &> /dev/null; then
        print_status "Installing FFmpeg via Homebrew..."
        brew install ffmpeg
        print_success "FFmpeg installed"
    else
        print_warning "FFmpeg not found and Homebrew not available"
        echo "Please install FFmpeg manually for video processing support"
    fi
else
    print_success "FFmpeg is installed"
fi

# Step 7: Setup Whisper.cpp
print_status "Setting up Whisper.cpp..."
WHISPER_DIR="$PROJECT_ROOT/deps/whisper.cpp"

if [ -d "$WHISPER_DIR" ]; then
    print_status "Whisper.cpp directory found"
    
    # Check if binary exists
    if [ -f "$WHISPER_DIR/build/bin/whisper-cli" ]; then
        print_success "Whisper binary found"
        chmod +x "$WHISPER_DIR/build/bin/whisper-cli"
        print_success "Whisper binary made executable"
    else
        print_warning "Whisper binary not found"
        echo -n "Do you want to build Whisper.cpp? (y/n): "
        read -r response
        if [[ "$response" == "y" ]]; then
            cd "$WHISPER_DIR"
            
            # Clean previous build
            rm -rf build
            mkdir build
            cd build
            
            print_status "Building Whisper.cpp (this may take a few minutes)..."
            cmake ..
            make -j$(sysctl -n hw.ncpu)
            
            if [ -f "bin/whisper-cli" ]; then
                chmod +x bin/whisper-cli
                print_success "Whisper.cpp built successfully"
            else
                print_error "Failed to build Whisper.cpp"
            fi
            
            cd "$PROJECT_ROOT"
        fi
    fi
else
    print_error "Whisper.cpp directory not found at $WHISPER_DIR"
    echo "Please ensure the deps/whisper.cpp directory exists"
fi

# Step 8: Create necessary directories
print_status "Creating necessary directories..."
mkdir -p "$PROJECT_ROOT/models"
mkdir -p "$PROJECT_ROOT/transcriptions"
mkdir -p "$PROJECT_ROOT/transcriptions/temp"
print_success "Directories created"

# Step 9: Download default model
print_status "Checking for Whisper models..."
MODEL_DIR="$PROJECT_ROOT/models"
DEFAULT_MODEL="ggml-large-v3-turbo.bin"

if [ -f "$MODEL_DIR/$DEFAULT_MODEL" ]; then
    print_success "Default model already exists"
else
    print_warning "Default model not found"
    echo -n "Do you want to download the recommended model (large-v3-turbo, ~809MB)? (y/n): "
    read -r response
    if [[ "$response" == "y" ]]; then
        print_status "Downloading model (this may take several minutes)..."
        MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/$DEFAULT_MODEL"
        curl -L --progress-bar -o "$MODEL_DIR/$DEFAULT_MODEL" "$MODEL_URL"
        
        if [ -f "$MODEL_DIR/$DEFAULT_MODEL" ]; then
            print_success "Model downloaded successfully"
        else
            print_error "Failed to download model"
        fi
    else
        print_warning "Skipping model download"
        echo "You can download models later using the web interface"
    fi
fi

# Step 10: Create/Update configuration
print_status "Setting up configuration..."
CONFIG_FILE="$HOME/.whisper_tool.json"

cat > "$CONFIG_FILE" << EOF
{
    "whisper_binary": "$PROJECT_ROOT/deps/whisper.cpp/build/bin/whisper-cli",
    "models_dir": "$PROJECT_ROOT/models",
    "transcriptions_dir": "$PROJECT_ROOT/transcriptions",
    "default_model": "large-v3-turbo",
    "default_language": "auto",
    "cleanup_enabled": true,
    "cleanup_keep_days": 7
}
EOF

print_success "Configuration file created at $CONFIG_FILE"

# Final message
echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║              INSTALLATION COMPLETE! 🎉                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
print_success "Whisper Transcription Tool has been installed successfully!"
echo ""
echo "To start the application:"
echo "  1. Double-click on 'Start.command' in the scripts folder"
echo "  2. Or run: ./scripts/Start.command"
echo ""
echo "The web interface will open at: http://localhost:8090"
echo ""
echo "Press any key to exit..."
read -n 1