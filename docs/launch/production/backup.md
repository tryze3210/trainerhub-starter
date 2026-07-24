# Backup And Restore

## Backup Requirements

- Automated database backups are enabled.
- Backup retention matches the legal and operational retention policy.
- Object storage/media backups are enabled for protected course/video assets.
- Finance documents and audit exports are included in backup scope.

## Manual Database Backup

Use this before risky maintenance, migration windows or incident response when the managed backup point is not recent enough:

```bash
DATABASE_URL="$DATABASE_URL" BACKUP_DIR="./backups/postgres" bash scripts/ops/backup_postgres.sh
```

The script writes a gzip-compressed plain SQL dump and a `.sha256` checksum. Keep generated files outside the deploy artifact and upload them to the approved backup store.

## Restore Drill

1. Identify target restore timestamp.
2. Restore database into an isolated environment.
3. Run the isolated restore verification:

```bash
BACKUP_FILE="./backups/postgres/trainerhub-postgres-YYYYMMDDTHHMMSSZ.sql.gz" \
RESTORE_DATABASE_URL="$RESTORE_DATABASE_URL" \
RESTORE_TARGET_ISOLATED=1 \
RUN_DJANGO_CHECK=1 \
bash scripts/ops/verify_postgres_restore.sh
```

4. Restore object storage/media references.
5. Run `python manage.py check`.
6. Run `python manage.py check_production_readiness --json`.
7. Validate orders, payments, entitlements, payouts and audit trails.

## Production Incident Notes

- Use `ops/runbooks/database-restore.md` for incident execution.
- Do not overwrite production until restore integrity is proven.
- Record restore actor, timestamp, source backup and verification result in audit notes.
