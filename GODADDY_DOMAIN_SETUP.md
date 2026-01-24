# GoDaddy Domain Setup - Step by Step Guide

## Overview

This guide will help you connect your GoDaddy domain to your News Summarizer application running on Kubernetes.

## Prerequisites

- ✅ GoDaddy domain purchased
- ✅ Kubernetes cluster running (minikube or cloud)
- ✅ Application deployed and running

## Important: Choose Your Setup Type

### Option A: Cloud Kubernetes (Recommended for Production)
**Best for:** Production deployments, real websites
- **GKE** (Google Cloud), **EKS** (AWS), or **AKS** (Azure)
- Provides a real external IP that DNS can point to
- Automatic SSL certificates with Let's Encrypt

### Option B: Local Minikube with Tunneling
**Best for:** Development, testing, learning
- Use **Cloudflare Tunnel** (free) or **ngrok** (free tier available)
- Exposes your local minikube to the internet
- Can use real domain and SSL

---

## Step-by-Step: Cloud Kubernetes Setup

### Step 1: Install Ingress Controller

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml

# Wait for it to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s
```

### Step 2: Get External IP

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

Copy the **EXTERNAL-IP** (e.g., `34.123.45.67`)

### Step 3: Configure DNS in GoDaddy

1. **Log in to GoDaddy**
   - Go to https://www.godaddy.com
   - Click "Sign In" → Enter credentials

2. **Navigate to DNS Management**
   - Click "My Products"
   - Find your domain
   - Click "DNS" or "Manage DNS"

3. **Add/Edit A Record**
   - Find the **A Record** section
   - Click **"Add"** or edit existing **@** record
   - **Type**: A
   - **Name**: `@` (for root domain) OR `news` (for subdomain)
   - **Value**: Paste your Kubernetes EXTERNAL-IP
   - **TTL**: 600 (10 minutes)
   - Click **"Save"**

   **Example:**
   - For `yourdomain.com` → Name: `@`
   - For `news.yourdomain.com` → Name: `news`

4. **Wait for DNS Propagation**
   - Usually takes 5-30 minutes
   - Check with: `nslookup yourdomain.com` or `dig yourdomain.com`

### Step 4: Install cert-manager (for SSL)

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.3/cert-manager.yaml

# Wait for cert-manager
kubectl wait --namespace cert-manager \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/instance=cert-manager \
  --timeout=300s
```

### Step 5: Create Let's Encrypt ClusterIssuer

Replace `your-email@example.com` with your email:

```bash
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Step 6: Update and Apply Ingress

1. **Edit `k8s/ingress.yaml`**:
   - Replace `newssummariser.yourdomain.com` with your actual domain
   - Example: `news.yourdomain.com`

2. **Apply Ingress**:
   ```bash
   kubectl apply -f k8s/ingress.yaml
   ```

3. **Check Status**:
   ```bash
   kubectl get ingress
   kubectl describe ingress newssummariser-ingress
   ```

### Step 7: Verify SSL Certificate

```bash
# Check certificate status
kubectl describe certificate newssummariser-tls

# Test your domain
curl -I https://yourdomain.com
```

---

## Step-by-Step: Minikube with Cloudflare Tunnel

### Step 1: Install Cloudflare Tunnel

```bash
# Download cloudflared (macOS)
brew install cloudflared

# Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
```

### Step 2: Authenticate Cloudflare

```bash
cloudflared tunnel login
```

This opens a browser - select your domain and authorize.

### Step 3: Create Tunnel

```bash
cloudflared tunnel create newssummariser
```

Note the tunnel ID.

### Step 4: Configure Tunnel

Create `cloudflare-tunnel-config.yaml`:

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /Users/deep/.cloudflared/<TUNNEL_ID>.json

ingress:
  - hostname: news.yourdomain.com
    service: http://localhost:30080  # Minikube NodePort
  - service: http_status:404
```

### Step 5: Run Tunnel

```bash
cloudflared tunnel --config cloudflare-tunnel-config.yaml run
```

### Step 6: Configure DNS in GoDaddy

1. Go to GoDaddy DNS management
2. Add **CNAME** record:
   - **Type**: CNAME
   - **Name**: `news` (or `@` for root)
   - **Value**: `<TUNNEL_ID>.cfargotunnel.com`
   - **TTL**: 600

### Step 7: Update Ingress (for SSL)

The tunnel handles SSL automatically, but you can still use ingress for internal routing.

---

## Quick Setup Script

We've created an automated script:

```bash
./k8s/setup-domain.sh
```

This will:
1. Detect your cluster type
2. Install ingress controller
3. Install cert-manager
4. Create ClusterIssuer
5. Configure ingress
6. Provide DNS instructions

---

## Troubleshooting

### DNS Not Resolving
```bash
# Check DNS propagation
nslookup yourdomain.com
dig yourdomain.com

# Check if DNS is correct in GoDaddy
# Wait 10-30 minutes for propagation
```

### Ingress Not Working
```bash
# Check ingress status
kubectl get ingress
kubectl describe ingress newssummariser-ingress

# Check ingress controller logs
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller
```

### SSL Certificate Issues
```bash
# Check certificate status
kubectl get certificate
kubectl describe certificate newssummariser-tls

# Check cert-manager logs
kubectl logs -n cert-manager -l app.kubernetes.io/instance=cert-manager
```

### Service Not Accessible
```bash
# Verify service exists
kubectl get svc newssummariser-service

# Check service endpoints
kubectl get endpoints newssummariser-service

# Verify pods are running
kubectl get pods -l app=newssummariser
```

---

## Next Steps After Setup

1. **Test your domain**: Visit `https://yourdomain.com` in a browser
2. **Monitor logs**: `kubectl logs -f deployment/newssummariser`
3. **Set up monitoring**: Consider Prometheus/Grafana
4. **Backup**: Regular backups of Kubernetes configs

---

## Cost Considerations

- **Cloud Kubernetes**: ~$20-50/month (GKE/EKS/AKS)
- **Cloudflare Tunnel**: Free
- **GoDaddy Domain**: Already purchased
- **SSL Certificate**: Free (Let's Encrypt)

---

## Need Help?

- Check logs: `kubectl logs -f deployment/newssummariser`
- Ingress issues: `kubectl describe ingress`
- DNS issues: Use `nslookup` or `dig`

