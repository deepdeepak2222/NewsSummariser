#!/bin/bash

# Update deployment with latest image
# This pulls the latest image from Docker Hub

set -e

echo "🔄 Updating deployment to use latest image..."

# Restart deployment to pull latest image
kubectl rollout restart deployment/newssummariser

echo "⏳ Waiting for rollout to complete..."
kubectl rollout status deployment/newssummariser --timeout=300s

echo "✅ Deployment updated!"
echo ""
echo "📊 New pod status:"
kubectl get pods -l app=newssummariser

echo ""
echo "📝 View logs: kubectl logs -f deployment/newssummariser"

