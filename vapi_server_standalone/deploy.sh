#!/bin/bash
# Quick deploy script for Soniox Vapi Server

set -e

VPS_USER="fbotis"
VPS_HOST="techvantage.es"
VPS_COMPOSE_DIR="/home/fbotis/monitoring-stack"

echo "🔨 Building Docker image..."
docker build -t soniox-vapi-transcriber:latest .

echo "📦 Saving image..."
docker save soniox-vapi-transcriber:latest | gzip > soniox-vapi.tar.gz

echo "📤 Uploading to VPS..."
scp soniox-vapi.tar.gz ${VPS_USER}@${VPS_HOST}:/tmp/

echo "🚀 Deploying on VPS..."
ssh ${VPS_USER}@${VPS_HOST} << 'EOF'
  echo "Loading new image..."
  docker load < /tmp/soniox-vapi.tar.gz
  rm /tmp/soniox-vapi.tar.gz

  echo "Restarting service..."
  cd /home/fbotis/monitoring-stack
  docker-compose up -d soniox-vapi-transcriber

  echo "✅ Deployment complete!"
  echo "Showing logs (Ctrl+C to exit):"
  docker-compose logs --tail=50 -f soniox-vapi-transcriber
EOF

echo "🎉 Done! Cleaning up local tar file..."
rm soniox-vapi.tar.gz

echo "✅ Deployment successful!"
