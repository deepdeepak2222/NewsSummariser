# Docker Hub Setup Guide

## Step-by-Step Instructions

### 1. Create Docker Hub Access Token

1. **Go to Docker Hub Security Settings**
   - Visit: https://hub.docker.com/settings/security
   - Or: Docker Hub → Account Settings → Security

2. **Create New Access Token**
   - Click **"New Access Token"** button
   - **Description**: `GitHub Actions - NewsSummariser` (or any descriptive name)
   - **Permissions**: Select **"Read & Write"** (required to push images)
   - Click **"Generate"**

3. **Copy the Token**
   - ⚠️ **IMPORTANT**: Copy the token immediately
   - You won't be able to see it again after closing the dialog
   - Save it securely (you'll need it in the next step)

### 2. Add Secrets to GitHub

1. **Go to Your Repository**
   - Visit: https://github.com/deepdeepak2222/NewsSummariser
   - Or navigate to: `Settings` → `Secrets and variables` → `Actions`

2. **Add First Secret: DOCKERHUB_USERNAME**
   - Click **"New repository secret"**
   - **Name**: `DOCKERHUB_USERNAME`
   - **Value**: `deepdeepak2222`
   - Click **"Add secret"**

3. **Add Second Secret: DOCKERHUB_TOKEN**
   - Click **"New repository secret"** again
   - **Name**: `DOCKERHUB_TOKEN`
   - **Value**: `<paste your Docker Hub access token here>`
   - Click **"Add secret"**

### 3. Verify Setup

After adding secrets, the CI/CD pipeline will automatically:
- Build Docker image on every push to `main` branch
- Push to Docker Hub: `deepdeepak2222/newssummariser:latest`
- Tag images with branch names and commit SHAs

### 4. Test the Pipeline

1. **Make a small change** (or just push again)
2. **Go to Actions tab** in GitHub repository
3. **Watch the workflow run**
4. **Check Docker Hub** after completion:
   - Visit: https://hub.docker.com/repository/docker/deepdeepak2222/newssummariser
   - You should see the new image

## Troubleshooting

### Token Not Working
- Verify token has **Read & Write** permissions
- Check token hasn't expired
- Ensure username matches exactly: `deepdeepak2222`

### Build Fails
- Check GitHub Actions logs
- Verify Dockerfile syntax
- Ensure all dependencies are in requirements.txt

### Push Fails
- Verify `DOCKERHUB_TOKEN` secret is set correctly
- Check token permissions include "Write"
- Ensure repository name matches: `deepdeepak2222/newssummariser`

## Manual Docker Build (Optional)

To test locally before CI/CD:

```bash
# Build image
docker build -t deepdeepak2222/newssummariser:latest .

# Login to Docker Hub
docker login -u deepdeepak2222

# Push image
docker push deepdeepak2222/newssummariser:latest
```

