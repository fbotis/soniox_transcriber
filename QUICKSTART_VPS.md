# Quick Start - Deploy to techvantage.es VPS

## 🚀 5-Minute Deployment

### 1. Build Image (on your Mac)

```bash
cd /Users/fbotis/PERSONAL/soniox_transcriber
docker build -t soniox-vapi-transcriber:latest .
docker save soniox-vapi-transcriber:latest | gzip > soniox-vapi-transcriber.tar.gz
```

### 2. Upload to VPS

```bash
scp soniox-vapi-transcriber.tar.gz fbotis@techvantage.es:/tmp/
```

### 3. Load on VPS

```bash
ssh fbotis@techvantage.es

# Load image
docker load < /tmp/soniox-vapi-transcriber.tar.gz
rm /tmp/soniox-vapi-transcriber.tar.gz

# Add API key to environment
cd /home/fbotis/monitoring-stack  # your docker-compose directory
echo "SONIOX_API_KEY=your_actual_soniox_api_key" >> .env
```

### 4. Add Service to docker-compose.yml

Edit your `docker-compose.yml` and add this service:

```yaml
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
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### 5. Make sure DNS is set

```bash
# Check DNS
nslookup transcriber.techvantage.es
# Should point to your VPS IP
```

### 6. Start Service

```bash
docker-compose up -d soniox-vapi-transcriber
docker-compose logs -f soniox-vapi-transcriber
```

### 7. Test

```bash
# Wait for SSL cert (1-2 minutes)
curl https://transcriber.techvantage.es/health
# Should return: OK
```

### 8. Update Vapi

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

## ✅ Done!

Your transcriber is now live at: `wss://transcriber.techvantage.es/api/custom-transcriber`

Make a test call and check logs: `docker-compose logs -f soniox-vapi-transcriber`
