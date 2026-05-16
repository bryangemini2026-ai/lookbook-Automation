#!/bin/bash
# Download recommended models for 8GB VRAM
set -euo pipefail

IMAGE_DIR="/opt/comfyui/image/models"
VIDEO_DIR="/opt/comfyui/video/models"

echo "=== Downloading Models ==="
echo "Target directories:"
echo "  Image: $IMAGE_DIR"
echo "  Video: $VIDEO_DIR"
echo ""

# ── Image Server Models ──

echo "[1/5] SDXL Base 1.0..."
wget -nc -P "$IMAGE_DIR/checkpoints/" \
    "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors" || true

echo "[2/5] Real-ESRGAN 4x..."
wget -nc -P "$IMAGE_DIR/upscale_models/" \
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/RealESRGAN_x4plus.pth" || true

echo "[3/5] 4x-UltraSharp..."
wget -nc -P "$IMAGE_DIR/upscale_models/" \
    "https://huggingface.co/Kim2091/UltraSharp/resolve/main/4x-UltraSharp.pth" || true

# ── Video Server Models ──

echo "[4/5] SD1.5 (AnimateDiff base)..."
wget -nc -P "$VIDEO_DIR/checkpoints/" \
    "https://huggingface.co/runwayml/stable-diffusion-v1-5/resolve/main/v1-5-pruned-emaonly.safetensors" || true

echo "[5/5] AnimateDiff v3 motion module..."
wget -nc -P "$VIDEO_DIR/animatediff/" \
    "https://huggingface.co/guoyww/animatediff/resolve/main/v3_sd15_mm.ckpt" || true

echo ""
echo "=== Model Download Complete ==="
echo ""
echo "Additional recommended models (manual download):"
echo "  - RealVisXL V4 (photorealistic SDXL): https://civitai.com/models/139562"
echo "  - IP-Adapter Plus SDXL: https://huggingface.co/h94/IP-Adapter"
echo "  - GFPGANv1.4 (face fix): https://github.com/TencentARC/GFPGAN"
