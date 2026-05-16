#!/bin/bash
# Full GPU server setup for Computer A (Ubuntu)
set -euo pipefail

echo "=== Lookbook GPU Server Setup ==="

# 1. System dependencies
echo "[1/8] Installing system dependencies..."
sudo apt update && sudo apt install -y \
    python3.11 python3.11-venv python3-pip \
    git ffmpeg samba redis-server \
    inotify-tools curl

# 2. NVIDIA driver check
echo "[2/8] Checking NVIDIA driver..."
if ! nvidia-smi &>/dev/null; then
    echo "WARNING: nvidia-smi not found. Install NVIDIA drivers first:"
    echo "  sudo apt install nvidia-driver-535"
    echo "  sudo reboot"
    exit 1
fi
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv

# 3. Create lookbook user
echo "[3/8] Creating lookbook user..."
if ! id lookbook &>/dev/null; then
    sudo useradd -m -s /bin/bash lookbook
    sudo usermod -aG sudo lookbook
fi

# 4. Create directory structure
echo "[4/8] Creating directory structure..."
sudo mkdir -p /opt/lookbook/{data,gateway,worker,scripts}
sudo mkdir -p /opt/comfyui/{image,video}
sudo mkdir -p /srv/lookbook/{inbox,outbox,processed,brand,bgm}
sudo chown -R lookbook:lookbook /opt/lookbook /srv/lookbook /opt/comfyui

# 5. Install ComfyUI Image Server
echo "[5/8] Setting up ComfyUI Image Server..."
if [ ! -f /opt/comfyui/image/main.py ]; then
    sudo -u lookbook git clone https://github.com/comfyanonymous/ComfyUI.git /opt/comfyui/image
    cd /opt/comfyui/image
    sudo -u lookbook python3.11 -m venv venv
    sudo -u lookbook /opt/comfyui/image/venv/bin/pip install -r requirements.txt
    echo "  Image server cloned. Custom nodes need manual installation."
else
    echo "  Image server already exists, skipping."
fi

# 6. Install ComfyUI Video Server
echo "[6/8] Setting up ComfyUI Video Server..."
if [ ! -f /opt/comfyui/video/main.py ]; then
    sudo -u lookbook git clone https://github.com/comfyanonymous/ComfyUI.git /opt/comfyui/video
    cd /opt/comfyui/video
    sudo -u lookbook python3.11 -m venv venv
    sudo -u lookbook /opt/comfyui/video/venv/bin/pip install -r requirements.txt
    echo "  Video server cloned. Custom nodes need manual installation."
else
    echo "  Video server already exists, skipping."
fi

# 7. Set up PipelineWorker
echo "[7/8] Setting up PipelineWorker..."
sudo -u lookbook cp -r worker/* /opt/lookbook/worker/
cd /opt/lookbook/worker
sudo -u lookbook python3.11 -m venv venv
sudo -u lookbook /opt/lookbook/worker/venv/bin/pip install -r requirements.txt

# 8. Set up FastAPI Gateway
echo "[8/8] Setting up FastAPI Gateway..."
sudo -u lookbook cp -r gateway/* /opt/lookbook/gateway/
cd /opt/lookbook/gateway
sudo -u lookbook python3.11 -m venv venv
sudo -u lookbook /opt/lookbook/gateway/venv/bin/pip install -r requirements.txt

# Copy .env
if [ ! -f /opt/lookbook/.env ]; then
    sudo -u lookbook cp .env.example /opt/lookbook/.env
    echo "  Edit /opt/lookbook/.env with your settings."
fi

# Copy gpu-guard.sh
sudo cp scripts/gpu-guard.sh /opt/lookbook/scripts/
sudo chmod +x /opt/lookbook/scripts/gpu-guard.sh

# Install systemd services
echo "Installing systemd services..."
sudo cp scripts/comfyui-image.service /etc/systemd/system/
sudo cp scripts/comfyui-video.service /etc/systemd/system/
sudo cp scripts/lookbook-gateway.service /etc/systemd/system/
sudo cp scripts/lookbook-worker.service /etc/systemd/system/
sudo cp scripts/lookbook-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /opt/lookbook/.env"
echo "  2. Download models: bash scripts/download_models.sh"
echo "  3. Install ComfyUI custom nodes manually"
echo "  4. Start services:"
echo "     sudo systemctl start redis-server"
echo "     sudo systemctl start lookbook-gateway"
echo "     sudo systemctl start lookbook-worker"
echo "     sudo systemctl start lookbook-watcher"
echo "  5. Start ComfyUI when ready:"
echo "     sudo systemctl start comfyui-image"
