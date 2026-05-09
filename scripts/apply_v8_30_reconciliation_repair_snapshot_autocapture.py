#!/usr/bin/env python3
from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path.cwd()
BACKEND = ROOT / "backend"
OPS = BACKEND / "apps" / "ops"
API = OPS / "api"
TESTS = BACKEND / "tests"
DOCS = ROOT / "docs" / "ops"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def backup(path: Path) -> None:
    backup_path = path.with_suffix(path.suffix + ".v8_30.bak")
    if path.exists() and not backup_path.exists():
        shutil.copy2(path, backup_path)


def ensure_backend() -> None:
    required = [
        OPS / "repair.py",
        OPS / "reconciliation_snapshots.py",
        API / "views.py",
        API / "urls.py",
        API / "repair_serializers.py",
        API / "snapshot_serializers.py",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise SystemExit("v8.30 patch must be run from trainerhub-starter repository root. Missing:\n" + "\n".join(missing))


def ensure_reconciliation_snapshot_helpers() -> None:
    path = OPS / "reconciliation_snapshots.py"
    backup(path)
    text = read(path)
    if "def capture_repair_reconciliation_snapshot" in text and "def get_latest_reconciliation_snapshot" in text:
        return

    append = '''


def _repair_snapshot_metric(snapshot_payload: dict[str, Any], key: str) -> int:
    value = snapshot_payload.get(key)
    if value is None:
        value = (snapshot_payload.get('summary') or {}).get(key)
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _repair_snapshot_correlation_id(repair_payload: dict[str, Any]) -> str:
    audit_event_id = str(repair_payload.get('audit_event_id') or '')
    action = str(repair_payload.get('action') or 'repair')
    entity_type = str(repair_payload.get('entity_type') or '')
    entity_id = str(repair_payload.get('entity_id') or '')
    if audit_event_id:
        return f'repair:{audit_event_id}'[:128]
    return f'repair:{action}:{entity_type}:{entity_id}'[:128]


def _repair_snapshot_summary(
    *,
    snapshot_payload: dict[str, Any],
    previous: ReconciliationSnapshot | None,
    repair_payload: dict[str, Any],
) -> dict[str, Any]:
    current_problem_count = _repair_snapshot_metric(snapshot_payload, 'total_issues')
    current_critical_count = _repair_snapshot_metric(snapshot_payload, 'critical_count')
    current_warning_count = _repair_snapshot_metric(snapshot_payload, 'warning_count')

    previous_problem_count = int(previous.total_issues) if previous else None
    previous_critical_count = int(previous.critical_count) if previous else None
    previous_warning_count = int(previous.warning_count) if previous else None

    problem_delta = None if previous_problem_count is None else current_problem_count - previous_problem_count
    critical_delta = None if previous_critical_count is None else current_critical_count - previous_critical_count
    warning_delta = None if previous_warning_count is None else current_warning_count - previous_warning_count
    improved = bool(problem_delta is not None and (critical_delta or 0) <= 0 and problem_delta < 0)
    worsened = bool(problem_delta is not None and ((critical_delta or 0) > 0 or problem_delta > 0))

    return _json_safe({
        'status': 'captured',
        'source': ReconciliationSnapshot.Source.REPAIR,
        'snapshot_id': snapshot_payload.get('id'),
        'href': snapshot_payload.get('href'),
        'generated_at': snapshot_payload.get('generated_at'),
        'snapshot_status': snapshot_payload.get('status'),
        'has_previous': previous is not None,
        'previous_snapshot_id': str(previous.id) if previous else None,
        'previous_problem_count': previous_problem_count,
        'current_problem_count': current_problem_count,
        'problem_delta': problem_delta,
        'previous_critical_count': previous_critical_count,
        'current_critical_count': current_critical_count,
        'critical_delta': critical_delta,
        'previous_warning_count': previous_warning_count,
        'current_warning_count': current_warning_count,
        'warning_delta': warning_delta,
        'improved': improved,
        'worsened': worsened,
        'repair': {
            'action': repair_payload.get('action'),
            'status': repair_payload.get('status'),
            'changed': repair_payload.get('changed'),
            'entity_type': repair_payload.get('entity_type'),
            'entity_id': repair_payload.get('entity_id'),
            'audit_event_id': repair_payload.get('audit_event_id'),
        },
        'snapshot': snapshot_payload,
    })


def capture_repair_reconciliation_snapshot(
    *,
    repair_payload: dict[str, Any],
    request=None,
    limit: int = ReconciliationSnapshotService.DEFAULT_LIMIT,
) -> dict[str, Any]:
    """Capture source=repair snapshot after a successful repair action.

    The previous snapshot is read before capture, so the response can immediately
    show whether the repair reduced the total/critical/warning issue counts.
    """
    previous = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()
    snapshot_payload = capture_reconciliation_snapshot(
        limit=limit,
        source=ReconciliationSnapshot.Source.REPAIR,
        correlation_id=_repair_snapshot_correlation_id(repair_payload),
        request=request,
    )
    return _repair_snapshot_summary(
        snapshot_payload=snapshot_payload,
        previous=previous,
        repair_payload=repair_payload,
    )


def get_latest_reconciliation_snapshot(
    *,
    source: str = '',
    status: str = '',
    include_report: bool = False,
) -> dict[str, Any]:
    qs = ReconciliationSnapshot.objects.all().order_by('-generated_at', '-created_at')
    if source:
        qs = qs.filter(source=source)
    if status:
        qs = qs.filter(status=status)
    latest = qs.first()
    if latest is None:
        return _json_safe({
            'status': 'missing',
            'generated_at': timezone.now(),
            'filters': {'source': source, 'status': status, 'include_report': include_report},
            'snapshot': None,
        })
    previous = qs.exclude(pk=latest.pk).first()
    return _json_safe({
        'status': 'ok',
        'generated_at': timezone.now(),
        'filters': {'source': source, 'status': status, 'include_report': include_report},
        'snapshot': _snapshot_to_dict(latest, include_report=include_report, previous=previous),
    })
'''
    write(path, text.rstrip() + append + "\n")


def insert_repair_autocapture() -> None:
    path = OPS / "repair.py"
    backup(path)
    text = read(path)
    if "capture_repair_reconciliation_snapshot" in text:
        return

    audit_pos = text.find("payload['audit'] =")
    if audit_pos == -1:
        raise SystemExit("Could not find payload['audit'] assignment in backend/apps/ops/repair.py")

    match = re.search(r"\n(?P<indent>[ \t]+)return payload\b", text[audit_pos:])
    if not match:
        raise SystemExit("Could not find return payload after audit block in backend/apps/ops/repair.py")
    insert_at = audit_pos + match.start()
    indent = match.group('indent')
    block = f'''
{indent}try:
{indent}    from apps.ops.reconciliation_snapshots import capture_repair_reconciliation_snapshot

{indent}    repair_snapshot = capture_repair_reconciliation_snapshot(repair_payload=payload, request=request)
{indent}    payload['repair_snapshot'] = repair_snapshot
{indent}    payload['reconciliation_snapshot_id'] = str(repair_snapshot.get('snapshot_id') or '')
{indent}    payload['reconciliation_snapshot_href'] = str(repair_snapshot.get('href') or '')
{indent}    payload['reconciliation_snapshot_source'] = 'repair'
{indent}    payload['previous_problem_count'] = repair_snapshot.get('previous_problem_count')
{indent}    payload['current_problem_count'] = repair_snapshot.get('current_problem_count')
{indent}    payload['problem_delta'] = repair_snapshot.get('problem_delta')
{indent}    payload['improved'] = bool(repair_snapshot.get('improved', False))
{indent}except Exception as exc:  # snapshot capture must not rollback an already completed repair
{indent}    payload['repair_snapshot'] = {{'status': 'failed', 'source': 'repair', 'error': str(exc)}}
{indent}    payload['reconciliation_snapshot_id'] = ''
{indent}    payload['reconciliation_snapshot_href'] = ''
{indent}    payload['reconciliation_snapshot_source'] = 'repair'
{indent}    payload['previous_problem_count'] = None
{indent}    payload['current_problem_count'] = None
{indent}    payload['problem_delta'] = None
{indent}    payload['improved'] = False
'''
    text = text[:insert_at] + block + text[insert_at:]
    write(path, text)


def patch_repair_serializer() -> None:
    path = API / "repair_serializers.py"
    backup(path)
    text = read(path)
    if "repair_snapshot = serializers.DictField" in text:
        return

    marker = " audit = serializers.DictField(required=False)"
    if marker not in text:
        # fallback for conventional 4-space indentation
        marker = "    audit = serializers.DictField(required=False)"
    if marker not in text:
        raise SystemExit("Could not find audit field in repair_serializers.py")

    indent = re.match(r"([ \t]*)", marker).group(1)
    addition = f'''
{indent}reconciliation_snapshot_id = serializers.CharField(required=False, allow_blank=True)
{indent}reconciliation_snapshot_href = serializers.CharField(required=False, allow_blank=True)
{indent}reconciliation_snapshot_source = serializers.CharField(required=False, allow_blank=True)
{indent}previous_problem_count = serializers.IntegerField(required=False, allow_null=True)
{indent}current_problem_count = serializers.IntegerField(required=False, allow_null=True)
{indent}problem_delta = serializers.IntegerField(required=False, allow_null=True)
{indent}improved = serializers.BooleanField(required=False)
{indent}repair_snapshot = serializers.DictField(required=False)
'''
    text = text.replace(marker, marker + addition, 1)
    write(path, text)


def patch_snapshot_serializer() -> None:
    path = API / "snapshot_serializers.py"
    backup(path)
    text = read(path)
    if "class AdminReconciliationSnapshotLatestSerializer" in text:
        return

    append = '''

class AdminReconciliationSnapshotLatestSerializer(serializers.Serializer):
 limit = None
 source = serializers.ChoiceField(
  required=False,
  allow_blank=True,
  choices=(('', 'Any'), ('manual', 'Manual'), ('scheduled', 'Scheduled'), ('repair', 'Repair'), ('ci', 'CI')),
  default='',
 )
 status = serializers.ChoiceField(
  required=False,
  allow_blank=True,
  choices=(('', 'Any'), ('ok', 'OK'), ('degraded', 'Degraded'), ('critical', 'Critical')),
  default='',
 )
 include_report = serializers.BooleanField(required=False, default=False)
'''
    # Put latest serializer before trend serializer when possible, otherwise append.
    trend_marker = "class AdminReconciliationSnapshotTrendSerializer"
    if trend_marker in text:
        text = text.replace(trend_marker, append + "\n" + trend_marker, 1)
    else:
        text = text.rstrip() + append + "\n"
    write(path, text)


def patch_views() -> None:
    path = API / "views.py"
    backup(path)
    text = read(path)

    if "AdminReconciliationSnapshotLatestView" not in text:
        # serializer import
        text = text.replace(
            "AdminReconciliationSnapshotListSerializer,",
            "AdminReconciliationSnapshotListSerializer,\n AdminReconciliationSnapshotLatestSerializer,",
            1,
        )
        # service import
        text = text.replace(
            "get_reconciliation_snapshot_trend,",
            "get_reconciliation_snapshot_trend,\n get_latest_reconciliation_snapshot,",
            1,
        )
        view_class = '''

class AdminReconciliationSnapshotLatestView(APIView):
 """Latest persisted reconciliation snapshot, usually source=repair for post-repair checks."""
 permission_classes = [IsAdminUser]

 def get(self, request):
  serializer = AdminReconciliationSnapshotLatestSerializer(data=request.query_params)
  serializer.is_valid(raise_exception=True)
  payload = get_latest_reconciliation_snapshot(**serializer.validated_data)
  return Response(payload)
'''
        marker = "class AdminReconciliationSnapshotCaptureView(APIView):"
        if marker not in text:
            raise SystemExit("Could not find AdminReconciliationSnapshotCaptureView in views.py")
        text = text.replace(marker, view_class + "\n" + marker, 1)
        write(path, text)
    else:
        if "get_latest_reconciliation_snapshot" not in text:
            raise SystemExit("views.py already has AdminReconciliationSnapshotLatestView but service import is missing; patch manually.")


def patch_urls() -> None:
    path = API / "urls.py"
    backup(path)
    text = read(path)
    if "reconciliation-snapshots/latest" in text:
        return

    text = text.replace(
        "AdminReconciliationSnapshotListView,",
        "AdminReconciliationSnapshotListView,\n AdminReconciliationSnapshotLatestView,",
        1,
    )
    marker = " path('admin/reconciliation-snapshots/capture/', AdminReconciliationSnapshotCaptureView.as_view(), name='ops-admin-reconciliation-snapshot-capture'),"
    if marker not in text:
        # fallback: add after list route
        marker = " path('admin/reconciliation-snapshots/', AdminReconciliationSnapshotListView.as_view(), name='ops-admin-reconciliation-snapshots'),"
        addition_after = True
    else:
        addition_after = False
    if marker not in text:
        raise SystemExit("Could not find reconciliation snapshot routes in urls.py")
    route = " path('admin/reconciliation-snapshots/latest/', AdminReconciliationSnapshotLatestView.as_view(), name='ops-admin-reconciliation-snapshot-latest'),"
    if addition_after:
        text = text.replace(marker, marker + "\n" + route, 1)
    else:
        text = text.replace(marker, route + "\n" + marker, 1)
    write(path, text)


def write_tests() -> None:
    path = TESTS / "test_ops_reconciliation_repair_snapshot_autocapture.py"
    if path.exists():
        return
    write(path, '''from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import pytest
from django.utils import timezone


@pytest.mark.django_db
def test_capture_repair_reconciliation_snapshot_compares_against_previous(monkeypatch):
    from apps.ops.models import ReconciliationSnapshot
    from apps.ops.reconciliation_snapshots import capture_repair_reconciliation_snapshot

    previous = ReconciliationSnapshot.objects.create(
        status=ReconciliationSnapshot.Status.CRITICAL,
        source=ReconciliationSnapshot.Source.MANUAL,
        total_issues=5,
        critical_count=2,
        warning_count=3,
        info_count=0,
        summary={'total_issues': 5, 'critical_count': 2, 'warning_count': 3, 'info_count': 0},
        section_statuses={},
        report={},
    )

    def fake_report(*, limit=100):
        return {
            'status': 'degraded',
            'generated_at': timezone.now(),
            'summary': {'total_issues': 3, 'critical_count': 1, 'warning_count': 2, 'info_count': 0},
            'sections': {},
        }

    monkeypatch.setattr('apps.ops.reconciliation_snapshots.get_money_reconciliation_report', fake_report)

    payload = capture_repair_reconciliation_snapshot(
        repair_payload={
            'action': 'retry_outbox',
            'status': 'accepted',
            'changed': True,
            'entity_type': 'outbox_message',
            'entity_id': 'msg-1',
            'audit_event_id': 'audit-1',
        },
        request=None,
    )

    created = ReconciliationSnapshot.objects.order_by('-generated_at', '-created_at').first()
    assert created is not None
    assert created.source == ReconciliationSnapshot.Source.REPAIR
    assert created.correlation_id == 'repair:audit-1'
    assert payload['snapshot_id'] == str(created.id)
    assert payload['previous_snapshot_id'] == str(previous.id)
    assert payload['previous_problem_count'] == 5
    assert payload['current_problem_count'] == 3
    assert payload['problem_delta'] == -2
    assert payload['critical_delta'] == -1
    assert payload['improved'] is True


def test_repair_execute_returns_snapshot_summary_without_hiding_repair_result(monkeypatch):
    from apps.ops import repair as repair_module
    from apps.ops.repair import ReconciliationRepairService, RepairResult

    def fake_log_admin_action(**kwargs):
        return SimpleNamespace(
            id=uuid4(),
            event_type=kwargs['action'],
            entity_type=kwargs['target_type'],
            entity_id=kwargs['target_id'],
            created_at=timezone.now(),
        )

    def fake_retry(self, *, entity_type: str, entity_id: str, reason: str):
        return RepairResult(
            action='retry_outbox',
            status='accepted',
            entity_type=entity_type,
            entity_id=entity_id,
            message='Outbox message was returned to pending state.',
            changed=True,
            result={'outbox_status': 'pending', 'reason': reason},
        )

    def fake_capture(*, repair_payload, request=None, limit=100):
        return {
            'status': 'captured',
            'source': 'repair',
            'snapshot_id': 'snapshot-1',
            'href': '/admin/entities/reconciliation_snapshot/snapshot-1',
            'previous_problem_count': 4,
            'current_problem_count': 2,
            'problem_delta': -2,
            'improved': True,
        }

    monkeypatch.setattr(repair_module.AuditService, 'log_admin_action', staticmethod(fake_log_admin_action))
    monkeypatch.setattr(ReconciliationRepairService, '_retry_outbox', fake_retry)
    monkeypatch.setattr('apps.ops.reconciliation_snapshots.capture_repair_reconciliation_snapshot', fake_capture)

    payload = ReconciliationRepairService().execute(
        action='retry_outbox',
        entity_type='outbox_message',
        entity_id='msg-1',
        reason='test repair',
        request=None,
    )

    assert payload['status'] == 'accepted'
    assert payload['repair_snapshot']['source'] == 'repair'
    assert payload['reconciliation_snapshot_id'] == 'snapshot-1'
    assert payload['previous_problem_count'] == 4
    assert payload['current_problem_count'] == 2
    assert payload['problem_delta'] == -2
    assert payload['improved'] is True
''')


def write_docs() -> None:
    path = DOCS / "reconciliation_repair_snapshots_v8_30.md"
    if path.exists():
        return
    write(path, '''# v8.30 — reconciliation snapshot auto-capture after repair actions

## Цель

После любого успешного `admin/reconciliation-repair/` backend автоматически делает persisted snapshot `source=repair` и возвращает в ответе repair action краткую динамику проблем.

## Что меняется

- `ReconciliationRepairService.execute()` после audit log вызывает `capture_repair_reconciliation_snapshot()`.
- Snapshot создаётся с `source='repair'` и `correlation_id='repair:<audit_event_id>'`.
- Ответ repair endpoint теперь содержит:
  - `repair_snapshot`;
  - `reconciliation_snapshot_id`;
  - `reconciliation_snapshot_href`;
  - `previous_problem_count`;
  - `current_problem_count`;
  - `problem_delta`;
  - `improved`.
- Добавлен read endpoint latest snapshot:
  - `GET /api/v1/ops/admin/reconciliation-snapshots/latest/`
  - `GET /api/v1/ops/admin/reconciliation-snapshots/latest/?source=repair`

## Проверка

```bash
cd backend
python manage.py check
python manage.py makemigrations --check --dry-run
pytest -q tests/test_ops_reconciliation_repair_snapshot_autocapture.py
pytest -q
```
''')


def main() -> None:
    ensure_backend()
    ensure_reconciliation_snapshot_helpers()
    insert_repair_autocapture()
    patch_repair_serializer()
    patch_snapshot_serializer()
    patch_views()
    patch_urls()
    write_tests()
    write_docs()
    print("v8.30 applied: reconciliation repair actions now auto-capture source=repair snapshots.")


if __name__ == "__main__":
    main()
