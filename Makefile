PYTHON ?= python3
BACKEND_DIR := backend
FRONTEND_DIR := frontend

.PHONY: install install-backend install-frontend test lint typecheck quality build-frontend smoke migrate backend-check frontend-check full-check

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
	$(MAKE) full-check

backend-check:
	bash scripts/quality/backend_check.sh

frontend-check:
	bash scripts/quality/frontend_check.sh

full-check:
	bash scripts/quality/full_check.sh

build-frontend:
	cd $(FRONTEND_DIR) && npm ci && npm run build

migrate:
	cd $(BACKEND_DIR) && $(PYTHON) manage.py migrate

smoke:
	bash scripts/smoke/runtime.sh
