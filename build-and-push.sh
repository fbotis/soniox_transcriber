#!/bin/bash
# Script to build and tag the Soniox Vapi Transcriber Docker image

set -e

IMAGE_NAME="soniox-vapi-transcriber"
TAG="${1:-latest}"

echo "Building Docker image: ${IMAGE_NAME}:${TAG}"

# Build the image
docker build -t ${IMAGE_NAME}:${TAG} .

echo "✅ Image built successfully: ${IMAGE_NAME}:${TAG}"
echo ""
echo "To save and transfer to your VPS:"
echo "  docker save ${IMAGE_NAME}:${TAG} | gzip > soniox-vapi-transcriber.tar.gz"
echo "  scp soniox-vapi-transcriber.tar.gz user@your-vps:/tmp/"
echo "  ssh user@your-vps 'docker load < /tmp/soniox-vapi-transcriber.tar.gz'"
echo ""
echo "Or push to a registry:"
echo "  docker tag ${IMAGE_NAME}:${TAG} your-registry/${IMAGE_NAME}:${TAG}"
echo "  docker push your-registry/${IMAGE_NAME}:${TAG}"
