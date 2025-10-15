# Deployment to Your VPS (techvantage.es)

Complete guide to deploy the Soniox Vapi Transcriber to your VPS with your existing docker-compose setup.

## 📋 Prerequisites

- Your VPS at techvantage.es with Docker and Docker Compose
- Your existing webproxy network
- DNS record for transcriber.techvantage.es pointing to your VPS IP
- Soniox API key

## 🚀 Step-by-Step Deployment

### Step 1: Build the Docker Image Locally

```bash
# On your Mac, in the soniox_transcriber directory
cd /Users/fbotis/PERSONAL/soniox_transcriber

# Make the build script executable
chmod +x build-and-push.sh

# Build the image
./build-and-push.sh

# Or build manually
docker build -t soniox-vapi-transcriber:latest .
```

### Step 2: Transfer Image to VPS

**Option A: Save and Upload (Recommended for your setup)**

```bash
# Save the image to a tar file
docker save soniox-vapi-transcriber:latest | gzip > soniox-vapi-transcriber.tar.gz

# Upload to your VPS
scp soniox-vapi-transcriber.tar.gz fbotis@techvantage.es:/tmp/

# SSH to VPS and load the image
ssh fbotis@techvantage.es
cd /tmp
docker load < soniox-vapi-transcriber.tar.gz
rm soniox-vapi-transcriber.tar.gz
```

**Option B: Build Directly on VPS**

```bash
# Upload project files to VPS
rsync -avz --exclude '.venv' --exclude '__pycache__' --exclude '*.pyc' \
  /Users/fbotis/PERSONAL/soniox_transcriber/ \
  fbotis@techvantage.es:/home/fbotis/soniox_transcriber/

# SSH to VPS and build
ssh fbotis@techvantage.es
cd /home/fbotis/soniox_transcriber
docker build -t soniox-vapi-transcriber:latest .
```

### Step 3: Configure DNS

Make sure DNS is set up:

```bash
# Check DNS resolution
nslookup transcriber.techvantage.es

# Or
dig transcriber.techvantage.es
```

It should point to your VPS IP address.

### Step 4: Add Service to Your docker-compose.yml

On your VPS, edit your main `docker-compose.yml` file and add the soniox-vapi-transcriber service:

```yaml
# Add this to your services section:

  soniox-vapi-transcriber:
    image: soniox-vapi-transcriber:latest
    container_name: soniox-vapi-transcriber
    restart: unless-stopped
    environment:
      # Soniox API Key (required)
      - SONIOX_API_KEY=${SONIOX_API_KEY}

      # Server configuration
      - VAPI_SERVER_HOST=0.0.0.0
      - VAPI_SERVER_PORT=8080

      # Nginx Proxy Configuration
      - VIRTUAL_HOST=transcriber.techvantage.es
      - VIRTUAL_PORT=8080
      - LETSENCRYPT_HOST=transcriber.techvantage.es
      - LETSENCRYPT_EMAIL=florin.botis@gmail.com

    networks:
      - webproxy

    # Health check
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health')\" || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Step 5: Add SONIOX_API_KEY to Environment

On your VPS, add the API key to your environment file:

```bash
# If you have a .env file in your docker-compose directory
echo "SONIOX_API_KEY=your_soniox_api_key_here" >> .env

# Or export it
export SONIOX_API_KEY=your_soniox_api_key_here
```

### Step 6: Start the Service

```bash
# Navigate to your docker-compose directory
cd /home/fbotis/monitoring-stack  # or wherever your docker-compose.yml is

# Start the new service
docker-compose up -d soniox-vapi-transcriber

# Check logs
docker-compose logs -f soniox-vapi-transcriber
```

### Step 7: Verify It's Working

```bash
# Check container status
docker-compose ps soniox-vapi-transcriber

# Test health endpoint
curl http://localhost:8080/health
# Should return: OK

# Test via domain (after SSL is set up)
curl https://transcriber.techvantage.es/health
# Should return: OK

# Check SSL certificate
curl -I https://transcriber.techvantage.es/health
```

### Step 8: Update Vapi Configuration

Now update your Vapi assistant to use the new URL:

```bash
curl -X PATCH https://api.vapi.ai/assistant/bf61ffaa-d5a7-4537-9a69-a76a4c78c723 \
  -H "Authorization: Bearer YOUR_VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "transcriber": {
      "provider": "custom-transcriber",
      "server": {
        "url": "wss://transcriber.techvantage.es/api/custom-transcriber"
      }
    }
  }'
```

## ✅ Verification Checklist

- [ ] DNS points transcriber.techvantage.es to VPS IP
- [ ] Docker image built and loaded on VPS
- [ ] Service added to docker-compose.yml
- [ ] SONIOX_API_KEY set in environment
- [ ] Container is running (`docker-compose ps`)
- [ ] Health endpoint returns OK
- [ ] SSL certificate issued by Let's Encrypt
- [ ] Vapi assistant updated with new URL
- [ ] Test call shows transcriptions in logs

## 📊 Monitoring and Logs

```bash
# View logs
docker-compose logs -f soniox-vapi-transcriber

# Check container stats
docker stats soniox-vapi-transcriber

# Check health
docker inspect soniox-vapi-transcriber | grep -A 10 Health
```

## 🔄 Updating the Service

When you make changes:

```bash
# On your Mac: Rebuild image
docker build -t soniox-vapi-transcriber:latest .
docker save soniox-vapi-transcriber:latest | gzip > soniox-vapi-transcriber.tar.gz
scp soniox-vapi-transcriber.tar.gz fbotis@techvantage.es:/tmp/

# On VPS: Load and restart
ssh fbotis@techvantage.es
docker load < /tmp/soniox-vapi-transcriber.tar.gz
cd /home/fbotis/monitoring-stack
docker-compose up -d soniox-vapi-transcriber
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker-compose logs soniox-vapi-transcriber

# Check if SONIOX_API_KEY is set
docker-compose exec soniox-vapi-transcriber env | grep SONIOX
```

### SSL Certificate Not Issued

```bash
# Check acme-companion logs
docker-compose logs acme-companion

# Manually trigger certificate
docker exec acme-companion /app/signal_le_service
```

### Can't Connect from Vapi

```bash
# Test WebSocket locally
docker exec -it soniox-vapi-transcriber python -c "
import asyncio
from websockets import connect

async def test():
    async with connect('ws://localhost:8080/api/custom-transcriber') as ws:
        print('WebSocket connected!')

asyncio.run(test())
"

# Check nginx-proxy config
docker exec nginx-proxy cat /etc/nginx/conf.d/default.conf | grep transcriber
```

### Port Conflicts

If port 8080 is already used by cadvisor:

```yaml
# Change VIRTUAL_PORT in your service config
environment:
  - VIRTUAL_PORT=8082  # or any available port
```

## 📝 Complete docker-compose.yml Service Entry

Here's the complete service configuration to add to your docker-compose.yml:

```yaml
services:
  # ... your existing services ...

  soniox-vapi-transcriber:
    image: soniox-vapi-transcriber:latest
    container_name: soniox-vapi-transcriber
    restart: unless-stopped
    environment:
      - SONIOX_API_KEY=${SONIOX_API_KEY}
      - VAPI_SERVER_HOST=0.0.0.0
      - VAPI_SERVER_PORT=8080
      - VIRTUAL_HOST=transcriber.techvantage.es
      - VIRTUAL_PORT=8080
      - LETSENCRYPT_HOST=transcriber.techvantage.es
      - LETSENCRYPT_EMAIL=florin.botis@gmail.com
    networks:
      - webproxy
    healthcheck:
      test: ["CMD-SHELL", "python -c \"import urllib.request; urllib.request.urlopen('http://localhost:8080/health')\" || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🎯 Final URL

Your transcriber will be available at:
```
wss://transcriber.techvantage.es/api/custom-transcriber
```

Use this URL in your Vapi assistant configuration!

## 🔒 Security Notes

- SSL/TLS is automatically handled by nginx-proxy and acme-companion
- The service is only accessible via the nginx-proxy (no direct port exposure)
- Health endpoint is public but safe (read-only)
- WebSocket endpoint requires proper Vapi authentication

Your deployment is complete! The service will automatically restart on server reboot and renew SSL certificates. 🚀
