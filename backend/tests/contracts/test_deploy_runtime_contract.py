from pathlib import Path
import subprocess


def test_backend_entrypoint_does_not_run_database_migrations():
    repo_root = Path(__file__).resolve().parents[3]
    entrypoint = (repo_root / 'deploy' / 'backend' / 'entrypoint.sh').read_text()
    release = (repo_root / 'deploy' / 'backend' / 'release.sh').read_text()
    compose = (repo_root / 'docker-compose.yml').read_text()

    assert 'manage.py migrate' not in entrypoint
    assert 'collectstatic' not in entrypoint
    assert 'gunicorn config.wsgi:application' in entrypoint
    assert 'manage.py migrate --noinput' in release
    assert 'collectstatic --noinput' in release
    assert '  release:' in compose
    assert '/app/deploy/backend/release.sh' in compose
    assert 'image: ${BACKEND_IMAGE:-trainerhub-backend:local}' in compose
    assert 'image: ${FRONTEND_IMAGE:-trainerhub-frontend:local}' in compose


def test_celery_worker_default_queues_cover_routed_tasks():
    repo_root = Path(__file__).resolve().parents[3]
    worker = (repo_root / 'deploy' / 'backend' / 'celery-worker.sh').read_text()
    celery_config = (repo_root / 'backend' / 'config' / 'celery.py').read_text()

    assert 'CELERY_WORKER_QUEUES:-default,outbox,ops,email,media,notifications,billing' in worker
    assert '--queues="${CELERY_WORKER_QUEUES' in worker
    for queue in ('OUTBOX_QUEUE', 'OPS_QUEUE', 'EMAIL_QUEUE', 'DEFAULT_QUEUE'):
        assert queue in celery_config
    for queue_name in ('default', 'outbox', 'ops', 'email'):
        assert queue_name in worker


def test_outbox_compose_overlay_uses_canonical_backend_image():
    repo_root = Path(__file__).resolve().parents[3]
    overlay = (repo_root / 'docker-compose.outbox.yml').read_text()

    assert 'dockerfile: deploy/backend/Dockerfile' in overlay
    assert 'docker/celery/Dockerfile' not in overlay
    assert 'context: .' in overlay
    assert '${TRAINERHUB_ENV_FILE:-.env}' in overlay
    assert 'cd /app/backend' in overlay
    assert '--queues=outbox,default' in overlay


def test_deploy_scripts_run_preflight_before_release_job():
    repo_root = Path(__file__).resolve().parents[3]
    deploy = (repo_root / 'scripts' / 'deploy' / 'deploy.sh').read_text()
    migrate = (repo_root / 'scripts' / 'deploy' / 'migrate.sh').read_text()

    assert ': "${REGISTRY:?REGISTRY is required}"' in deploy
    assert ': "${IMAGE_TAG:?IMAGE_TAG is required}"' in deploy
    assert 'BACKEND_IMAGE="${REGISTRY}/trainerhub-backend:${IMAGE_TAG}"' in deploy
    assert 'FRONTEND_IMAGE="${REGISTRY}/trainerhub-frontend:${IMAGE_TAG}"' in deploy
    assert ': "${REGISTRY:?REGISTRY is required}"' in migrate
    assert 'BACKEND_IMAGE="${REGISTRY}/trainerhub-backend:${IMAGE_TAG}"' in migrate

    for script in (deploy, migrate):
        deploy_check_index = script.index('python manage.py check --deploy --fail-level WARNING')
        readiness_index = script.index('python manage.py check_production_readiness --summary-only --fail-on-degraded')
        release_index = script.index('docker compose run --rm release')
        assert deploy_check_index < release_index
        assert readiness_index < release_index


def test_dockerignore_excludes_sensitive_and_heavy_local_artifacts():
    repo_root = Path(__file__).resolve().parents[3]
    dockerignore = (repo_root / '.dockerignore').read_text()

    required_patterns = [
        '.env',
        '.env.*',
        '**/.env',
        '**/.env.*',
        '!.env.example',
        '!.env.backend.example',
        '!.env.frontend.example',
        'backend/.venv/',
        'backend/db.sqlite3',
        'backend/test.sqlite3',
        '**/*.sqlite3',
        'frontend/.next/',
        'frontend/node_modules/',
        'frontend/test-results/',
        'frontend/playwright-report/',
        '.coverage',
        'coverage/',
        'htmlcov/',
    ]
    for pattern in required_patterns:
        assert pattern in dockerignore


def test_compose_config_works_without_image_environment_variables():
    repo_root = Path(__file__).resolve().parents[3]
    result = subprocess.run(
        ['docker', 'compose', '-f', 'docker-compose.yml', 'config', '--quiet'],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert 'variable is not set' not in result.stderr


def test_frontend_dockerfile_matches_next_standalone_output():
    repo_root = Path(__file__).resolve().parents[3]
    dockerfile = (repo_root / 'deploy' / 'frontend' / 'Dockerfile').read_text()
    next_config = (repo_root / 'frontend' / 'next.config.ts').read_text()

    assert "output: 'standalone'" in next_config
    assert 'COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/standalone ./' in dockerfile
    assert 'COPY --from=builder --chown=nextjs:nodejs /app/frontend/.next/static ./.next/static' in dockerfile
    assert 'CMD ["node", "server.js"]' in dockerfile
    assert 'NEXT_TELEMETRY_DISABLED=1' in dockerfile
    assert 'NEXT_PUBLIC_API_BASE_URL' in dockerfile


def test_nginx_proxy_preserves_forwarded_headers_and_blocks_flower():
    repo_root = Path(__file__).resolve().parents[3]
    nginx = (repo_root / 'deploy' / 'nginx' / 'nginx.conf').read_text()

    assert 'map $http_upgrade $connection_upgrade' in nginx
    assert 'proxy_set_header X-Forwarded-Host $host;' in nginx
    assert 'proxy_set_header X-Forwarded-Port $server_port;' in nginx
    assert 'proxy_set_header Upgrade $http_upgrade;' in nginx
    assert 'proxy_set_header Connection $connection_upgrade;' in nginx
    assert 'add_header X-Content-Type-Options "nosniff" always;' in nginx
    assert 'add_header X-Frame-Options "DENY" always;' in nginx
    assert 'add_header Referrer-Policy "strict-origin-when-cross-origin" always;' in nginx
    assert 'location /flower/' in nginx
    assert 'return 404;' in nginx


def test_database_backup_and_restore_scripts_are_safe_and_executable():
    repo_root = Path(__file__).resolve().parents[3]
    backup = repo_root / 'scripts' / 'ops' / 'backup_postgres.sh'
    restore = repo_root / 'scripts' / 'ops' / 'verify_postgres_restore.sh'
    backup_source = backup.read_text()
    restore_source = restore.read_text()

    assert backup.stat().st_mode & 0o111
    assert restore.stat().st_mode & 0o111
    assert 'set -euo pipefail' in backup_source
    assert 'set -euo pipefail' in restore_source
    assert ': "${DATABASE_URL:?DATABASE_URL is required}"' in backup_source
    assert 'pg_dump --no-owner --no-privileges --format=plain "$DATABASE_URL"' in backup_source
    assert 'sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"' in backup_source
    assert ': "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL is required}"' in restore_source
    assert ': "${RESTORE_TARGET_ISOLATED:?Set RESTORE_TARGET_ISOLATED=1' in restore_source
    assert 'RESTORE_TARGET_ISOLATED" != "1"' in restore_source
    assert 'gzip -t "$BACKUP_FILE"' in restore_source
    assert 'gzip -cd "$BACKUP_FILE" | psql "$RESTORE_DATABASE_URL" --set ON_ERROR_STOP=1' in restore_source
