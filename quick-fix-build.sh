#!/bin/bash

# Quick fix: Build and push updated image locally
# This is faster than waiting for CI/CD

set -e

echo "🔨 Building updated Docker image locally..."

# Check if logged into Docker Hub (try to pull a test image or check auth)
if ! docker info 2>/dev/null | grep -q "Username" && ! docker system info 2>/dev/null | grep -q "Username"; then
    echo "⚠️  Warning: Docker login status unclear. Attempting build anyway..."
    echo "   If build fails, run: docker login"
fi

# Build for both platforms and push
echo "Building for linux/amd64 and linux/arm64..."
docker buildx create --use --name multiarch 2>/dev/null || docker buildx use multiarch
docker buildx build --platform linux/amd64,linux/arm64 \
  -t deepdeepak2222/newssummariser:latest \
  --push .

echo "✅ Image built and pushed!"
echo ""
echo "🔄 Now update the deployment:"
echo "   kubectl rollout restart deployment/newssummariser"
echo "   kubectl rollout status deployment/newssummariser"

