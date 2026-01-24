#!/bin/bash

# Build and push Docker image for linux/amd64 (for minikube)
# This is a temporary fix until CI/CD builds multi-platform images

set -e

echo "🔨 Building Docker image for linux/amd64..."

# Build for linux/amd64 platform
docker buildx create --use --name multiarch-builder 2>/dev/null || docker buildx use multiarch-builder
docker buildx build --platform linux/amd64,linux/arm64 \
  -t deepdeepak2222/newssummariser:latest \
  --push .

echo "✅ Image built and pushed for both platforms!"
echo "Now you can deploy: ./k8s/deploy-minikube.sh YOUR_API_KEY"

