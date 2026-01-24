#!/bin/bash

# Stop News Summarizer Application

echo "🛑 Stopping News Summarizer Application"
echo "========================================"
echo ""

# Stop port-forwarding
echo "🔌 Stopping port-forwarding..."
pkill -f "kubectl port-forward.*newssummariser" 2>/dev/null && echo "   ✅ Port-forwarding stopped" || echo "   ℹ️  Port-forwarding was not running"

# Stop Cloudflare Tunnel
echo "🌐 Stopping Cloudflare Tunnel..."
pkill -f "cloudflared tunnel run" 2>/dev/null && echo "   ✅ Tunnel stopped" || echo "   ℹ️  Tunnel was not running"

echo ""
echo "✅ Application stopped"
echo ""
echo "ℹ️  Note: Minikube is still running. To stop it:"
echo "   minikube stop"
echo ""

