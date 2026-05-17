#!/bin/bash
# Deploy script for Computer A
# Pulls latest changes and restarts services
#
# Usage:
#   bash scripts/deploy.sh              # Full deploy
#   bash scripts/deploy.sh --gateway    # Restart gateway only
#   bash scripts/deploy.sh --worker     # Restart worker only
#   bash scripts/deploy.sh --status     # Show current version + status

set -euo pipefail

PROJECT_DIR="/opt/lookbook"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
VERSION_FILE="$REPO_DIR/VERSION"

# ── Colors ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()  { echo -e "${GREEN}[deploy]${NC} $*"; }
warn() { echo -e "${YELLOW}[deploy]${NC} $*"; }
err()  { echo -e "${RED}[deploy]${NC} $*" >&2; }

# ── Version ──
get_version() {
    if [ -f "$VERSION_FILE" ]; then
        head -1 "$VERSION_FILE"
    else
        echo "unknown"
    fi
}

show_status() {
    echo "=== Lookbook Deploy Status ==="
    echo "Version:  $(get_version)"
    echo "Commit:   $(git -C "$REPO_DIR" rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo "Branch:   $(git -C "$REPO_DIR" branch --show-current 2>/dev/null || echo 'unknown')"
    echo ""
    echo "Services:"
    systemctl is-active lookbook-gateway 2>/dev/null && echo "  Gateway:  running" || echo "  Gateway:  stopped"
    systemctl is-active lookbook-worker 2>/dev/null && echo "  Worker:   running" || echo "  Worker:   stopped"
    systemctl is-active lookbook-watcher 2>/dev/null && echo "  Watcher:  running" || echo "  Watcher:  stopped"
    systemctl is-active comfyui-image 2>/dev/null && echo "  ComfyUI Image: running" || echo "  ComfyUI Image: stopped"
    systemctl is-active comfyui-video 2>/dev/null && echo "  ComfyUI Video: running" || echo "  ComfyUI Video: stopped"
    echo ""
    echo "Redis:    $(redis-cli ping 2>/dev/null || echo 'unavailable')"
}

# ── Deploy ──
deploy() {
    local component="${1:-all}"

    log "Starting deploy... (current: $(get_version))"

    # Pull latest changes
    log "Pulling latest changes..."
    cd "$REPO_DIR"
    git pull origin main --ff-only || {
        err "Git pull failed. Resolve conflicts manually."
        exit 1
    }

    NEW_VERSION=$(get_version)
    log "Updated to: $NEW_VERSION"

    # Install/update Python deps
    if [ "$component" = "all" ] || [ "$component" = "gateway" ]; then
        log "Updating gateway dependencies..."
        cd "$REPO_DIR/gateway"
        source venv/bin/activate
        pip install -r requirements.txt -q 2>/dev/null || true
    fi

    if [ "$component" = "all" ] || [ "$component" = "worker" ]; then
        log "Updating worker dependencies..."
        cd "$REPO_DIR/worker"
        source venv/bin/activate
        pip install -r requirements.txt -q 2>/dev/null || true
    fi

    # Install dashboard deps
    if [ "$component" = "all" ]; then
        log "Updating dashboard dependencies..."
        cd "$REPO_DIR/dashboard"
        npm install --silent 2>/dev/null || true
    fi

    # Copy systemd services if changed
    log "Updating systemd services..."
    sudo cp "$REPO_DIR/scripts/"*.service /etc/systemd/system/ 2>/dev/null || true
    sudo systemctl daemon-reload

    # Restart services
    if [ "$component" = "all" ] || [ "$component" = "gateway" ]; then
        log "Restarting gateway..."
        sudo systemctl restart lookbook-gateway 2>/dev/null || warn "Gateway restart failed (not installed as service)"
    fi

    if [ "$component" = "all" ] || [ "$component" = "worker" ]; then
        log "Restarting worker..."
        sudo systemctl restart lookbook-worker 2>/dev/null || warn "Worker restart failed (not installed as service)"
        sudo systemctl restart lookbook-watcher 2>/dev/null || warn "Watcher restart failed (not installed as service)"
    fi

    log "Deploy complete! Version: $(get_version)"
}

# ── Main ──
case "${1:-all}" in
    --status|-s)
        show_status
        ;;
    --gateway|-g)
        deploy gateway
        ;;
    --worker|-w)
        deploy worker
        ;;
    --help|-h)
        echo "Usage: deploy.sh [--status|--gateway|--worker|--help]"
        echo ""
        echo "  (no args)    Full deploy: pull + restart all services"
        echo "  --status     Show current version and service status"
        echo "  --gateway    Restart gateway only"
        echo "  --worker     Restart worker only"
        ;;
    *)
        deploy all
        ;;
esac
