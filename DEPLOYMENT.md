# Deployment Guide

## Prerequisites

1. **GitHub Account** with repository access
2. **Docker Hub Account** (https://hub.docker.com/repository/docker/deepdeepak2222)
3. **Kubernetes Cluster** (GKE, EKS, AKS, or local minikube)
4. **kubectl** configured

## Step 1: Push Code to GitHub

### Option A: Using SSH (Recommended)
```bash
# If SSH keys are not set up, generate them:
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add SSH key to GitHub:
# 1. Copy public key: cat ~/.ssh/id_ed25519.pub
# 2. Go to GitHub Settings > SSH and GPG keys > New SSH key
# 3. Paste and save

# Push code
git push -u origin main
```

### Option B: Using HTTPS
```bash
# Change remote URL to HTTPS
git remote set-url origin https://github.com/deepdeepak2222/NewsSummariser.git

# Push code (will prompt for credentials)
git push -u origin main
```

## Step 2: Set Up GitHub Actions Secrets

1. Go to your GitHub repository
2. Navigate to **Settings** > **Secrets and variables** > **Actions**
3. Add the following secrets:
   - `DOCKERHUB_USERNAME`: `deepdeepak2222`
   - `DOCKERHUB_TOKEN`: Your Docker Hub access token
     - Get token from: https://hub.docker.com/settings/security
     - Click "New Access Token"

## Step 3: CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/docker-build-push.yml`) will automatically:
- Build Docker image on push to main/master
- Push to Docker Hub: `deepdeepak2222/newssummariser:latest`
- Tag images with branch names and commit SHAs

## Step 4: Deploy to Kubernetes

### 4.1 Create Secret
```bash
kubectl create secret generic newssummariser-secrets \
  --from-literal=openai-api-key=YOUR_OPENAI_API_KEY_HERE
```

### 4.2 Deploy Application
```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Optional: Apply ingress (if you have ingress controller)
kubectl apply -f k8s/ingress.yaml
```

### 4.3 Check Status
```bash
# Check pods
kubectl get pods -l app=newssummariser

# Check services
kubectl get svc newssummariser-service

# View logs
kubectl logs -f deployment/newssummariser
```

### 4.4 Access Application
- **LoadBalancer**: Get external IP with `kubectl get svc newssummariser-service`
- **Ingress**: Configure DNS to point to ingress controller IP

## Step 5: Update Deployment

After pushing new code:
```bash
# Pull latest image
kubectl rollout restart deployment/newssummariser

# Or update image tag in deployment.yaml and apply
kubectl apply -f k8s/deployment.yaml
```

## Troubleshooting

### Docker Build Fails
- Check Docker Hub credentials in GitHub Secrets
- Verify Dockerfile syntax
- Check build logs in GitHub Actions

### Pods Not Starting
```bash
# Check pod status
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>

# Verify secrets exist
kubectl get secret newssummariser-secrets
```

### Service Not Accessible
```bash
# Check service endpoints
kubectl get endpoints newssummariser-service

# Port forward for testing
kubectl port-forward svc/newssummariser-service 8501:8501
```

## Environment Variables

The application requires:
- `OPENAI_API_KEY`: Set in Kubernetes secret

## Scaling

```bash
# Scale deployment
kubectl scale deployment newssummariser --replicas=3

# Auto-scaling (requires metrics server)
kubectl autoscale deployment newssummariser --min=2 --max=5 --cpu-percent=80
```

