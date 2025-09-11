@echo off
REM Dashtech Installation Script for Windows
REM This script helps set up Dashtech on Windows

echo 🚀 Dashtech Installation Script
echo ================================

REM Check for required tools
echo.
echo 🔍 Checking dependencies...

REM Check Node.js
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed
    echo Please install Node.js from https://nodejs.org
    pause
    exit /b 1
) else (
    echo ✅ Node.js is installed
)

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
) else (
    echo ✅ Python is installed
)

REM Check Rust
rustc --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Rust is not installed
    echo Please install Rust from https://rustup.rs
    pause
    exit /b 1
) else (
    echo ✅ Rust is installed
)

REM Check Ollama
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Ollama is not installed
    echo Please install Ollama from https://ollama.ai
    pause
    exit /b 1
) else (
    echo ✅ Ollama is installed
)

echo.
echo 📦 Installing Python dependencies...
cd app\backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install Python dependencies
    pause
    exit /b 1
)

echo.
echo 📦 Installing frontend dependencies...
cd ..\ui
npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo 🤖 Setting up AI models...
echo Starting Ollama...
start /B ollama serve

REM Wait for Ollama to start
timeout /t 5 /nobreak >nul

echo Downloading gpt-oss:20b model (this may take a while)...
ollama pull gpt-oss:20b
if %errorlevel% neq 0 (
    echo ❌ Failed to download AI model
    pause
    exit /b 1
)

echo.
echo ✅ Installation complete!
echo.
echo To run Dashtech:
echo 1. Start Ollama: ollama serve
echo 2. Run the app: cd app\ui ^&^& npm run tauri dev
echo.
echo For troubleshooting, see SETUP.md
pause
