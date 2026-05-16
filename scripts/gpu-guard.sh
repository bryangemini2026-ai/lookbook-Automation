#!/bin/bash
# /opt/lookbook/scripts/gpu-guard.sh
#
# GPU mutual exclusion for dual ComfyUI servers.
# Ensures only one server occupies the GPU at a time.
#
# Called by systemd ExecStartPre/ExecStopPost.
# CRITICAL: systemd passes the 2nd argument ($2) as the caller identity.
#   ExecStartPre=/opt/lookbook/scripts/gpu-guard.sh check image
#   ExecStopPost=/opt/lookbook/scripts/gpu-guard.sh cleanup image
#
# Usage:
#   gpu-guard.sh check <image|video>    — pre-start: verify + lock
#   gpu-guard.sh cleanup <image|video>  — post-stop: unlock + VRAM cleanup
#   gpu-guard.sh switch <image|video>   — runtime: stop other + start target
#   gpu-guard.sh status                 — query current state

set -euo pipefail

ACTION="${1:-}"
CALLER="${2:-}"

IMAGE_LOCK="/tmp/comfyui-image.lock"
VIDEO_LOCK="/tmp/comfyui-video.lock"

# ── helper: kill leftover ComfyUI processes and free VRAM ──
force_cleanup_gpu() {
    local port="$1"  # 8188 or 8288

    # 1. Kill any python process listening on the given port
    local pids
    pids=$(fuser "${port}/tcp" 2>/dev/null | xargs || true)
    if [ -n "$pids" ]; then
        echo "gpu-guard: killing leftover processes on :${port} (PIDs: ${pids})"
        kill -9 $pids 2>/dev/null || true
        sleep 1
    fi

    # 2. Kill any orphan comfyui/python that still holds GPU memory
    #    Match by port in cmdline to avoid killing unrelated python processes
    pkill -9 -f "main.py.*--port ${port}" 2>/dev/null || true
    sleep 1

    # 3. Verify GPU memory is freed
    local vram_used
    vram_used=$(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>/dev/null || echo "0")
    if [ "$vram_used" -gt 500 ] 2>/dev/null; then
        echo "gpu-guard: WARNING — GPU still using ${vram_used}MB after cleanup"
    else
        echo "gpu-guard: GPU memory cleared (${vram_used}MB used)"
    fi
}

case "$ACTION" in
    # ── Pre-start check ──
    check)
        if [ -z "$CALLER" ]; then
            echo "ERROR: usage: gpu-guard.sh check <image|video>"
            exit 1
        fi

        # Check if the OTHER server holds the lock
        if [ "$CALLER" = "image" ] && [ -f "$VIDEO_LOCK" ]; then
            echo "ERROR: Video server is running. Stop it first or use 'switch image'."
            exit 1
        fi
        if [ "$CALLER" = "video" ] && [ -f "$IMAGE_LOCK" ]; then
            echo "ERROR: Image server is running. Stop it first or use 'switch video'."
            exit 1
        fi

        # Acquire lock
        touch "/tmp/comfyui-${CALLER}.lock"
        echo "gpu-guard: lock acquired for ${CALLER} server."
        ;;

    # ── Post-stop cleanup ──
    cleanup)
        if [ -z "$CALLER" ]; then
            echo "ERROR: usage: gpu-guard.sh cleanup <image|video>"
            exit 1
        fi

        # Release lock
        rm -f "/tmp/comfyui-${CALLER}.lock"
        echo "gpu-guard: lock released for ${CALLER} server."

        # Force-kill leftover processes and free VRAM
        if [ "$CALLER" = "image" ]; then
            force_cleanup_gpu 8188
        else
            force_cleanup_gpu 8288
        fi
        ;;

    # ── Runtime switch (stop other → clean → start target) ──
    switch)
        TARGET="${2:-}"
        if [ -z "$TARGET" ] || [[ "$TARGET" != "image" && "$TARGET" != "video" ]]; then
            echo "ERROR: usage: gpu-guard.sh switch <image|video>"
            exit 1
        fi

        if [ "$TARGET" = "image" ]; then
            echo "gpu-guard: switching to IMAGE server..."
            echo "gpu-guard: stopping video server..."
            systemctl stop comfyui-video 2>/dev/null || true
            sleep 2
            force_cleanup_gpu 8288
            echo "gpu-guard: starting image server..."
            systemctl start comfyui-image
        else
            echo "gpu-guard: switching to VIDEO server..."
            echo "gpu-guard: stopping image server..."
            systemctl stop comfyui-image 2>/dev/null || true
            sleep 2
            force_cleanup_gpu 8188
            echo "gpu-guard: starting video server..."
            systemctl start comfyui-video
        fi
        ;;

    # ── Status query ──
    status)
        echo "=== GPU Server Status ==="
        if [ -f "$IMAGE_LOCK" ]; then
            echo "Image server (:8188): RUNNING"
        else
            echo "Image server (:8188): STOPPED"
        fi
        if [ -f "$VIDEO_LOCK" ]; then
            echo "Video server (:8288): RUNNING"
        else
            echo "Video server (:8288): STOPPED"
        fi
        echo ""
        echo "=== GPU Memory ==="
        nvidia-smi --query-gpu=memory.used,memory.total,temperature.gpu --format=csv 2>/dev/null || echo "nvidia-smi unavailable"
        ;;

    *)
        echo "usage: gpu-guard.sh <check|cleanup|switch|status> [image|video]"
        exit 1
        ;;
esac
