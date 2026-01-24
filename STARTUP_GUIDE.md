# Startup Guide - After Restarting Your Laptop

## Quick Start

After restarting your laptop, simply run:

```bash
./start-app.sh
```

This script will:
1. ✅ Start minikube (if not running)
2. ✅ Check if pods are running
3. ✅ Start port-forwarding (connects Kubernetes → localhost)
4. ✅ Start Cloudflare Tunnel (connects domain → localhost)

## Manual Steps (if script doesn't work)

### Step 1: Start Minikube

```bash
minikube start
```

Wait until you see: `✅ Done! kubectl is now configured...`

### Step 2: Verify Pods Are Running

```bash
kubectl get pods
```

You should see pods with status `Running`. If not, deploy them:

```bash
./k8s/deploy-minikube.sh YOUR_OPENAI_API_KEY
```

### Step 3: Start Port-Forwarding

This connects your Kubernetes service to `localhost:8501`:

```bash
kubectl port-forward service/newssummariser-service 8501:8501 8000:8000
```

**Keep this terminal open!** Or run it in background:

```bash
kubectl port-forward service/newssummariser-service 8501:8501 8000:8000 > /tmp/port-forward.log 2>&1 &

### Step 4: Start Cloudflare Tunnel

This connects `news.deestore.in` to `localhost:8501`:

```bash
cloudflared tunnel run news-summariser
```

**Keep this terminal open!** Or run it in background:

```bash
cloudflared tunnel run news-summariser > /tmp/tunnel.log 2>&1 &
```

## Check Status

```bash
./check-status.sh
```

This will show you:
- ✅ Minikube status
- ✅ Pod status
- ✅ Port-forwarding status
- ✅ Tunnel status
- ✅ Test connectivity

## Stop Everything

```bash
./stop-app.sh
```

This stops port-forwarding and tunnel (but keeps minikube running).

## Troubleshooting

### "Bad Gateway" Error

This usually means port-forwarding or tunnel is not running:

1. **Check port-forwarding:**
   ```bash
   ps aux | grep "kubectl port-forward"
   ```
   If not running, restart it (Step 3 above)

2. **Check tunnel:**
   ```bash
   ps aux | grep cloudflared
   ```
   If not running, restart it (Step 4 above)

3. **Check localhost:**
   ```bash
   curl http://localhost:8501
   ```
   Should return HTML. If not, check pods:
   ```bash
   kubectl get pods
   kubectl logs <pod-name>
   ```

### Pods Not Running

```bash
# Check pod status
kubectl get pods

# Check pod logs
kubectl logs <pod-name>

# Restart deployment
kubectl rollout restart deployment/newssummariser
```

### Tunnel Connection Issues

```bash
# Check tunnel logs
tail -f /tmp/tunnel.log

# Restart tunnel
pkill -f cloudflared
cloudflared tunnel run news-summariser > /tmp/tunnel.log 2>&1 &
```

## Auto-Start (Optional)

To automatically start everything on boot, you can:

1. **Create a Launch Agent** (macOS):
   ```bash
   # Create plist file
   cat > ~/Library/LaunchAgents/com.news.summariser.plist << EOF
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.news.summariser</string>
       <key>ProgramArguments</key>
       <array>
           <string>/bin/bash</string>
           <string>/Users/deep/Desktop/MyProjects/NewsSummariser/start-app.sh</string>
       </array>
       <key>RunAtLoad</key>
       <true/>
       <key>KeepAlive</key>
       <false/>
   </dict>
   </plist>
   EOF
   
   # Load it
   launchctl load ~/Library/LaunchAgents/com.news.summariser.plist
   ```

2. **Or use a simple cron job** (runs on login):
   ```bash
   crontab -e
   # Add: @reboot /Users/deep/Desktop/MyProjects/NewsSummariser/start-app.sh
   ```

## Summary

**After every restart:**
1. Run `./start-app.sh` (or follow manual steps)
2. Wait 30 seconds
3. Visit https://news.deestore.in

That's it! 🎉

