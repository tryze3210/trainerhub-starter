from __future__ import annotations

# Backward-compatible Celery app module. Existing commands that use
# `celery -A config.celery_app ...` continue to work, while the canonical app is
# now `config.celery`.
from config.celery import app

__all__ = ['app']
