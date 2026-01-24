#!/bin/bash

# Check status of News Summarizer Application

echo "📊 News Summarizer Status"
echo "=========================="
echo ""

# Check minikube
echo "📦 Minikube:"
if minikube status &>/dev/null; then
    echo "   ✅ Running"
    minikube status | grep -E "host|kubelet|apiserver" | sed 's/^/   /'
else
    echo "   ❌ Not running"
fi
echo ""

# Check pods
echo "🔍 Kubernetes Pods:"
kubectl get pods 2>/dev/null | grep newssummariser || echo "   ⚠️  No pods found"
echo ""

# Check port-forwarding
echo "🔌 Port-Forwarding:"
if pgrep -f "kubectl port-forward.*newssummariser" > /dev/null; then
    echo "   ✅ Running"
    echo "   Testing localhost:8501..."
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "   ✅ Service is accessible"
    else
        echo "   ⚠️  Service not responding"
    fi
else
    echo "   ❌ Not running"
fi
echo ""

# Check Cloudflare Tunnel
echo "🌐 Cloudflare Tunnel:"
if pgrep -f "cloudflared tunnel run" > /dev/null; then
    echo "   ✅ Running"
    echo "   Testing news.deestore.in..."
    if curl -s -I https://news.deestore.in 2>&1 | grep -q "200\|HTTP/2"; then
        echo "   ✅ Domain is accessible"
    else
        echo "   ⚠️  Domain not responding (check tunnel logs)"
    fi
else
    echo "   ❌ Not running"
fi
echo ""

# Show recent tunnel logs
if [ -f /tmp/tunnel.log ]; then
    echo "📝 Recent Tunnel Logs:"
    tail -5 /tmp/tunnel.log | sed 's/^/   /'
    echo ""
fi

echo "=========================="
echo ""
echo "📍 Access URLs:"
echo "   🌐 https://news.deestore.in"
echo "   🔗 http://localhost:8501"
echo ""

