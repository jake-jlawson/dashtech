# Dashtech Setup Guide

This guide will help you set up Dashtech on any computer (Windows, macOS, Linux).

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 18.04+)
- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 10GB free space
- **CPU**: 4 cores recommended

### Required Software

#### 1. Node.js (v18+)
```bash
# Check if installed
node --version
npm --version

# Install if missing:
# Windows: Download from https://nodejs.org
# macOS: brew install node
# Linux: sudo apt install nodejs npm
```

#### 2. Python 3.8+
```bash
# Check if installed
python3 --version

# Install if missing:
# Windows: Download from https://python.org
# macOS: brew install python3
# Linux: sudo apt install python3 python3-pip
```

#### 3. Rust (for Tauri)
```bash
# Check if installed
rustc --version

# Install if missing:
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

#### 4. Ollama (AI Model Server)
```bash
# Install Ollama
# Windows: Download from https://ollama.ai
# macOS: brew install ollama
# Linux: curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Download required model (in another terminal)
ollama pull gpt-oss:20b
```

## Installation Steps

### 1. Clone and Setup
```bash
git clone <repository-url>
cd dashtech
```

### 2. Install Python Dependencies
```bash
cd app/backend
pip install -r requirements.txt
```

### 3. Install Frontend Dependencies
```bash
cd ../ui
npm install
```

### 4. Build and Run
```bash
# Development mode
npm run tauri dev

# Or build for production
npm run tauri build
```

## Troubleshooting

### Common Issues

#### "Python not found"
- Ensure Python 3.8+ is installed and in PATH
- Try `python3` instead of `python`

#### "Ollama connection failed"
- Start Ollama: `ollama serve`
- Check if model is installed: `ollama list`
- Install model: `ollama pull gpt-oss:20b`

#### "Microphone permission denied"
- **Windows**: Settings > Privacy > Microphone
- **macOS**: System Preferences > Security & Privacy > Privacy > Microphone
- **Linux**: Check PulseAudio permissions

#### "Voice recording failed"
- Install audio dependencies:
  - **Ubuntu**: `sudo apt install portaudio19-dev`
  - **macOS**: `brew install portaudio`
  - **Windows**: Usually works out of the box

### Platform-Specific Notes

#### Windows
- Use PowerShell or Command Prompt
- May need to install Visual Studio Build Tools
- Python executable is usually `python`

#### macOS
- Use Terminal
- May need Xcode Command Line Tools: `xcode-select --install`
- Python executable is usually `python3`

#### Linux
- Use Terminal
- May need additional audio libraries
- Python executable is usually `python3`

## Verification

After setup, verify everything works:

1. **Backend**: Check `http://localhost:8000/test` returns success
2. **Voice Input**: Click microphone button and speak
3. **Voice Output**: Click speaker button on messages
4. **Diagnostics**: Click "Run Diagnostics" button

## Support

If you encounter issues:
1. Check this troubleshooting guide
2. Verify all dependencies are installed
3. Check system permissions (microphone, file access)
4. Review console logs for specific error messages
