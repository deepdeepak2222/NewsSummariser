#!/bin/bash

# Setup Ollama in Kubernetes for News Summarizer
# This script:
# 1. Creates Ollama deployment
# 2. Pulls Mistral 7B model
# 3. Updates main deployment to use Ollama

set -e

echo "🚀 Setting up Ollama in Kubernetes"
echo "===================================="
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ Error: kubectl is not installed or not in PATH"
    exit 1
fi

# Check if minikube is running (or any k8s cluster)
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Error: Kubernetes cluster is not accessible"
    echo "   Make sure minikube is running: minikube start"
    exit 1
fi

echo "✅ Kubernetes cluster is accessible"
echo ""

# Step 1: Deploy Ollama
echo "📦 Step 1: Deploying Ollama..."
kubectl apply -f k8s/ollama-deployment.yaml

echo "⏳ Waiting for Ollama to be ready..."
kubectl wait --for=condition=available deployment/ollama --timeout=300s || {
    echo "⚠️  Ollama deployment taking longer than expected"
    echo "   Check status: kubectl get pods -l app=ollama"
}

echo "✅ Ollama deployed"
echo ""

# Step 2: Wait for Ollama pod to be ready
echo "⏳ Waiting for Ollama pod to be ready..."
OLLAMA_POD=$(kubectl get pod -l app=ollama -o jsonpath='{.items[0].metadata.name}')
kubectl wait --for=condition=ready pod/$OLLAMA_POD --timeout=300s

echo "✅ Ollama pod is ready"
echo ""

# Step 3: Pull Mistral 7B model
echo "📥 Step 2: Pulling Mistral 7B model (~4GB, this may take 5-10 minutes)..."
echo "   This is a one-time download"
echo ""

kubectl exec $OLLAMA_POD -- ollama pull mistral:7b

echo ""
echo "✅ Mistral 7B model downloaded"
echo ""

# Step 4: Verify model is available
echo "🔍 Step 3: Verifying model..."
kubectl exec $OLLAMA_POD -- ollama list | grep mistral:7b || {
    echo "⚠️  Warning: Mistral model not found in list"
}

echo "✅ Model verification complete"
echo ""

# Step 5: Update main deployment
echo "🔄 Step 4: Updating News Summarizer deployment to use Ollama..."
echo "   Options:"
echo "   1. Use deployment-with-ollama.yaml (recommended)"
echo "   2. Update existing deployment.yaml manually"
echo ""
read -p "Update deployment now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "📝 Applying updated deployment..."
    kubectl apply -f k8s/deployment-with-ollama.yaml
    
    echo "⏳ Waiting for deployment rollout..."
    kubectl rollout status deployment/newssummariser --timeout=300s
    
    echo "✅ Deployment updated"
else
    echo "ℹ️  Skipping deployment update"
    echo "   You can update manually later"
fi

echo ""
echo "===================================="
echo "✅ Setup Complete!"
echo "===================================="
echo ""
echo "📊 Status:"
kubectl get pods -l app=ollama
echo ""
kubectl get pods -l app=newssummariser
echo ""
echo "🧪 Test Ollama:"
echo "   kubectl exec -it $OLLAMA_POD -- ollama run mistral:7b \"Test\""
echo ""
echo "📝 Next Steps:"
echo "   1. Your app is now using Ollama instead of OpenAI"
echo "   2. Check logs: kubectl logs -f deployment/newssummariser"
echo "   3. Monitor Ollama: kubectl logs -f deployment/ollama"
echo ""

