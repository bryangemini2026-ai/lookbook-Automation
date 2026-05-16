.PHONY: help gateway worker dashboard setup-gpu setup-samba

help:
	@echo "=== Lookbook SNS Automation ==="
	@echo ""
	@echo "  make gateway        Run FastAPI gateway (port 8000)"
	@echo "  make worker         Run PipelineWorker"
	@echo "  make dashboard      Run Vite dev server (port 5173)"
	@echo "  make watcher        Run watch folder daemon"
	@echo ""
	@echo "  make setup-gpu      Full GPU server setup (Computer A)"
	@echo "  make setup-samba    Configure Samba shared folder"
	@echo "  make download-models  Download ComfyUI models"
	@echo ""
	@echo "  make gpu-status     Show GPU server status"
	@echo "  make gpu-start-image  Start image server"
	@echo "  make gpu-stop-image   Stop image server"
	@echo "  make gpu-start-video  Start video server"
	@echo "  make gpu-stop-video   Stop video server"
	@echo ""

# ── Development ──

gateway:
	cd gateway && source venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

worker:
	cd worker && source venv/bin/activate && python main.py

dashboard:
	cd dashboard && npm run dev

watcher:
	cd worker && source venv/bin/activate && python watcher.py

# ── GPU Control ──

gpu-status:
	@bash scripts/gpu-guard.sh status

gpu-start-image:
	sudo systemctl start comfyui-image

gpu-stop-image:
	sudo systemctl stop comfyui-image

gpu-start-video:
	sudo systemctl start comfyui-video

gpu-stop-video:
	sudo systemctl stop comfyui-video

# ── Setup ──

setup-gpu:
	bash scripts/setup_gpu_server.sh

setup-samba:
	bash scripts/setup_samba.sh

download-models:
	bash scripts/download_models.sh
