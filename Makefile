SHELL := /bin/bash

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

FRONTEND_DIR := frontend

HOST := 127.0.0.1
BACKEND_PORT := 8000
FRONTEND_PORT := 5173

.PHONY: help install install-back install-front backend frontend dev

help:
	@echo "Доступные команды:"
	@echo "  make install       - установить зависимости бэка и фронта"
	@echo "  make install-back  - установить зависимости бэка"
	@echo "  make install-front - установить зависимости фронта"
	@echo "  make backend       - запустить FastAPI"
	@echo "  make frontend      - запустить Vite frontend"
	@echo "  make dev           - запустить бэк и фронт одновременно"

install: install-back install-front

install-back:
	$(PIP) install -r requirements.txt

install-front:
	cd $(FRONTEND_DIR) && npm install

backend:
	$(PYTHON) -m uvicorn app.main:app --reload --host $(HOST) --port $(BACKEND_PORT)

frontend:
	cd $(FRONTEND_DIR) && npm run dev -- --host $(HOST) --port $(FRONTEND_PORT)

dev:
	@trap 'kill 0' SIGINT SIGTERM EXIT; \
	$(MAKE) backend & \
	$(MAKE) frontend & \
	wait