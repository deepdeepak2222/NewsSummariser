#!/bin/bash

# Setup script for public IP hosting
# This assumes you've configured port forwarding on your router

set -e

echo "🌐 Public IP Setup for News Summarizer"
echo "======================================"
echo ""

PUBLIC_IP="49.207.61.209"
LOCAL_IP="192.168.0.104"
MINIKUBE_IP=$(minikube ip 2>/dev/null || echo "192.168.49.2")

echo "📋 Detected Configuration:"
echo "   Public IP: $PUBLIC_IP"
echo "   Local IP: $LOCAL_IP"
echo "   Minikube IP: $MINIKUBE_IP"
echo ""

read -p "Enter your domain name (e.g., news.yourdomain.com): " DOMAIN_NAME
read -p "Enter your email for Let's Encrypt SSL: " EMAIL

if [ -z "$DOMAIN_NAME" ] || [ -z "$EMAIL" ]; then
    echo "❌ Error: Domain name and email are required"
    exit 1
fi

echo ""
echo "⚠️  IMPORTANT: Before proceeding, ensure:"
echo "   1. Port forwarding is configured on your router:"
echo "      - Port 80 → $LOCAL_IP:30080"
echo "      - Port 443 → $LOCAL_IP:30080"
echo "   2. DNS A record in GoDaddy points to: $PUBLIC_IP"
echo "   3. Ports 80/443 are not blocked by your ISP"
echo ""
read -p "Have you completed the above steps? (y/n): " CONFIRMED

if [ "$CONFIRMED" != "y" ]; then
    echo ""
    echo "Please complete the prerequisites first:"
    echo "1. Configure port forwarding on router"
    echo "2. Set up DNS in GoDaddy"
    echo ""
    echo "See PUBLIC_IP_SETUP.md for detailed instructions"
    exit 0
fi

# Enable ingress in minikube
echo ""
echo "📦 Step 1: Enabling Ingress in Minikube..."
minikube addons enable ingress

# Install cert-manager
echo ""
echo "🔒 Step 2: Installing cert-manager..."
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml
echo "⏳ Waiting for cert-manager..."
kubectl wait --namespace cert-manager \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=cert-manager \
  --timeout=300s

# Create ClusterIssuer
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

# Update and apply ingress
echo ""
echo "🌐 Step 4: Configuring Ingress..."
sed "s/newssummariser.yourdomain.com/$DOMAIN_NAME/g" k8s/ingress.yaml > /tmp/ingress-updated.yaml
kubectl apply -f /tmp/ingress-updated.yaml

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Configuration Summary:"
echo "   Domain: $DOMAIN_NAME"
echo "   Public IP: $PUBLIC_IP"
echo "   Email: $EMAIL"
echo ""
echo "🔍 Next Steps:"
echo "1. Wait for DNS propagation (5-30 minutes)"
echo "2. Test: curl http://$DOMAIN_NAME"
echo "3. Check SSL: kubectl describe certificate newssummariser-tls"
echo ""
echo "⚠️  Note: If your public IP changes, update GoDaddy DNS"
echo "   Consider setting up Dynamic DNS (see PUBLIC_IP_SETUP.md)"

