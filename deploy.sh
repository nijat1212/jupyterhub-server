#!/usr/bin/env bash
# ==============================================================================
# Multi-User Secure JupyterHub Deployment Script
# Domain: https://jupyter.customser.az
# ==============================================================================
set -e

echo "=== 1. Checking Docker & Compose ==="
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    usermod -aG docker $USER
fi

# Ensure docker network exists
docker network inspect jupyterhub-network >/dev/null 2>&1 || docker network create jupyterhub-network

echo "=== 2. Creating persistent storage directories ==="
mkdir -p /opt/jupyterhub/data
chmod 777 /opt/jupyterhub/data

echo "=== 3. Building Custom Images ==="
# Hub image
docker build -t jupyterhub-custom:latest -f Dockerfile .

# Data Science image
docker build -t custom-datascience-notebook:latest -f Dockerfile.datascience .

# Pull minimal image
docker pull jupyter/minimal-notebook:latest

echo "=== 4. Configuring Nginx ==="
if command -v nginx &> /dev/null; then
    cp nginx/jupyterhub.conf /etc/nginx/sites-available/jupyterhub
    ln -sf /etc/nginx/sites-available/jupyterhub /etc/nginx/sites-enabled/jupyterhub
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
fi

echo "=== 5. Launching JupyterHub via Docker Compose ==="
docker compose down || true
docker compose up -d

echo "=========================================================="
echo " JupyterHub is now LIVE and fully configured!             "
echo "=========================================================="
