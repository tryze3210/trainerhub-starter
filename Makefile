PYTHON ?= python3
BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: install install-backend install-frontend test lint typecheck quality build-frontend smoke migrate

install: install-backend install-frontend

install-backend:
	$(PYTHON) -m pip install -r $(BACKEND_DIR)/requirements.txt

install-frontend:
	cd $(FRONTEND_DIR) && npm ci

test:
	cd $(BACKEND_DIR) && pytest

lint:
	flake8 $(BACKEND_DIR)

typecheck:
	mypy $(BACKEND_DIR)

quality:
	$(PYTHON) -m compileall $(BACKEND_DIR)
	$(MAKE) test
	$(MAKE) lint
	$(MAKE) typecheck
	$(MAKE) build-frontend

build-frontend:
	cd $(FRONTEND_DIR) && npm ci && npm run build

migrate:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate

smoke:
	bash scripts/smoke/runtime.sh
