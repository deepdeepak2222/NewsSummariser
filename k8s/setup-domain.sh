#!/bin/bash

# Domain Setup Script for News Summarizer
# This script helps set up your domain with Kubernetes

set -e

echo "🌐 Domain Setup for News Summarizer"
echo "===================================="
echo ""

# Check if running in minikube or cloud
if kubectl config current-context | grep -q "minikube"; then
    echo "📍 Detected: Minikube (Local Cluster)"
    CLUSTER_TYPE="minikube"
else
    echo "📍 Detected: Cloud Cluster"
    CLUSTER_TYPE="cloud"
fi

echo ""
echo "📋 Domain Setup:"
echo "   Your domain: deestore.in"
echo "   Subdomain pattern: <app>.deestore.in"
echo ""
read -p "Enter subdomain name (e.g., 'news' for news.deestore.in): " SUBDOMAIN
read -p "Enter your email for Let's Encrypt SSL: " EMAIL

if [ -z "$SUBDOMAIN" ]; then
    SUBDOMAIN="news"
    echo "   Using default: news"
fi

DOMAIN_NAME="${SUBDOMAIN}.deestore.in"

if [ -z "$DOMAIN_NAME" ] || [ -z "$EMAIL" ]; then
    echo "❌ Error: Domain name and email are required"
    exit 1
fi

echo ""
echo "📋 Configuration:"
echo "   Domain: $DOMAIN_NAME"
echo "   Email: $EMAIL"
echo "   Cluster: $CLUSTER_TYPE"
echo ""

read -p "Continue? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Enable/Install Ingress
echo ""
echo "📦 Step 1: Setting up Ingress Controller..."
if [ "$CLUSTER_TYPE" = "minikube" ]; then
    minikube addons enable ingress
    echo "✅ Minikube ingress addon enabled"
    EXTERNAL_IP=$(minikube ip)
    echo "⚠️  Note: Minikube IP: $EXTERNAL_IP"
    echo "   For production, you'll need a tunneling service or cloud cluster"
else
    kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
    echo "⏳ Waiting for ingress controller to be ready..."
    kubectl wait --namespace ingress-nginx \
      --for=condition=ready pod \
      --selector=app.kubernetes.io/component=controller \
      --timeout=300s
    EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    if [ -z "$EXTERNAL_IP" ]; then
        EXTERNAL_IP=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    fi
fi

# Step 2: Install cert-manager
echo ""
echo "🔒 Step 2: Installing cert-manager for SSL..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
echo "⏳ Waiting for cert-manager to be ready..."
kubectl wait --namespace cert-manager \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=cert-manager \
  --timeout=300s

# Step 3: Create ClusterIssuer
echo ""
echo "📝 Step 3: Creating Let's Encrypt ClusterIssuer..."
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: $EMAIL
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF

# Step 4: Update and apply Ingress
echo ""
echo "🌐 Step 4: Configuring Ingress..."
# Update ingress.yaml with domain name
sed "s/newssummariser.yourdomain.com/$DOMAIN_NAME/g" k8s/ingress.yaml > /tmp/ingress-updated.yaml
kubectl apply -f /tmp/ingress-updated.yaml

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next Steps:"
echo ""
if [ "$CLUSTER_TYPE" = "minikube" ]; then
    echo "⚠️  IMPORTANT: For minikube, you need to:"
    echo "   1. Use a tunneling service (ngrok, Cloudflare Tunnel, etc.)"
    echo "   2. Point your GoDaddy DNS to the tunnel endpoint"
    echo "   3. Or deploy to a cloud Kubernetes cluster"
    echo ""
    echo "   Current minikube IP: $EXTERNAL_IP"
    echo "   This IP is only accessible on your local network"
else
    echo "1. Configure DNS in GoDaddy:"
    echo "   - Type: A"
    echo "   - Name: @ (or subdomain)"
    echo "   - Value: $EXTERNAL_IP"
    echo ""
    echo "2. Wait for DNS propagation (5-30 minutes)"
    echo ""
    echo "3. Check status:"
    echo "   kubectl get ingress"
    echo "   kubectl describe certificate newssummariser-tls"
fi

echo ""
echo "🔍 Check ingress status:"
kubectl get ingress

