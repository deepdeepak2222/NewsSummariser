#!/bin/bash

# Cloudflare Tunnel Setup for news.deestore.in
# This script sets up Cloudflare Tunnel to expose your minikube app

set -e

DOMAIN="news.deestore.in"
BASE_DOMAIN="deestore.in"

echo "🌐 Cloudflare Tunnel Setup for $DOMAIN"
echo "========================================"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "❌ Error: cloudflared is not installed"
    echo "   Install with: brew install cloudflared"
    exit 1
fi

echo "✅ cloudflared is installed"
echo ""

# Step 1: Login to Cloudflare
echo "📝 Step 1: Authenticating with Cloudflare..."
echo "   This will open a browser window for authentication"
echo ""
read -p "Press Enter to continue..."
cloudflared tunnel login

# Step 2: Create tunnel
echo ""
echo "📦 Step 2: Creating Cloudflare Tunnel..."
TUNNEL_NAME="news-summariser"
cloudflared tunnel create $TUNNEL_NAME 2>/dev/null || echo "Tunnel already exists or continuing..."

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep "$TUNNEL_NAME" | awk '{print $1}' | head -1)

if [ -z "$TUNNEL_ID" ]; then
    echo "❌ Error: Could not find tunnel ID"
    echo "   Please check: cloudflared tunnel list"
    exit 1
fi

echo "✅ Tunnel created: $TUNNEL_ID"
echo ""

# Step 3: Get minikube service URL
echo "🔍 Step 3: Getting minikube service URL..."
MINIKUBE_IP=$(minikube ip)
NODEPORT=$(kubectl get svc newssummariser-service -o jsonpath='{.spec.ports[?(@.name=="streamlit")].nodePort}')

if [ -z "$NODEPORT" ]; then
    echo "⚠️  Warning: Could not find NodePort, using default 30080"
    NODEPORT="30080"
fi

SERVICE_URL="http://${MINIKUBE_IP}:${NODEPORT}"
echo "   Service URL: $SERVICE_URL"
echo ""

# Step 4: Create tunnel config
echo "📝 Step 4: Creating tunnel configuration..."
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/config.yaml" <<EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - hostname: $DOMAIN
    service: $SERVICE_URL
  - service: http_status:404
EOF

echo "✅ Configuration saved to: $CONFIG_DIR/config.yaml"
echo ""

# Step 5: Create DNS route
echo "🌐 Step 5: Creating DNS route in Cloudflare..."
echo "   This will create a CNAME record: $DOMAIN → $TUNNEL_ID.cfargotunnel.com"
echo ""
read -p "Press Enter to create DNS route..."
cloudflared tunnel route dns $TUNNEL_NAME $DOMAIN

echo ""
echo "✅ DNS route created!"
echo ""

# Step 6: Instructions for GoDaddy
echo "📋 Step 6: GoDaddy DNS Configuration"
echo "======================================"
echo ""
echo "⚠️  IMPORTANT: You need to update DNS in GoDaddy:"
echo ""
echo "1. Go to: https://www.godaddy.com"
echo "2. Navigate to: My Products → DNS Management for deestore.in"
echo "3. Add/Edit CNAME record:"
echo "   - Type: CNAME"
echo "   - Name: news"
echo "   - Value: $TUNNEL_ID.cfargotunnel.com"
echo "   - TTL: 600"
echo "4. Save the changes"
echo ""
echo "   OR let Cloudflare manage DNS (recommended):"
echo "   - Transfer DNS to Cloudflare (free)"
echo "   - Cloudflare will manage DNS automatically"
echo ""

read -p "Have you configured DNS in GoDaddy? (y/n): " DNS_CONFIRMED

# Step 7: Run tunnel
echo ""
echo "🚀 Step 7: Starting Cloudflare Tunnel..."
echo ""
echo "⚠️  Keep this terminal open - the tunnel runs in foreground"
echo "   To run in background, use: cloudflared tunnel run $TUNNEL_NAME &"
echo ""
echo "Starting tunnel in 5 seconds..."
sleep 5

cloudflared tunnel run $TUNNEL_NAME

