# Docker Deployment Guide - Soniox Vapi Server

Deploy the Soniox custom transcriber for Vapi to your VPS using Docker.

## 📋 Prerequisites

- VPS with Docker and Docker Compose installed
- Your Soniox API key
- Domain name or static IP address
- SSL certificate (recommended) or Cloudflare Tunnel

## 🚀 Quick Deployment

### 1. Clone/Upload Your Project to VPS

```bash
# SSH into your VPS
ssh user@your-vps-ip

# Clone or upload your project
git clone your-repo-url
cd soniox_transcriber

# Or use rsync to upload
rsync -avz --exclude '.venv' --exclude '__pycache__' \
  /Users/fbotis/PERSONAL/soniox_transcriber/ \
  user@your-vps:/opt/soniox_transcriber/
```

### 2. Create Environment File

```bash
# Create .env file on your VPS
cat > .env << EOF
SONIOX_API_KEY=your_soniox_api_key_here
VAPI_SERVER_HOST=0.0.0.0
VAPI_SERVER_PORT=8080
EOF
```

### 3. Build and Run with Docker Compose

```bash
# Build the image
docker-compose build

# Start the service
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Verify It's Running

```bash
# Check health endpoint
curl http://localhost:8080/health
# Should return: OK

# Check container status
docker-compose ps
```

## 🔒 SSL/HTTPS Setup Options

### Option 1: Nginx Reverse Proxy with Let's Encrypt (Recommended)

Create `nginx.conf`:

```nginx
server {
    listen 80;
    server_name transcriber.yourdomain.com;

    location / {
        return 301 https://$server_name$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name transcriber.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/transcriber.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/transcriber.yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

Install Certbot and get SSL certificate:

```bash
# Install certbot
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d transcriber.yourdomain.com

# Auto-renewal is setup automatically
```

Update your Vapi config to use:
```
wss://transcriber.yourdomain.com/api/custom-transcriber
```

### Option 2: Cloudflare Tunnel (Easier, No SSL Config Needed)

```bash
# Install cloudflared
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Authenticate
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create soniox-transcriber

# Create config
cat > ~/.cloudflared/config.yml << EOF
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: transcriber.yourdomain.com
    service: http://localhost:8080
  - service: http_status:404
EOF

# Run tunnel
cloudflared tunnel run soniox-transcriber

# Or install as service
sudo cloudflared service install
sudo systemctl start cloudflared
```

Update your Vapi config to use:
```
wss://transcriber.yourdomain.com/api/custom-transcriber
```

### Option 3: Direct Public IP (Not Recommended for Production)

If you must use without SSL:

```bash
# Make sure firewall allows port 8080
sudo ufw allow 8080/tcp
```

Update your Vapi config to use:
```
ws://YOUR-VPS-IP:8080/api/custom-transcriber
```

⚠️ **Warning**: This is not secure. Use only for testing!

## 📊 Monitoring and Management

### View Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service logs
docker logs soniox-vapi-transcriber
```

### Restart Service

```bash
# Restart
docker-compose restart

# Stop
docker-compose stop

# Start
docker-compose start

# Rebuild and restart
docker-compose up -d --build
```

### Update Deployment

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up -d --build

# Or rebuild from scratch
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Configuration

### Environment Variables

Edit `.env` file:

```bash
# Required
SONIOX_API_KEY=your_key_here

# Optional
VAPI_SERVER_HOST=0.0.0.0
VAPI_SERVER_PORT=8080
```

### Resource Limits

Edit `docker-compose.yml` to adjust CPU/memory:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'          # Adjust based on your VPS
      memory: 1G           # Adjust based on your VPS
    reservations:
      cpus: '1.0'
      memory: 512M
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is already in use
sudo lsof -i :8080

# Check environment variables
docker-compose config
```

### Can't Connect from Vapi

```bash
# Test locally first
curl http://localhost:8080/health

# Check firewall
sudo ufw status

# Check if container is running
docker-compose ps

# Test WebSocket connection
wscat -c ws://localhost:8080/api/custom-transcriber
```

### High Memory Usage

```bash
# Check resource usage
docker stats soniox-vapi-transcriber

# Restart to clear memory
docker-compose restart

# Reduce resource limits in docker-compose.yml
```

### SSL Certificate Issues

```bash
# Renew certificate manually
sudo certbot renew

# Test certificate
sudo certbot certificates

# Check nginx config
sudo nginx -t
```

## 🔄 Auto-Start on Boot

Docker Compose with `restart: unless-stopped` will automatically restart the container on reboot.

To ensure Docker starts on boot:

```bash
sudo systemctl enable docker
```

## 📈 Production Best Practices

1. **Use SSL/TLS**: Always use HTTPS/WSS in production
2. **Monitor logs**: Set up log rotation and monitoring
3. **Backup**: Keep backups of your .env file and configuration
4. **Update regularly**: Keep Docker and images updated
5. **Use a process manager**: Consider using systemd for cloudflared or nginx
6. **Set up monitoring**: Use tools like Prometheus, Grafana, or Uptime Kuma
7. **Resource limits**: Set appropriate CPU/memory limits
8. **Firewall**: Only open necessary ports

## 📝 Updating Vapi Configuration

After deployment, update your Vapi assistant:

```bash
# Using the update script
VAPI_TRANSCRIBER_URL=wss://transcriber.yourdomain.com/api/custom-transcriber uv run python create_vapi_assistant.py
```

Or via curl:

```bash
curl -X PATCH https://api.vapi.ai/assistant/YOUR_ASSISTANT_ID \
  -H "Authorization: Bearer YOUR_VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "transcriber": {
      "provider": "custom-transcriber",
      "server": {
        "url": "wss://transcriber.yourdomain.com/api/custom-transcriber"
      }
    }
  }'
```

## 🆘 Getting Help

If you encounter issues:

1. Check container logs: `docker-compose logs -f`
2. Verify environment variables: `docker-compose config`
3. Test health endpoint: `curl http://localhost:8080/health`
4. Check Soniox API credits: https://console.soniox.com
5. Verify Vapi configuration in dashboard

## 📊 Example Systemd Service (Alternative to Docker Compose)

If you prefer systemd:

```bash
sudo cat > /etc/systemd/system/soniox-vapi.service << EOF
[Unit]
Description=Soniox Vapi Transcriber
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/soniox_transcriber
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable soniox-vapi
sudo systemctl start soniox-vapi
```

## ✅ Checklist

- [ ] VPS has Docker and Docker Compose installed
- [ ] Project files uploaded to VPS
- [ ] .env file created with SONIOX_API_KEY
- [ ] Container built and running
- [ ] Health endpoint returns OK
- [ ] SSL/HTTPS configured (Nginx or Cloudflare)
- [ ] Firewall configured
- [ ] Vapi assistant updated with new URL
- [ ] Test call successful
- [ ] Logs show transcriptions working
- [ ] Auto-restart on boot enabled

Your Soniox Vapi transcriber is now deployed and ready for production! 🚀
