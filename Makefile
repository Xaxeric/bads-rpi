# BADS Camera Server Makefile
# Systemd service management for Raspberry Pi

# Variables
SERVICE_NAME = bads-camera
SERVICE_FILE = bads-camera.service
SYSTEMD_USER_DIR = $(HOME)/.config/systemd/user
TARGET_DIR = /opt/bads-rpi
CURRENT_DIR = $(shell pwd)
PYTHON = python3

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

.PHONY: help install uninstall start stop restart status logs enable disable info check-deps check-location move-project clean

# Default target
help:
	@echo "$(GREEN)BADS Camera Server - Makefile Commands$(NC)"
	@echo ""
	@echo "$(YELLOW)Setup Commands:$(NC)"
	@echo "  make install        - Install systemd service (user-level)"
	@echo "  make move-project   - Move project to /opt/bads-rpi"
	@echo "  make check-deps     - Check Python dependencies"
	@echo ""
	@echo "$(YELLOW)Service Management:$(NC)"
	@echo "  make start          - Start camera server"
	@echo "  make stop           - Stop camera server"
	@echo "  make restart        - Restart camera server"
	@echo "  make status         - Show service status"
	@echo "  make logs           - Show live logs"
	@echo ""
	@echo "$(YELLOW)Service Configuration:$(NC)"
	@echo "  make enable         - Enable auto-start on login"
	@echo "  make disable        - Disable auto-start on login"
	@echo ""
	@echo "$(YELLOW)Information:$(NC)"
	@echo "  make info           - Show server endpoints"
	@echo "  make check-location - Check if project is in correct location"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  make uninstall      - Remove systemd service"
	@echo "  make clean          - Clean temporary files"
	@echo ""
	@echo "$(YELLOW)Note:$(NC) User-level services start when you log in."

# Check if Python dependencies are installed
check-deps:
	@echo "$(YELLOW)Checking Python dependencies...$(NC)"
	@$(PYTHON) -c "import cv2; print('✓ OpenCV available')" || (echo "$(RED)✗ OpenCV missing$(NC)" && exit 1)
	@$(PYTHON) -c "import picamera2; print('✓ Picamera2 available')" || (echo "$(RED)✗ Picamera2 missing$(NC)" && exit 1)
	@$(PYTHON) -c "import flask; print('✓ Flask available')" || (echo "$(RED)✗ Flask missing$(NC)" && exit 1)
	@$(PYTHON) -c "import requests; print('✓ Requests available')" || (echo "$(RED)✗ Requests missing$(NC)" && exit 1)
	@echo "$(GREEN)✓ All Python dependencies found$(NC)"

# Check if project is in the correct location
check-location:
	@if [ "$(CURRENT_DIR)" = "$(TARGET_DIR)" ]; then \
		echo "$(GREEN)✓ Project is in correct location: $(TARGET_DIR)$(NC)"; \
	else \
		echo "$(YELLOW)⚠ Project is at: $(CURRENT_DIR)$(NC)"; \
		echo "$(YELLOW)⚠ Expected location: $(TARGET_DIR)$(NC)"; \
		echo "$(YELLOW)Run 'make move-project' to fix this$(NC)"; \
	fi

# Move project to the correct location
move-project:
	@echo "$(YELLOW)Moving project to $(TARGET_DIR)...$(NC)"
	@if [ "$(CURRENT_DIR)" = "$(TARGET_DIR)" ]; then \
		echo "$(GREEN)✓ Project is already in the correct location$(NC)"; \
	elif [ -d "$(TARGET_DIR)" ]; then \
		echo "$(RED)✗ Target directory already exists: $(TARGET_DIR)$(NC)"; \
		echo "Remove it first: sudo rm -rf $(TARGET_DIR)"; \
		exit 1; \
	else \
		sudo mkdir -p /opt; \
		sudo mv "$(CURRENT_DIR)" "$(TARGET_DIR)"; \
		sudo chown -R pi:pi "$(TARGET_DIR)"; \
		echo "$(GREEN)✓ Project moved to $(TARGET_DIR)$(NC)"; \
		echo "$(YELLOW)Change to new directory: cd $(TARGET_DIR)$(NC)"; \
	fi

# Install the systemd service (user-level)
install: check-deps check-location
	@echo "$(YELLOW)Installing $(SERVICE_NAME) systemd service (user-level)...$(NC)"
	@if [ "$(CURRENT_DIR)" != "$(TARGET_DIR)" ]; then \
		echo "$(RED)✗ Project must be at $(TARGET_DIR)$(NC)"; \
		echo "Run 'make move-project' first"; \
		exit 1; \
	fi
	@if [ ! -f "$(SERVICE_FILE)" ]; then \
		echo "$(RED)✗ Service file not found: $(SERVICE_FILE)$(NC)"; \
		exit 1; \
	fi
	@# Create user systemd directory if it doesn't exist
	mkdir -p $(SYSTEMD_USER_DIR)
	@# Create user service file (remove [Install] section for user services)
	@sed '/^\[Install\]/,$$d' $(SERVICE_FILE) > /tmp/$(SERVICE_NAME)-user.service
	@echo "" >> /tmp/$(SERVICE_NAME)-user.service
	@echo "[Install]" >> /tmp/$(SERVICE_NAME)-user.service
	@echo "WantedBy=default.target" >> /tmp/$(SERVICE_NAME)-user.service
	cp /tmp/$(SERVICE_NAME)-user.service $(SYSTEMD_USER_DIR)/$(SERVICE_NAME).service
	chmod 644 $(SYSTEMD_USER_DIR)/$(SERVICE_NAME).service
	systemctl --user daemon-reload
	systemctl --user enable $(SERVICE_NAME)
	@echo "$(GREEN)✓ User-level service installed and enabled$(NC)"
	@echo ""
	@echo "$(GREEN)Next steps:$(NC)"
	@echo "  make start    - Start the camera server"
	@echo "  make status   - Check service status"
	@echo "  make logs     - View live logs"
	@echo ""
	@echo "$(YELLOW)Note:$(NC) User services start when you log in."
	@rm -f /tmp/$(SERVICE_NAME)-user.service

# Start the service
start:
	@echo "$(YELLOW)Starting $(SERVICE_NAME) service...$(NC)"
	systemctl --user start $(SERVICE_NAME)
	@sleep 2
	@if systemctl --user is-active --quiet $(SERVICE_NAME); then \
		echo "$(GREEN)✓ Camera server started successfully$(NC)"; \
		make info; \
	else \
		echo "$(RED)✗ Failed to start camera server$(NC)"; \
		echo "Check logs with: make logs"; \
	fi

# Stop the service
stop:
	@echo "$(YELLOW)Stopping $(SERVICE_NAME) service...$(NC)"
	systemctl --user stop $(SERVICE_NAME)
	@echo "$(GREEN)✓ Camera server stopped$(NC)"

# Restart the service
restart:
	@echo "$(YELLOW)Restarting $(SERVICE_NAME) service...$(NC)"
	systemctl --user restart $(SERVICE_NAME)
	@sleep 2
	@if systemctl --user is-active --quiet $(SERVICE_NAME); then \
		echo "$(GREEN)✓ Camera server restarted successfully$(NC)"; \
		make info; \
	else \
		echo "$(RED)✗ Failed to restart camera server$(NC)"; \
		echo "Check logs with: make logs"; \
	fi

# Show service status
status:
	@echo "$(YELLOW)Service Status:$(NC)"
	@systemctl --user status $(SERVICE_NAME) --no-pager || true
	@echo ""
	@if systemctl --user is-active --quiet $(SERVICE_NAME); then \
		make info; \
	fi

# Show live logs
logs:
	@echo "$(YELLOW)Live logs (Ctrl+C to exit):$(NC)"
	journalctl --user -u $(SERVICE_NAME) -f

# Enable auto-start on login
enable:
	@echo "$(YELLOW)Enabling auto-start on login...$(NC)"
	systemctl --user enable $(SERVICE_NAME)
	@echo "$(GREEN)✓ Auto-start on login enabled$(NC)"

# Disable auto-start on login
disable:
	@echo "$(YELLOW)Disabling auto-start on login...$(NC)"
	systemctl --user disable $(SERVICE_NAME)
	@echo "$(GREEN)✓ Auto-start on login disabled$(NC)"

# Show server information and endpoints
info:
	@echo "$(GREEN)Camera Server Endpoints:$(NC)"
	@PI_IP=$$(hostname -I | awk '{print $$1}' | tr -d '\n'); \
	echo "  Single frame (ESP32): http://$${PI_IP}:5000/frame"; \
	echo "  MJPEG stream:         http://$${PI_IP}:5000/stream"; \
	echo "  Server info:          http://$${PI_IP}:5000/info"; \
	echo "  Main page:            http://$${PI_IP}:5000/"
	@echo ""
	@echo "$(GREEN)Database Integration:$(NC)"
	@echo "  Target server: 192.168.18.11:3000"
	@echo "  Endpoint: /api/capture"
	@echo ""

# Uninstall the user-level service
uninstall:
	@echo "$(YELLOW)Uninstalling $(SERVICE_NAME) service...$(NC)"
	-systemctl --user stop $(SERVICE_NAME) 2>/dev/null
	-systemctl --user disable $(SERVICE_NAME) 2>/dev/null
	-rm -f $(SYSTEMD_USER_DIR)/$(SERVICE_NAME).service
	systemctl --user daemon-reload
	@echo "$(GREEN)✓ Service uninstalled$(NC)"

# Clean temporary files
clean:
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	@rm -f /tmp/$(SERVICE_NAME).service
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# Install Python dependencies (requires sudo)
install-deps:
	@echo "$(YELLOW)Installing Python dependencies...$(NC)"
	sudo apt update
	sudo apt install -y python3-opencv python3-picamera2 python3-flask python3-requests
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

# Quick setup target (user-level only)
setup: move-project install start
	@echo "$(GREEN)✓ Complete setup finished!$(NC)"
	@echo "Camera server is running and enabled for auto-start on login."