# Whisper Transcription Tool

🎙️ **A powerful, modular Python tool for audio/video transcription using Whisper.cpp**

[![Version](https://img.shields.io/badge/version-0.9.5-blue.svg)](https://github.com/cubetribe/Whisper-Transcription-Tool)
[![Python](https://img.shields.io/badge/python-3.8%2B-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Personal%20Use%20%7C%20Commercial%20on%20Request-orange.svg)](LICENSE)
[![Website](https://img.shields.io/badge/website-goaiex.com-orange.svg)](https://www.goaiex.com)

## ✨ Features

- 🚀 **Local transcription** with Whisper.cpp (no API needed)
- 🍎 **Optimized for Apple Silicon** Macs
- 🌐 **Web interface** with real-time progress updates
- 📁 **Batch processing** for multiple files
- 🎬 **Video support** with automatic audio extraction
- 📄 **Multiple output formats** (TXT, SRT, VTT, JSON)
- 🧹 **Automatic cleanup** of temporary files
- 🎯 **Phone recording** with dual-track support

## 🚀 Quick Start

### Fastest Way to Start
```bash
# Clone the repository
git clone https://github.com/cubetribe/Whisper-Transcription-Tool.git
cd Whisper-Transcription-Tool

# Activate virtual environment
source venv_new/bin/activate  # Use venv_new, NOT venv

# Start the web server
python -m src.whisper_transcription_tool.main web --port 8090
```

Then open http://localhost:8090 in your browser.

### Alternative: Using Start Script
```bash
./start_server.sh
```

## 🔧 Installation

### Prerequisites
- Python 3.8+
- macOS (optimized for Apple Silicon)
- FFmpeg (auto-installed via install.sh)

### Full Setup
```bash
# 1. Clone repository
git clone https://github.com/cubetribe/Whisper-Transcription-Tool.git
cd Whisper-Transcription-Tool

# 2. Create virtual environment
python3 -m venv venv_new
source venv_new/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
pip install -e ".[full]"

# 4. Setup Whisper.cpp and FFmpeg
bash install.sh

# 5. Make whisper binary executable
chmod +x deps/whisper.cpp/build/bin/whisper-cli
```

## 📁 Project Structure

```
whisper_clean/
├── src/                              # Main source code
│   └── whisper_transcription_tool/
│       ├── core/                     # Core functionality
│       ├── module1_transcribe/       # Transcription module
│       ├── module2_extract/          # Video extraction
│       ├── module3_phone/            # Phone recording
│       ├── module4_chatbot/          # Chatbot module
│       └── web/                      # Web interface
├── models/                           # Whisper models
├── transcriptions/                   # Output directory
├── deps/                            # Dependencies (Whisper.cpp)
├── scripts/                         # Utility scripts
└── start_server.sh                  # Server start script
```

## 💻 Usage

### Web Interface (Recommended)
```bash
# Start server
./start_server.sh
# Open http://localhost:8090
```

### Command Line
```bash
# Transcribe audio/video
whisper-tool transcribe path/to/audio.mp3 --model large-v3-turbo

# Extract audio from video
whisper-tool extract path/to/video.mp4

# Process phone recordings
whisper-tool phone track_a.mp3 track_b.mp3
```

## 🎯 Available Models

- `tiny` - Fastest, least accurate (39 MB)
- `base` - Fast, good accuracy (74 MB)
- `small` - Balanced speed/accuracy (244 MB)
- `medium` - Slower, better accuracy (769 MB)
- `large-v3` - Best accuracy (1550 MB)
- **`large-v3-turbo`** - Best balance (recommended, 809 MB)

## 🛠️ Troubleshooting

### Permission Denied Error
```bash
chmod +x deps/whisper.cpp/build/bin/whisper-cli
```

### Port Already in Use
```bash
# The start script handles this automatically
# Or manually change port:
python -m src.whisper_transcription_tool.main web --port 8091
```

### Virtual Environment Issues
- Primary: Use `venv_new`
- Fallback: `venv`
- The start_server.sh script checks for both

## 📖 Documentation

- [Full Documentation](documentation/README.md)
- [Installation Guide](documentation/INSTALLATION.md)
- [Claude Code Instructions](CLAUDE.md)
- [Changelog](CHANGELOG.md)

## 🔐 License

**PERSONAL USE LICENSE**  
Copyright © 2025 Dennis Westermann - aiEX Academy  
Website: [www.goaiex.com](https://www.goaiex.com)

### 📋 License Terms

#### ✅ Free for Personal Use:
- Personal projects and learning
- Educational and academic research
- Non-profit personal use

#### 💼 Commercial & Enterprise Use:
**Available upon request!** We offer flexible licensing options for:
- Commercial products and services
- Business and enterprise deployment
- Professional services and consulting
- Revenue-generating activities

### 📧 Get a Commercial License

For commercial or enterprise licensing, please contact:
- **Email**: mail@goaiex.com
- **Website**: [www.goaiex.com](https://www.goaiex.com)

We're happy to discuss your needs and provide appropriate licensing terms.

See the [LICENSE](LICENSE) file for full terms and conditions.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/cubetribe/Whisper-Transcription-Tool/issues)
- **Website**: [www.goaiex.com](https://www.goaiex.com)
- **Documentation**: See the `documentation/` directory

---

**Version:** 0.9.5 | **Status:** Production Ready ✅

Made with ❤️ by aiEX Academy for the transcription community