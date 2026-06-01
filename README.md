# TrainerHub v61 — admin audit retention summary

Safe files-only archive. No scripts, no patch files.

Adds a read-only admin endpoint:

```text
GET /api/v1/audit/admin/retention/summary/
```

It helps the platform owner inspect audit table growth before implementing a destructive retention policy.

## Apply

From repository root:

```bash
cp -a trainerhub_v61_admin_audit_retention_summary_verified_files/backend .
cp -a trainerhub_v61_admin_audit_retention_summary_verified_files/docs .
```

## Verify

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest tests/test_audit_v58_admin_filters.py \
       tests/test_audit_v60_admin_csv_export.py \
       tests/test_audit_v61_retention_summary.py -q
```
