# Soniox Vapi Server - Standalone

Minimal standalone server for Vapi custom transcriber using Soniox API.

## 🎯 What's This?

This is a **minimal version** of the Soniox transcriber server with **only the dependencies needed** for the Vapi server. No PyAudio, no pynput, no dictation features - just the WebSocket server for Vapi.

Perfect for Docker deployment on Linux VPS!

## 📦 Dependencies

Only 3 pure Python packages (no system dependencies):
- `websockets` - WebSocket client for Soniox
- `aiohttp` - Web server for Vapi connections
- `python-dotenv` - Environment variable management

## 🚀 Quick Start

### Local Testing

```bash
cd vapi_server_standalone

# Install dependencies
pip install -e .

# Set API key
export SONIOX_API_KEY=your_key_here

# Run server
soniox-vapi-server
```

### Docker Build

```bash
cd vapi_server_standalone

# Build image
docker build -t soniox-vapi-transcriber:latest .

# Run container
docker run -d \
  -p 8080:8080 \
  -e SONIOX_API_KEY=your_key_here \
  --name soniox-vapi \
  soniox-vapi-transcriber:latest

# Check logs
docker logs -f soniox-vapi

# Test health
curl http://localhost:8080/health
```

## 🚢 Deploy to VPS

### Step 1: Build and Save Image

```bash
# Build
docker build -t soniox-vapi-transcriber:latest .

# Save to tar
docker save soniox-vapi-transcriber:latest | gzip > soniox-vapi.tar.gz

# Upload to VPS
scp soniox-vapi.tar.gz user@your-vps:/tmp/
```

### Step 2: Load on VPS

```bash
# SSH to VPS
ssh user@your-vps

# Load image
docker load < /tmp/soniox-vapi.tar.gz
```

### Step 3: Add to docker-compose.yml

```yaml
services:
  soniox-vapi-transcriber:
    image: soniox-vapi-transcriber:latest
    container_name: soniox-vapi-transcriber
    restart: unless-stopped
    environment:
      - SONIOX_API_KEY=${SONIOX_API_KEY}
      - VAPI_SERVER_HOST=0.0.0.0
      - VAPI_SERVER_PORT=8080
      - VIRTUAL_HOST=transcriber.yourdomain.com
      - VIRTUAL_PORT=8080
      - LETSENCRYPT_HOST=transcriber.yourdomain.com
      - LETSENCRYPT_EMAIL=your@email.com
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

### Step 4: Start Service

```bash
docker-compose up -d soniox-vapi-transcriber
docker-compose logs -f soniox-vapi-transcriber
```

## ✅ Verify

```bash
# Health check
curl https://transcriber.yourdomain.com/health

# Should return: OK
```

## 🔧 Configuration

Environment variables:

- `SONIOX_API_KEY` - Your Soniox API key (required)
- `VAPI_SERVER_HOST` - Server host (default: 0.0.0.0)
- `VAPI_SERVER_PORT` - Server port (default: 8080)

## 📊 Endpoints

- `GET /health` - Health check endpoint
- `GET /api/custom-transcriber` - WebSocket endpoint for Vapi

## 🎯 Vapi Configuration

Use this URL in your Vapi assistant:

```
wss://transcriber.yourdomain.com/api/custom-transcriber
```

## 🐛 Troubleshooting

### Build fails on Linux

This standalone version has **no system dependencies**, so it should build on any Linux system without issues.

### Container won't start

```bash
# Check logs
docker logs soniox-vapi

# Verify API key is set
docker exec soniox-vapi env | grep SONIOX
```

### Can't connect from Vapi

```bash
# Test locally
curl http://localhost:8080/health

# Check if nginx-proxy is routing correctly
docker logs nginx-proxy | grep transcriber
```

## 📝 Project Structure

```
vapi_server_standalone/
├── src/
│   └── soniox_vapi/
│       ├── __init__.py
│       └── server.py          # Main server code
├── Dockerfile                  # Docker build file
├── pyproject.toml             # Minimal dependencies
├── .dockerignore
├── .env.example
└── README.md
```

## 🎉 Benefits of Standalone Version

- ✅ **No system dependencies** - Pure Python only
- ✅ **Smaller Docker image** - ~300MB vs 1GB+
- ✅ **Faster builds** - No compiling PyAudio, etc.
- ✅ **Works on any Linux** - No PortAudio, audio libs needed
- ✅ **Minimal attack surface** - Fewer dependencies
- ✅ **Easier to maintain** - Simple dependency tree

Perfect for production deployment! 🚀
