# Production bootstrap runbook

## 1. Environment
1. Copy `.env.example` to `.env`.
2. Replace `SECRET_KEY`, `POSTGRES_PASSWORD`, `VK_CLOUD_*`, `SENTRY_DSN`.
3. Set `DEBUG=0` and production `ALLOWED_HOSTS`.

## 2. Build and start
```bash
docker compose --env-file .env up --build -d
```

## 3. Verify runtime
- `GET /api/v1/runtime/health/`
- `GET /api/v1/runtime/readiness/`
- `GET /api/v1/runtime/config/`
- Flower behind `/flower/`

## 4. Minimal hardening checklist
- terminate TLS before nginx or replace nginx config with TLS-enabled config
- restrict Flower access at network/proxy layer
- move secrets out of `.env` into secret manager
- attach persistent volumes and backups for Postgres / Redis
- enable structured logging and shipping to Loki/ELK
- configure Sentry and OTel exporter

## 5. Celery queues
- `default` — generic domain jobs
- `media` — transcoding / probe / upload callbacks
- `notifications` — fanout / digest / delivery retries
- `billing` — provider callbacks / payout orchestration
