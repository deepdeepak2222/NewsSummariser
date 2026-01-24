#!/bin/bash

# Fix ImagePullBackOff issue by pulling image into minikube
# This script helps when the image architecture doesn't match

set -e

echo "🔧 Fixing ImagePullBackOff issue..."

# Check if minikube is running
if ! minikube status &> /dev/null; then
    echo "❌ Error: Minikube is not running"
    exit 1
fi

echo "📥 Pulling image into minikube..."
minikube image pull deepdeepak2222/newssummariser:latest

echo "🔄 Restarting deployment..."
kubectl rollout restart deployment/newssummariser

echo "⏳ Waiting for rollout..."
kubectl rollout status deployment/newssummariser --timeout=300s

echo "✅ Done! Check pods:"
kubectl get pods -l app=newssummariser

