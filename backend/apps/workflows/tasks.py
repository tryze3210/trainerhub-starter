from __future__ import annotations


def dispatch_outbox_batch() -> dict:
    return {'status': 'scheduled', 'task': 'dispatch_outbox_batch', 'batch_size': 100}


def rebuild_projection(projection_key: str) -> dict:
    return {'status': 'scheduled', 'task': 'rebuild_projection', 'projection_key': projection_key}
