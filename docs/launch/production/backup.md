# Backup And Restore

## Backup Requirements

- Automated database backups are enabled.
- Backup retention matches the legal and operational retention policy.
- Object storage/media backups are enabled for protected course/video assets.
- Finance documents and audit exports are included in backup scope.

## Restore Drill

1. Identify target restore timestamp.
2. Restore database into an isolated environment.
3. Restore object storage/media references.
4. Run `python manage.py check`.
5. Run `python manage.py check_production_readiness --json`.
6. Validate orders, payments, entitlements, payouts and audit trails.

## Production Incident Notes

- Use `ops/runbooks/database-restore.md` for incident execution.
- Do not overwrite production until restore integrity is proven.
- Record restore actor, timestamp, source backup and verification result in audit notes.
