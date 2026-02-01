#!/bin/bash

# Quick test script for Mistral 7B

echo "🧪 Testing Mistral 7B on your laptop"
echo "====================================="
echo ""

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "❌ Ollama server not running"
    echo "   Start it with: ollama serve"
    echo "   Or run: ./install-ollama.sh"
    exit 1
fi

echo "✅ Ollama server is running"
echo ""

# Check if Mistral is installed
if ! ollama list | grep -q "mistral:7b"; then
    echo "❌ Mistral 7B not installed"
    echo "   Install with: ollama pull mistral:7b"
    echo "   Or run: ./install-ollama.sh"
    exit 1
fi

echo "✅ Mistral 7B is installed"
echo ""

# Test summarization
echo "📝 Testing Hindi summarization..."
echo "   (This may take 10-15 seconds on first run)"
echo ""

TEST_TEXT="India is developing rapidly. Technology sector is growing fast. Many startups are emerging. Digital infrastructure is improving. Education system is modernizing."

RESULT=$(ollama run mistral:7b "Summarize this news in Hindi in 2-3 sentences: $TEST_TEXT" 2>&1)

echo "📊 Result:"
echo "---"
echo "$RESULT"
echo "---"
echo ""

if echo "$RESULT" | grep -qi "हिंदी\|भारत\|विकास\|तकनीक"; then
    echo "✅ Mistral 7B is working! Hindi summarization successful."
else
    echo "⚠️  Got response, but might not be in Hindi. Check the output above."
fi

echo ""
echo "⏱️  Performance:"
echo "   First run: Model loads (10-15s)"
echo "   Next runs: Should be faster (3-5s)"
echo ""
echo "💡 To use in your app:"
echo "   1. Add to .env: AI_PROVIDER=ollama"
echo "   2. Restart your app"
echo ""

