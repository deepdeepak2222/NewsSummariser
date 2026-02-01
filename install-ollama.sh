#!/bin/bash

# Install and setup Ollama with Mistral 7B for News Summarizer

set -e

echo "🚀 Setting up Ollama with Mistral 7B"
echo "======================================"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "📦 Installing Ollama..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found. Please install Homebrew first:"
        echo "   /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
    
    brew install ollama
    echo "✅ Ollama installed"
else
    echo "✅ Ollama already installed"
fi

echo ""

# Check if Ollama server is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama server is running"
else
    echo "⚠️  Ollama server not running"
    echo "   Starting Ollama server..."
    echo "   (This will run in background)"
    
    # Start Ollama in background
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    
    echo "   Started with PID: $OLLAMA_PID"
    echo "   Waiting for server to start..."
    sleep 5
    
    # Check if it started
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✅ Ollama server started successfully"
    else
        echo "❌ Failed to start Ollama server"
        echo "   Try manually: ollama serve"
        exit 1
    fi
fi

echo ""

# Check if Mistral 7B is installed
echo "🔍 Checking for Mistral 7B model..."
if ollama list | grep -q "mistral:7b"; then
    echo "✅ Mistral 7B already installed"
else
    echo "📥 Downloading Mistral 7B (~4GB, this may take a few minutes)..."
    echo "   This is a one-time download"
    ollama pull mistral:7b
    echo "✅ Mistral 7B installed"
fi

echo ""
echo "======================================"
echo "✅ Setup Complete!"
echo "======================================"
echo ""
echo "📊 Your System:"
echo "   RAM: 8GB"
echo "   CPU: 8 cores (M2)"
echo "   Model: Mistral 7B"
echo ""
echo "⚡ Expected Performance:"
echo "   First request: 10-15 seconds"
echo "   Subsequent: 3-5 seconds per summary"
echo ""
echo "🧪 Test it:"
echo "   ollama run mistral:7b \"Summarize this in Hindi: [your text]\""
echo ""
echo "🔧 Next Steps:"
echo "   1. Add to .env: AI_PROVIDER=ollama"
echo "   2. Restart your app"
echo "   3. It will use Mistral instead of OpenAI!"
echo ""

