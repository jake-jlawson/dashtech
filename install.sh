#!/bin/bash

# Dashtech Installation Script
# This script helps set up Dashtech on Linux/macOS

set -e

echo "🚀 Dashtech Installation Script"
echo "================================"

# Check if we're on a supported OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo "❌ Unsupported OS: $OSTYPE"
    echo "Please follow manual setup instructions in SETUP.md"
    exit 1
fi

echo "✅ Detected OS: $OS"

# Check for required tools
check_command() {
    if command -v $1 &> /dev/null; then
        echo "✅ $1 is installed"
        return 0
    else
        echo "❌ $1 is not installed"
        return 1
    fi
}

echo ""
echo "🔍 Checking dependencies..."

# Check Node.js
if ! check_command node; then
    echo "Please install Node.js from https://nodejs.org"
    exit 1
fi

# Check Python
if ! check_command python3; then
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

# Check Rust
if ! check_command rustc; then
    echo "Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source ~/.cargo/env
fi

# Check Ollama
if ! check_command ollama; then
    echo "Installing Ollama..."
    if [[ "$OS" == "linux" ]]; then
        curl -fsSL https://ollama.ai/install.sh | sh
    elif [[ "$OS" == "macos" ]]; then
        brew install ollama
    fi
fi

echo ""
echo "📦 Installing Python dependencies..."
cd app/backend
pip3 install -r requirements.txt

echo ""
echo "📦 Installing frontend dependencies..."
cd ../ui
npm install

echo ""
echo "🤖 Setting up AI models..."
# Start Ollama in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to start
sleep 5

# Download required model
echo "Downloading gpt-oss:20b model (this may take a while)..."
ollama pull gpt-oss:20b

# Stop Ollama
kill $OLLAMA_PID 2>/dev/null || true

echo ""
echo "✅ Installation complete!"
echo ""
echo "To run Dashtech:"
echo "1. Start Ollama: ollama serve"
echo "2. Run the app: cd app/ui && npm run tauri dev"
echo ""
echo "For troubleshooting, see SETUP.md"
