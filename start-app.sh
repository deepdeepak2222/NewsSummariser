#!/bin/bash

# Start News Summarizer Application
# Run this script after restarting your laptop

set -e

echo "🚀 Starting News Summarizer Application"
echo "========================================"
echo ""

# Step 1: Start minikube
echo "📦 Step 1: Starting minikube..."
if ! minikube status &>/dev/null; then
    echo "   Starting minikube (this may take a minute)..."
    minikube start
else
    echo "   ✅ Minikube is already running"
fi

# Wait for minikube to be ready
echo "   Waiting for minikube to be ready..."
minikube status

echo ""
echo "✅ Minikube is running"
echo ""

# Step 2: Check if pods are running
echo "🔍 Step 2: Checking pods..."
kubectl get pods | grep newssummariser || echo "   ⚠️  No pods found. Run: ./k8s/deploy-minikube.sh YOUR_OPENAI_API_KEY"

echo ""

# Step 3: Start port-forwarding
echo "🔌 Step 3: Starting port-forwarding..."
echo "   This will run in the background..."
echo ""

# Kill existing port-forward if running
pkill -f "kubectl port-forward.*newssummariser" 2>/dev/null || true

# Start port-forwarding in background
kubectl port-forward service/newssummariser-service 8501:8501 8000:8000 > /tmp/port-forward.log 2>&1 &
PORT_FORWARD_PID=$!

# Wait a moment for port-forward to establish
sleep 2

# Check if port-forward is working
if ps -p $PORT_FORWARD_PID > /dev/null; then
    echo "   ✅ Port-forwarding started (PID: $PORT_FORWARD_PID)"
    echo "   Logs: /tmp/port-forward.log"
else
    echo "   ❌ Port-forwarding failed. Check logs: /tmp/port-forward.log"
    exit 1
fi

echo ""

# Step 4: Start Cloudflare Tunnel
echo "🌐 Step 4: Starting Cloudflare Tunnel..."
echo "   This will run in the background..."
echo ""

# Kill existing tunnel if running
pkill -f "cloudflared tunnel run" 2>/dev/null || true

# Start tunnel in background
cloudflared tunnel run news-summariser > /tmp/tunnel.log 2>&1 &
TUNNEL_PID=$!

# Wait a moment for tunnel to connect
sleep 3

# Check if tunnel is running
if ps -p $TUNNEL_PID > /dev/null; then
    echo "   ✅ Cloudflare Tunnel started (PID: $TUNNEL_PID)"
    echo "   Logs: /tmp/tunnel.log"
else
    echo "   ❌ Tunnel failed. Check logs: /tmp/tunnel.log"
    exit 1
fi

echo ""
echo "========================================"
echo "✅ Application Started Successfully!"
echo "========================================"
echo ""
echo "📍 Access your app at:"
echo "   🌐 https://news.deestore.in"
echo "   🔗 http://localhost:8501 (local)"
echo ""
echo "📊 Check status:"
echo "   ./check-status.sh"
echo ""
echo "🛑 To stop everything:"
echo "   ./stop-app.sh"
echo ""

