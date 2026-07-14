from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management import get_commands
from django.urls import NoReverseMatch, reverse
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated

from apps.access_control.permissions import (
    IsAdminOrSupport,
    IsAdminSupportFinanceReadonly,
    IsAuditReader,
    IsFinanceOps,
    IsNotificationOperator,
)


_STATUS_RANK = {'ok': 0, 'warning': 1, 'degraded': 2, 'critical': 3}
LEGACY_CONTRACT_VERSIONS = {'public_marketplace': 'v118'}


@dataclass(frozen=True)
class UrlContract:
    key: str
    name: str
    expected_path: str
    args: tuple[str, ...] = ()


@dataclass(frozen=True)
class SymbolContract:
    key: str
    module: str
    attr: str
    description: str


@dataclass(frozen=True)
class PermissionContract:
    key: str
    module: str
    view_class: str
    expected_permissions: tuple[type, ...]
    description: str


@dataclass(frozen=True)
class FileContract:
    key: str
    path: str
    description: str


@dataclass(frozen=True)
class ExecutableFileContract:
    key: str
    path: str
    description: str


URL_CONTRACTS = [
    UrlContract('payment_admin', 'payments-admin-list', '/api/v1/payments-admin/'),
    UrlContract('payment_webhooks_admin', 'payments-webhooks-list', '/api/v1/payments-webhooks/'),
    UrlContract('customer_billing_orders', 'orders-list', '/api/v1/orders/'),
    UrlContract('customer_billing_payments', 'payments-list', '/api/v1/payments/'),
    UrlContract('customer_billing_entitlements', 'entitlements-list', '/api/v1/entitlements/'),
    UrlContract('subscriptions', 'subscriptions-list', '/api/v1/subscriptions/'),
    UrlContract('trainer_crm', 'trainer-crm-list', '/api/v1/customer/trainer-crm/'),
    UrlContract('trainer_schedule', 'booking-me-schedule', '/api/v1/booking/me/schedule/'),
    UrlContract('booking_check_in', 'booking-attendance-check-in', '/api/v1/booking/attendance/check-in/'),
    UrlContract('booking_attendance_history', 'booking-attendance-history', '/api/v1/booking/attendance/'),
    UrlContract('notifications_admin_center', 'admin-notification-center', '/api/v1/notifications/admin/center/'),
    UrlContract('ops_production_readiness', 'ops-admin-production-readiness', '/api/v1/ops/admin/production-readiness/'),
    UrlContract('ops_global_search', 'ops-admin-global-search', '/api/v1/ops/admin/global-search/'),
    UrlContract('ops_support_console', 'ops-admin-support-console', '/api/v1/ops/admin/support-console/'),
    UrlContract('ops_support_notification_resend', 'ops-admin-support-notification-resend', '/api/v1/ops/admin/support-console/notifications/resend/'),
    UrlContract('ops_support_entitlement_fix', 'ops-admin-support-entitlement-fix', '/api/v1/ops/admin/support-console/entitlements/fix/'),
    UrlContract('disputes_chargeback_open', 'admin-chargeback-open', '/api/v1/disputes/admin/chargebacks/open/'),
    UrlContract('disputes_chargeback_evidence', 'admin-chargeback-evidence', '/api/v1/disputes/admin/chargebacks/00000000-0000-0000-0000-000000000000/evidence/', ('00000000-0000-0000-0000-000000000000',)),
    UrlContract('disputes_chargeback_resolve', 'admin-chargeback-resolve', '/api/v1/disputes/admin/chargebacks/00000000-0000-0000-0000-000000000000/resolve/', ('00000000-0000-0000-0000-000000000000',)),
    UrlContract('finance_documents_admin_list', 'finance-documents-admin-list', '/api/v1/finance-documents/admin/documents/'),
    UrlContract('finance_documents_admin_build', 'finance-documents-admin-build', '/api/v1/finance-documents/admin/documents/build/'),
    UrlContract('finance_documents_accountant_export', 'finance-documents-admin-accountant-export', '/api/v1/finance-documents/admin/documents/accountant-export/'),
    UrlContract('legal_documents', 'legal-me-documents', '/api/v1/legal/me/documents/'),
    UrlContract('legal_compliance_status', 'legal-me-compliance-status', '/api/v1/legal/me/compliance-status/'),
    UrlContract('legal_consent_logs', 'legal-me-consent-logs', '/api/v1/legal/me/consent-logs/'),
    UrlContract('observability_runtime', 'observability-runtime', '/api/v1/observability/runtime/'),
    UrlContract('ops_observability_runtime', 'ops-admin-observability-runtime', '/api/v1/ops/admin/observability-runtime/'),
    UrlContract('ops_launch_candidate', 'ops-admin-launch-candidate', '/api/v1/ops/admin/launch-candidate/'),
    UrlContract('ops_production_launch_pack', 'ops-admin-production-launch-pack', '/api/v1/ops/admin/production-launch-pack/'),
    UrlContract('ops_runbooks', 'ops-admin-runbooks', '/api/v1/ops/admin/runbooks/'),
    UrlContract('ops_runbook_detail', 'ops-admin-runbook-detail', '/api/v1/ops/admin/runbooks/failed_payment_webhook/', ('failed_payment_webhook',)),
    UrlContract('content_learning_area', 'content-student-learning-area', '/api/v1/content/student/learning-area/'),
    UrlContract('content_program_runtime', 'content-runtime-program-lesson', '/api/v1/content/runtime/programs/example-program/lessons/example-lesson/', ('example-program', 'example-lesson')),
    UrlContract('content_course_runtime', 'content-runtime-course-lesson', '/api/v1/content/runtime/courses/00000000-0000-0000-0000-000000000000/lessons/00000000-0000-0000-0000-000000000000/', ('00000000-0000-0000-0000-000000000000', '00000000-0000-0000-0000-000000000000')),
    UrlContract('progress_lessons', 'progress-lessons-list', '/api/v1/progress/lessons/'),
    UrlContract('progress_summary', 'progress-summary-list', '/api/v1/progress/summary/'),
    UrlContract('assignments_student', 'assignments-student-list', '/api/v1/assignments/student/'),
    UrlContract('assignments_trainer', 'assignments-trainer-list', '/api/v1/assignments/trainer/'),
    UrlContract('reviews_trainer_quality', 'reviews-trainer-quality', '/api/v1/reviews/trainer/quality/'),
    UrlContract('messaging_inbox', 'messaging-inbox', '/api/v1/messaging/me/inbox/'),
    UrlContract('messaging_start', 'messaging-start-conversation', '/api/v1/messaging/conversations/start/'),
    UrlContract('public_marketplace_home', 'public-marketplace-home', '/api/v1/public-catalog/'),
    UrlContract('public_marketplace_content_landing', 'public-marketplace-content-landing', '/api/v1/public-catalog/landing/program/example-program/', ('program', 'example-program')),
    UrlContract('public_marketplace_trainer_landing', 'public-marketplace-trainer-landing', '/api/v1/public-catalog/trainers/example-trainer/landing/', ('example-trainer',)),
]


SYMBOL_CONTRACTS = [
    SymbolContract('payment_webhook_service', 'apps.payments.services', 'PaymentWebhookService', 'Webhook hardening, replay and duplicate protection.'),
    SymbolContract('payment_reconciliation', 'apps.ops.payment_reconciliation', 'get_payment_reconciliation_report', 'Payment/provider/entitlement reconciliation report.'),
    SymbolContract('entitlement_access_audit', 'apps.entitlements.access_audit', 'AccessControlAuditService', 'Runtime access guard policy.'),
    SymbolContract('subscription_lifecycle', 'apps.subscriptions.lifecycle', 'SubscriptionLifecycleService', 'Subscription lifecycle and renewal helpers.'),
    SymbolContract('domain_notifications', 'apps.notifications.domain.triggers', 'DomainNotificationTriggers', 'Commerce notification triggers.'),
    SymbolContract('trainer_crm_selector', 'apps.customers.selectors', 'TrainerCRMSelector', 'Trainer CRM read model.'),
    SymbolContract('booking_attendance_service', 'apps.booking.services.attendance', 'BookingAttendanceService', 'Attendance and check-in service.'),
    SymbolContract('course_program_builder', 'apps.trainer_cms.services', 'TrainerCMSService', 'Course/program builder and publishing snapshots.'),
    SymbolContract('content_access_runtime', 'apps.content.runtime', 'ContentAccessRuntime', 'Entitlement-gated lesson runtime.'),
    SymbolContract('student_learning_area', 'apps.content.student_learning', 'StudentLearningAreaSelector', 'Student learning area read model.'),
    SymbolContract('progress_service', 'apps.progress.services', 'ProgressService', 'Lesson completion and progress tracking.'),
    SymbolContract('assignment_service', 'apps.assignments.services', 'AssignmentService', 'Homework submission and trainer review.'),
    SymbolContract('review_feedback_loop', 'apps.reviews.services', 'ReviewService', 'Review moderation, aggregation and trainer replies.'),
    SymbolContract('messaging_conversations', 'apps.messaging.services.conversations', 'ConversationService', 'Trainer-student messaging core.'),
    SymbolContract('admin_global_search', 'apps.ops.admin_global_search', 'get_admin_global_search', 'Tenant-aware admin global search.'),
    SymbolContract('support_console', 'apps.ops.support_console', 'get_support_console_snapshot', 'Support console customer/payment/access snapshot.'),
    SymbolContract('chargeback_dispute_service', 'apps.disputes.services.case_service', 'ChargebackDisputeService', 'Chargeback lifecycle, evidence submission, entitlement hold and audit trail.'),
    SymbolContract('finance_commercial_documents', 'apps.finance_documents.services.commercial_documents', 'FinanceCommercialDocumentService', 'Invoice, receipt, credit note, refund document and accountant export service.'),
    SymbolContract('legal_acceptance_service', 'apps.legal_compliance.services.acceptance', 'LegalAcceptanceService', 'Terms, privacy, refund policy acceptance and consent log service.'),
    SymbolContract('observability_runtime', 'apps.observability.runtime', 'get_observability_runtime_snapshot', 'Production observability runtime health snapshot.'),
    SymbolContract('ops_runbooks', 'apps.ops.runbooks', 'get_ops_runbook_index', 'Production incident runbook index.'),
    SymbolContract('demo_seed_payload', 'scripts.bootstrap.seed_demo', 'build_demo_seed_payload', 'Launch demo data scenarios for trainer, student, payments, refunds, payouts and subscriptions.'),
    SymbolContract('public_marketplace_home', 'apps.public_catalog.services', 'build_marketplace_home', 'SEO marketplace home payload with featured catalog, trust copy and checkout CTAs.'),
    SymbolContract('public_content_landing', 'apps.public_catalog.services', 'build_content_landing', 'SEO content landing payload with pricing, reviews and entitlement-aware checkout messaging.'),
    SymbolContract('public_trainer_landing', 'apps.public_catalog.services', 'build_trainer_landing', 'SEO trainer landing payload with products, reviews, pricing and checkout CTAs.'),
    SymbolContract('launch_candidate_pack', 'apps.ops.launch_candidate', 'get_launch_candidate_pack', 'Launch candidate package with version, smoke checklist, known limitations, release notes and production env checklist.'),
    SymbolContract('production_launch_pack', 'apps.ops.production_launch_pack', 'get_production_launch_pack', 'Production launch documentation pack for deploy, backup, monitoring, admin, trainer and student handoffs.'),
]


PERMISSION_CONTRACTS = [
    PermissionContract('payment_admin_permissions', 'apps.payments.api.views', 'AdminPaymentViewSet', (IsAdminSupportFinanceReadonly,), 'Payment admin UI uses the v107 admin/support/finance/readonly matrix.'),
    PermissionContract('payment_webhook_permissions', 'apps.payments.api.views', 'PaymentWebhookViewSet', (), 'Payment webhook receive is public with signature checks; admin actions use get_permissions.'),
    PermissionContract('payout_admin_permissions', 'apps.payouts.api.views', 'AdminPayoutViewSet', (IsFinanceOps,), 'Payout admin API uses finance operations matrix.'),
    PermissionContract('audit_admin_permissions', 'apps.audit.api.views', 'AuditAdminViewSet', (IsAuditReader,), 'Audit APIs allow read-only audit roles and admin writes.'),
    PermissionContract('subscription_permissions', 'apps.subscriptions.api.views', 'SubscriptionViewSet', (IsAuthenticated,), 'Subscription self-service requires auth.'),
    PermissionContract('trainer_crm_permissions', 'apps.customers.api.views', 'TrainerCRMViewSet', (IsAuthenticated,), 'Trainer CRM requires auth plus role guard.'),
    PermissionContract('booking_schedule_permissions', 'apps.booking.api.views', 'TrainerScheduleView', (IsAuthenticated,), 'Trainer schedule requires auth.'),
    PermissionContract('booking_checkin_permissions', 'apps.booking.api.views', 'AttendanceCheckInView', (IsAuthenticated,), 'Attendance check-in requires auth.'),
    PermissionContract('ops_readiness_permissions', 'apps.ops.api.views', 'AdminProductionReadinessView', (IsAdminSupportFinanceReadonly,), 'Production readiness uses method-aware ops roles.'),
    PermissionContract('ops_launch_candidate_permissions', 'apps.ops.api.views', 'AdminLaunchCandidateView', (IsAdminSupportFinanceReadonly,), 'Launch candidate API uses ops role matrix.'),
    PermissionContract('ops_production_launch_pack_permissions', 'apps.ops.api.views', 'AdminProductionLaunchPackView', (IsAdminSupportFinanceReadonly,), 'Production launch pack API uses ops role matrix.'),
    PermissionContract('ops_global_search_permissions', 'apps.ops.api.views', 'AdminGlobalSearchView', (IsAdminSupportFinanceReadonly,), 'Admin global search uses method-aware ops roles.'),
    PermissionContract('ops_support_console_permissions', 'apps.ops.api.views', 'SupportConsoleView', (IsAdminOrSupport,), 'Support console is limited to admin/support roles.'),
    PermissionContract('chargeback_open_permissions', 'apps.disputes.api.views', 'AdminChargebackOpenView', (IsFinanceOps,), 'Chargeback write operations use finance/admin API permissions.'),
    PermissionContract('finance_documents_permissions', 'apps.finance_documents.api.views', 'AdminFinanceDocumentsView', (IsAuthenticated, IsFinanceOps), 'Finance document admin APIs use finance/admin API permissions.'),
    PermissionContract('observability_runtime_permissions', 'apps.observability.api.views', 'ObservabilityRuntimeView', (IsAdminSupportFinanceReadonly,), 'Observability runtime API uses ops role matrix.'),
    PermissionContract('ops_runbook_permissions', 'apps.ops.api.views', 'AdminOpsRunbookIndexView', (IsAdminSupportFinanceReadonly,), 'Ops runbook API uses ops role matrix.'),
    PermissionContract('notification_admin_permissions', 'apps.notifications.api.views', 'AdminNotificationCenterView', (IsAuthenticated, IsNotificationOperator), 'Notification admin API uses operator role matrix.'),
    PermissionContract('student_learning_permissions', 'apps.content.api.views', 'StudentLearningAreaApi', (IsAuthenticated,), 'Student learning area requires auth.'),
    PermissionContract('student_assignments_permissions', 'apps.assignments.api.views', 'StudentAssignmentViewSet', (IsAuthenticated,), 'Student homework requires auth.'),
    PermissionContract('trainer_assignments_permissions', 'apps.assignments.api.views', 'TrainerAssignmentViewSet', (IsAuthenticated,), 'Trainer homework dashboard requires auth.'),
    PermissionContract('trainer_review_reply_permissions', 'apps.reviews.api.views', 'TrainerReviewReplyView', (IsAuthenticated,), 'Trainer review replies require auth and owner guard.'),
    PermissionContract('messaging_inbox_permissions', 'apps.messaging.api.views', 'MyInboxView', (IsAuthenticated,), 'Messaging inbox requires auth.'),
    PermissionContract('messaging_start_permissions', 'apps.messaging.api.views', 'StartConversationView', (IsAuthenticated,), 'Starting conversations requires auth.'),
    PermissionContract('messaging_system_permissions', 'apps.messaging.api.views', 'CreateSystemMessageView', (IsAdminOrSupport,), 'System messages are limited to admin/support roles.'),
]


FILE_CONTRACTS = [
    FileContract('ci_workflow', '.github/workflows/ci.yml', 'CI workflow exists.'),
    FileContract('readme_current_version', 'README.md', 'Current-version README exists.'),
    FileContract('seed_demo', 'scripts/bootstrap/seed_demo.py', 'Seed data helper exists.'),
    FileContract('booking_v93_test', 'backend/tests/test_booking_v93_schedule_waitlist.py', 'Booking schedule regression test exists.'),
    FileContract('booking_v94_test', 'backend/tests/test_booking_v94_attendance_checkin.py', 'Attendance check-in regression test exists.'),
    FileContract('customer_crm_v92_test', 'backend/tests/test_customer_crm_v92.py', 'CRM regression test exists.'),
    FileContract('notifications_v91_test', 'backend/tests/test_notifications_v91_domain_triggers.py', 'Notification regression test exists.'),
    FileContract('course_builder_v97_test', 'backend/tests/test_course_program_builder_v97.py', 'Course/program builder regression test exists.'),
    FileContract('content_runtime_v98_test', 'backend/tests/test_content_access_runtime_v98.py', 'Content runtime regression test exists.'),
    FileContract('video_delivery_v99_test', 'backend/tests/test_video_delivery_hardening_v99.py', 'Video delivery regression test exists.'),
    FileContract('student_learning_v100_test', 'backend/tests/test_student_learning_area_v100.py', 'Student learning regression test exists.'),
    FileContract('progress_v101_test', 'backend/tests/test_progress_tracking_v101.py', 'Progress tracking regression test exists.'),
    FileContract('assignments_v102_test', 'backend/tests/test_assignments_homework_v102.py', 'Assignments/homework regression test exists.'),
    FileContract('reviews_v103_test', 'backend/tests/test_reviews_feedback_loop_v103.py', 'Reviews/feedback regression test exists.'),
    FileContract('messaging_v104_test', 'backend/tests/test_messaging_core_v104.py', 'Messaging core regression test exists.'),
    FileContract('role_matrix_v107_test', 'backend/tests/test_role_matrix_permissions_v107.py', 'Role matrix permission regression test exists.'),
    FileContract('tenant_isolation_v108_test', 'backend/tests/test_tenant_isolation_v108.py', 'Tenant isolation regression test exists.'),
    FileContract('admin_global_search_v109_test', 'backend/tests/test_admin_global_search_v109.py', 'Admin global search regression test exists.'),
    FileContract('support_console_v110_test', 'backend/tests/test_support_console_v110.py', 'Support console regression test exists.'),
    FileContract('disputes_chargebacks_v111_test', 'backend/tests/test_disputes_chargebacks_v111.py', 'Disputes/chargebacks regression test exists.'),
    FileContract('finance_documents_v112_test', 'backend/tests/test_finance_documents_v112.py', 'Finance documents regression test exists.'),
    FileContract('legal_compliance_v113_test', 'backend/tests/test_legal_compliance_v113.py', 'Legal compliance regression test exists.'),
    FileContract('observability_runtime_v114_test', 'backend/tests/test_observability_runtime_v114.py', 'Observability runtime regression test exists.'),
    FileContract('ops_runbooks_v115_test', 'backend/tests/test_ops_runbooks_v115.py', 'Ops runbooks regression test exists.'),
    FileContract('runbook_failed_payment_webhook', 'ops/runbooks/failed-payment-webhook.md', 'Failed payment webhook runbook exists.'),
    FileContract('runbook_wrong_entitlement', 'ops/runbooks/wrong-entitlement.md', 'Wrong entitlement runbook exists.'),
    FileContract('runbook_payout_mismatch', 'ops/runbooks/payout-mismatch.md', 'Payout mismatch runbook exists.'),
    FileContract('runbook_refund_conflict', 'ops/runbooks/refund-conflict.md', 'Refund conflict runbook exists.'),
    FileContract('runbook_database_restore', 'ops/runbooks/database-restore.md', 'Database restore runbook exists.'),
    FileContract('runbook_deployment_rollback', 'ops/runbooks/deployment-rollback.md', 'Deployment rollback runbook exists.'),
    FileContract('launch_gate_script', 'scripts/ci/launch_gate.sh', 'Launch hardening CI gate exists.'),
    FileContract('production_gate_script', 'scripts/ci/production_gate.sh', 'CI/CD production gate exists.'),
    FileContract('ci_cd_production_gate_v116_test', 'backend/tests/test_ci_cd_production_gate_v116.py', 'CI/CD production gate regression test exists.'),
    FileContract('demo_seed_scenarios_v117_test', 'backend/tests/test_demo_seed_scenarios_v117.py', 'Demo seed scenarios regression test exists.'),
    FileContract('public_marketplace_v118_test', 'backend/tests/test_public_marketplace_hardening_v118.py', 'Public marketplace hardening regression test exists.'),
    FileContract('version_file', 'VERSION', 'Project version file exists.'),
    FileContract('launch_candidate_doc', 'docs/launch/launch_candidate_v119.md', 'Launch candidate release note exists.'),
    FileContract('launch_candidate_v119_test', 'backend/tests/test_launch_candidate_v119.py', 'Launch candidate regression test exists.'),
    FileContract('production_launch_pack_index', 'docs/launch/production/README.md', 'Production launch pack index exists.'),
    FileContract('production_launch_deploy_doc', 'docs/launch/production/deploy.md', 'Production deploy docs exist.'),
    FileContract('production_launch_backup_doc', 'docs/launch/production/backup.md', 'Production backup docs exist.'),
    FileContract('production_launch_monitoring_doc', 'docs/launch/production/monitoring.md', 'Production monitoring docs exist.'),
    FileContract('production_launch_admin_doc', 'docs/launch/production/admin.md', 'Production admin docs exist.'),
    FileContract('production_launch_trainer_doc', 'docs/launch/production/trainer.md', 'Production trainer docs exist.'),
    FileContract('production_launch_student_doc', 'docs/launch/production/student.md', 'Production student docs exist.'),
    FileContract('production_launch_pack_v120_test', 'backend/tests/test_production_launch_pack_v120.py', 'Production launch pack regression test exists.'),
]

EXECUTABLE_FILE_CONTRACTS = [
    ExecutableFileContract('backend_quality_executable', 'scripts/ci/backend_quality.sh', 'Backend quality script is directly executable.'),
    ExecutableFileContract('frontend_build_executable', 'scripts/ci/frontend_build.sh', 'Frontend build script is directly executable.'),
    ExecutableFileContract('launch_gate_executable', 'scripts/ci/launch_gate.sh', 'Launch gate script is directly executable.'),
    ExecutableFileContract('production_gate_executable', 'scripts/ci/production_gate.sh', 'Production gate script is directly executable.'),
    ExecutableFileContract('backend_contracts_executable', 'scripts/test/run_backend_contracts.sh', 'Backend contracts runner is directly executable.'),
    ExecutableFileContract('integration_stack_executable', 'scripts/test/run_integration_stack.sh', 'Integration stack runner is directly executable.'),
    ExecutableFileContract('backend_check_executable', 'scripts/quality/backend_check.sh', 'Backend quality check script is directly executable.'),
    ExecutableFileContract('frontend_check_executable', 'scripts/quality/frontend_check.sh', 'Frontend quality check script is directly executable.'),
    ExecutableFileContract('full_check_executable', 'scripts/quality/full_check.sh', 'Full quality check script is directly executable.'),
]


SMOKE_COMMANDS = [
    {'key': 'django_check', 'title': 'Django system checks', 'command': 'cd backend && python manage.py check'},
    {'key': 'migration_check', 'title': 'Migration drift check', 'command': 'cd backend && python manage.py makemigrations --check --dry-run'},
    {'key': 'backend_contracts', 'title': 'Backend roadmap tests', 'command': 'cd backend && pytest tests/test_customer_crm_v92.py tests/test_booking_v93_schedule_waitlist.py tests/test_booking_v94_attendance_checkin.py tests/test_notifications_v91_domain_triggers.py tests/test_course_program_builder_v97.py tests/test_content_access_runtime_v98.py tests/test_video_delivery_hardening_v99.py tests/test_student_learning_area_v100.py tests/test_progress_tracking_v101.py tests/test_assignments_homework_v102.py tests/test_reviews_feedback_loop_v103.py tests/test_messaging_core_v104.py tests/test_role_matrix_permissions_v107.py tests/test_tenant_isolation_v108.py tests/test_admin_global_search_v109.py tests/test_support_console_v110.py tests/test_disputes_chargebacks_v111.py tests/test_finance_documents_v112.py tests/test_legal_compliance_v113.py tests/test_observability_runtime_v114.py tests/test_ops_runbooks_v115.py tests/test_ci_cd_production_gate_v116.py tests/test_demo_seed_scenarios_v117.py tests/test_public_marketplace_hardening_v118.py tests/test_launch_candidate_v119.py tests/test_production_launch_pack_v120.py'},
    {'key': 'readiness_gate', 'title': 'Production readiness gate', 'command': 'cd backend && python manage.py check_production_readiness --json --fail-on-degraded'},
    {'key': 'launch_gate', 'title': 'Launch hardening gate', 'command': 'bash scripts/ci/launch_gate.sh'},
    {'key': 'production_gate', 'title': 'CI/CD production gate', 'command': 'bash scripts/ci/production_gate.sh'},
    {'key': 'frontend_typecheck', 'title': 'Frontend typecheck', 'command': 'cd frontend && npm run typecheck'},
    {'key': 'frontend_build', 'title': 'Frontend build', 'command': 'cd frontend && npm run build'},
]


FRONTEND_SURFACE = [
    {'key': 'payment_admin', 'href': '/admin/payments', 'description': 'Payment admin UI.'},
    {'key': 'customer_billing', 'href': '/billing', 'description': 'Customer billing UI.'},
    {'key': 'trainer_sales', 'href': '/trainer/dashboard/sales', 'description': 'Trainer sales dashboard.'},
    {'key': 'trainer_crm', 'href': '/trainer/dashboard/crm', 'description': 'Trainer CRM dashboard.'},
    {'key': 'trainer_schedule', 'href': '/trainer/dashboard/schedule', 'description': 'Trainer booking/attendance dashboard.'},
    {'key': 'learning_area', 'href': '/learning', 'description': 'Student learning area.'},
    {'key': 'assignments', 'href': '/assignments', 'description': 'Student homework area.'},
    {'key': 'trainer_assignments', 'href': '/trainer/dashboard/assignments', 'description': 'Trainer homework dashboard.'},
    {'key': 'messages', 'href': '/messages', 'description': 'Trainer-student messaging inbox.'},
    {'key': 'trainer_reviews', 'href': '/trainer/reviews', 'description': 'Trainer reviews and feedback dashboard.'},
]


ROLE_MATRIX = [
    {'role': 'anonymous', 'allowed': ['/catalog', '/trainers', 'preview lessons'], 'blocked': ['/learning', '/assignments', '/messages', '/billing']},
    {'role': 'customer', 'allowed': ['/learning', '/assignments', '/messages', '/billing', '/subscriptions'], 'blocked': ['/trainer/dashboard/*', '/admin/*']},
    {'role': 'trainer', 'allowed': ['/trainer/dashboard/*', '/trainer/reviews', '/messages', '/payouts'], 'blocked': ['/admin/*']},
    {'role': 'support', 'allowed': ['/admin/payments', '/admin/audit', '/admin/ops read-only', 'notification resend'], 'blocked': ['payment writes', 'payout writes', 'audit cleanup']},
    {'role': 'finance', 'allowed': ['/admin/payments read-only', '/admin/payouts', 'finance exports'], 'blocked': ['audit cleanup', 'notification writes']},
    {'role': 'readonly_auditor', 'allowed': ['/admin/audit read-only', '/admin/payments read-only', '/admin/payouts read-only', '/admin/ops read-only'], 'blocked': ['all writes']},
    {'role': 'admin', 'allowed': ['/admin/*', '/api/v1/ops/admin/production-readiness/'], 'blocked': []},
]


CI_GATE = {
    'workflow': '.github/workflows/ci.yml',
    'required_jobs': ['backend-quality', 'frontend-build', 'launch-hardening', 'production-gate'],
    'launch_script': 'scripts/ci/launch_gate.sh',
    'production_script': 'scripts/ci/production_gate.sh',
}


def _rank(status: str) -> int:
    return _STATUS_RANK.get(status, 2)


def _worst_status(statuses: list[str]) -> str:
    if not statuses:
        return 'ok'
    return sorted(statuses, key=_rank, reverse=True)[0]


def _check(key: str, category: str, title: str, status: str = 'ok', **extra: Any) -> dict[str, Any]:
    return {'key': key, 'category': category, 'title': title, 'status': status, **extra}


def _check_url(contract: UrlContract) -> dict[str, Any]:
    try:
        actual = reverse(contract.name, args=contract.args)
    except NoReverseMatch as exc:
        return _check(contract.key, 'api_contract', contract.name, 'critical', detail=f'URL name is not resolvable: {exc}', expected_path=contract.expected_path)
    if actual != contract.expected_path:
        return _check(contract.key, 'api_contract', contract.name, 'degraded', detail=f'URL resolved to {actual}, expected {contract.expected_path}.', expected_path=contract.expected_path, actual_path=actual)
    return _check(contract.key, 'api_contract', contract.name, expected_path=contract.expected_path, actual_path=actual)


def _check_symbol(contract: SymbolContract) -> dict[str, Any]:
    try:
        module = import_module(contract.module)
    except Exception as exc:
        return _check(contract.key, 'python_contract', f'{contract.module}.{contract.attr}', 'critical', detail=f'Module import failed: {exc}', description=contract.description)
    if not hasattr(module, contract.attr):
        return _check(contract.key, 'python_contract', f'{contract.module}.{contract.attr}', 'critical', detail='Expected symbol is missing.', description=contract.description)
    return _check(contract.key, 'python_contract', f'{contract.module}.{contract.attr}', description=contract.description)


def _check_permissions(contract: PermissionContract) -> dict[str, Any]:
    try:
        view_class = getattr(import_module(contract.module), contract.view_class)
    except Exception as exc:
        return _check(contract.key, 'permissions', contract.view_class, 'critical', detail=f'View import failed: {exc}', description=contract.description)
    configured = tuple(getattr(view_class, 'permission_classes', ()) or ())
    missing = [permission.__name__ for permission in contract.expected_permissions if permission not in configured]
    if missing:
        return _check(
            contract.key,
            'permissions',
            contract.view_class,
            'critical',
            detail=f'Missing permission classes: {", ".join(missing)}',
            configured=[permission.__name__ for permission in configured],
            expected=[permission.__name__ for permission in contract.expected_permissions],
            description=contract.description,
        )
    return _check(
        contract.key,
        'permissions',
        contract.view_class,
        configured=[permission.__name__ for permission in configured],
        expected=[permission.__name__ for permission in contract.expected_permissions],
        description=contract.description,
    )


def _check_file(contract: FileContract, *, repo_root: Path) -> dict[str, Any]:
    path = repo_root / contract.path
    if not path.exists():
        return _check(contract.key, 'files', contract.path, 'critical', detail='Required file is missing.', description=contract.description)
    return _check(contract.key, 'files', contract.path, description=contract.description)


def _check_executable_file(contract: ExecutableFileContract, *, repo_root: Path) -> dict[str, Any]:
    path = repo_root / contract.path
    if not path.exists():
        return _check(contract.key, 'executable_files', contract.path, 'critical', detail='Required executable file is missing.', description=contract.description)
    if not path.is_file():
        return _check(contract.key, 'executable_files', contract.path, 'critical', detail='Path is not a file.', description=contract.description)
    if not path.stat().st_mode & 0o111:
        return _check(contract.key, 'executable_files', contract.path, 'degraded', detail='File exists but is not executable.', description=contract.description)
    return _check(contract.key, 'executable_files', contract.path, description=contract.description)


def _check_management_command() -> dict[str, Any]:
    commands = get_commands()
    if 'check_production_readiness' not in commands:
        return _check('check_production_readiness', 'management_commands', 'check_production_readiness', 'critical', detail='Management command is not registered.')
    return _check('check_production_readiness', 'management_commands', 'check_production_readiness', app=commands['check_production_readiness'])


def _check_payment_safety() -> dict[str, Any]:
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'payment_production_guards',
            'payment_safety',
            'Mock payment and unverified return guards',
            detail='Production payment safety guards are evaluated when IS_PRODUCTION=True.',
        )

    unsafe_flags = []
    if bool(getattr(settings, 'PAYMENTS_ALLOW_MOCK_PROVIDER', False)):
        unsafe_flags.append('PAYMENTS_ALLOW_MOCK_PROVIDER')
    if bool(getattr(settings, 'PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN', False)):
        unsafe_flags.append('PAYMENTS_ALLOW_UNVERIFIED_PROVIDER_RETURN')
    if unsafe_flags:
        return _check(
            'payment_production_guards',
            'payment_safety',
            'Mock payment and unverified return guards',
            'critical',
            detail='Disable unsafe payment flags before accepting production traffic.',
            unsafe_flags=unsafe_flags,
        )
    return _check(
        'payment_production_guards',
        'payment_safety',
        'Mock payment and unverified return guards',
        detail='Mock checkout and unverified provider-return mutations are disabled.',
    )


def _check_email_safety() -> dict[str, Any]:
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'email_production_config',
            'email_safety',
            'Transactional email configuration',
            detail='Production email configuration is evaluated when IS_PRODUCTION=True.',
        )

    backend = str(getattr(settings, 'EMAIL_BACKEND', '') or '')
    from_email = str(getattr(settings, 'DEFAULT_FROM_EMAIL', '') or '')
    host = str(getattr(settings, 'EMAIL_HOST', '') or '')
    unsafe = []
    if any(marker in backend for marker in ('console', 'locmem', 'dummy')):
        unsafe.append('EMAIL_BACKEND')
    if not from_email or 'localhost' in from_email or '@example.' in from_email:
        unsafe.append('DEFAULT_FROM_EMAIL')
    if 'smtp' in backend and (not host or host == 'localhost'):
        unsafe.append('EMAIL_HOST')
    if unsafe:
        return _check(
            'email_production_config',
            'email_safety',
            'Transactional email configuration',
            'critical',
            detail='Configure a real transactional email backend before accepting production traffic.',
            unsafe_flags=unsafe,
        )
    return _check(
        'email_production_config',
        'email_safety',
        'Transactional email configuration',
        detail='Transactional email backend and sender are production-ready.',
    )


def _check_payout_legal_eligibility_gate() -> dict[str, Any]:
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'payout_legal_eligibility_gate',
            'payout_safety',
            'Payout legal eligibility gate',
            detail='Payout legal eligibility enforcement is evaluated when IS_PRODUCTION=True.',
        )

    if not bool(getattr(settings, 'PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY', False)):
        return _check(
            'payout_legal_eligibility_gate',
            'payout_safety',
            'Payout legal eligibility gate',
            'critical',
            detail='Enable PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY before allowing production payouts.',
            unsafe_flags=['PAYOUTS_REQUIRE_LEGAL_ELIGIBILITY'],
        )

    return _check(
        'payout_legal_eligibility_gate',
        'payout_safety',
        'Payout legal eligibility gate',
        detail='Payout requests require approved KYC, payout profile data and an active trainer agreement.',
    )


def _rate_per_minute(rate: str) -> float | None:
    try:
        count_text, period_text = str(rate or '').split('/', 1)
        count = float(count_text)
    except (TypeError, ValueError):
        return None
    period = period_text.strip().lower()
    if period.startswith('s'):
        return count * 60
    if period.startswith('m'):
        return count
    if period.startswith('h'):
        return count / 60
    if period.startswith('d'):
        return count / 1440
    return None


def _check_auth_scoped_throttle(*, key: str, rate_key: str, title: str, max_production_per_minute: float, traffic_label: str) -> dict[str, Any]:
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    rate = str(rates.get(rate_key) or '')
    per_minute = _rate_per_minute(rate)
    if per_minute is None:
        return _check(
            key,
            'auth_safety',
            title,
            'critical',
            detail=f'Configure REST_FRAMEWORK.DEFAULT_THROTTLE_RATES["{rate_key}"] before accepting {traffic_label}.',
            configured_rate=rate,
        )

    if bool(getattr(settings, 'IS_PRODUCTION', False)) and per_minute > max_production_per_minute:
        return _check(
            key,
            'auth_safety',
            title,
            'critical',
            detail=f'{title} is too permissive for production.',
            configured_rate=rate,
            max_recommended_per_minute=max_production_per_minute,
        )

    return _check(
        key,
        'auth_safety',
        title,
        detail=f'{title} is configured.',
        configured_rate=rate,
        per_minute=per_minute,
    )


def _check_auth_login_throttle() -> dict[str, Any]:
    return _check_auth_scoped_throttle(
        key='auth_login_throttle',
        rate_key='auth_login',
        title='Login endpoint throttle',
        max_production_per_minute=30,
        traffic_label='login traffic',
    )


def _check_auth_register_throttle() -> dict[str, Any]:
    return _check_auth_scoped_throttle(
        key='auth_register_throttle',
        rate_key='auth_register',
        title='Registration endpoint throttle',
        max_production_per_minute=1,
        traffic_label='registration traffic',
    )


def _check_auth_refresh_throttle() -> dict[str, Any]:
    return _check_auth_scoped_throttle(
        key='auth_refresh_throttle',
        rate_key='auth_refresh',
        title='Refresh endpoint throttle',
        max_production_per_minute=120,
        traffic_label='refresh traffic',
    )


def _check_production_cache_backend() -> dict[str, Any]:
    cache_config = dict(getattr(settings, 'CACHES', {}).get('default', {}) or {})
    backend = str(cache_config.get('BACKEND') or '')
    location = str(cache_config.get('LOCATION') or '')
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'production_cache_backend',
            'auth_safety',
            'Shared cache backend',
            detail='Production cache backend is evaluated when IS_PRODUCTION=True.',
            backend=backend,
        )

    unsafe_markers = ('locmem', 'dummy', 'filebased', 'database')
    if not backend or any(marker in backend.lower() for marker in unsafe_markers):
        return _check(
            'production_cache_backend',
            'auth_safety',
            'Shared cache backend',
            'critical',
            detail='Configure a shared cache backend before accepting production traffic.',
            backend=backend,
        )
    if not location:
        return _check(
            'production_cache_backend',
            'auth_safety',
            'Shared cache backend',
            'critical',
            detail='Production cache backend is missing LOCATION.',
            backend=backend,
        )

    return _check(
        'production_cache_backend',
        'auth_safety',
        'Shared cache backend',
        detail='Production cache backend is shared and configured.',
        backend=backend,
    )


def _summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    by_status = {'ok': 0, 'warning': 0, 'degraded': 0, 'critical': 0}
    by_category: dict[str, dict[str, int]] = {}
    for check in checks:
        status = str(check.get('status') or 'critical')
        category = str(check.get('category') or 'unknown')
        by_status[status] = by_status.get(status, 0) + 1
        by_category.setdefault(category, {'ok': 0, 'warning': 0, 'degraded': 0, 'critical': 0})
        by_category[category][status] = by_category[category].get(status, 0) + 1
    return {
        'total_checks': len(checks),
        'ok_count': by_status.get('ok', 0),
        'warning_count': by_status.get('warning', 0),
        'degraded_count': by_status.get('degraded', 0),
        'critical_count': by_status.get('critical', 0),
        'by_status': by_status,
        'by_category': by_category,
    }


def _recommendations(summary: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    if summary.get('critical_count'):
        rows.append({'key': 'fix_critical_gate', 'severity': 'critical', 'title': 'Fix critical production readiness checks before release.'})
    if summary.get('degraded_count'):
        rows.append({'key': 'fix_degraded_contracts', 'severity': 'warning', 'title': 'Align degraded API or file contracts before release.'})
    rows.append({'key': 'run_smoke_suite', 'severity': 'info', 'title': 'Run the full v95 smoke suite in CI before tagging a release.'})
    return rows


def get_platform_production_readiness(
    *,
    include_commands: bool = True,
    include_recommendations: bool = True,
) -> dict[str, Any]:
    repo_root = Path(__file__).resolve().parents[3]
    checks: list[dict[str, Any]] = []
    checks.extend(_check_url(contract) for contract in URL_CONTRACTS)
    checks.extend(_check_symbol(contract) for contract in SYMBOL_CONTRACTS)
    checks.extend(_check_permissions(contract) for contract in PERMISSION_CONTRACTS)
    checks.extend(_check_file(contract, repo_root=repo_root) for contract in FILE_CONTRACTS)
    checks.extend(_check_executable_file(contract, repo_root=repo_root) for contract in EXECUTABLE_FILE_CONTRACTS)
    checks.append(_check_management_command())
    checks.append(_check_payment_safety())
    checks.append(_check_email_safety())
    checks.append(_check_payout_legal_eligibility_gate())
    checks.append(_check_auth_login_throttle())
    checks.append(_check_auth_register_throttle())
    checks.append(_check_auth_refresh_throttle())
    checks.append(_check_production_cache_backend())

    summary = _summarize(checks)
    status = _worst_status([str(check.get('status') or 'critical') for check in checks])
    payload: dict[str, Any] = {
        'status': status,
        'generated_at': timezone.now(),
        'version': 'v120',
        'scope': 'full platform production readiness',
        'summary': summary,
        'checks': checks,
        'api_surface': [{'key': item.key, 'name': item.name, 'expected_path': item.expected_path} for item in URL_CONTRACTS],
        'frontend_surface': FRONTEND_SURFACE,
        'seed_data': [
            {'key': 'migrate', 'command': 'cd backend && python manage.py migrate', 'description': 'Apply database schema before seed/smoke checks.'},
            {
                'key': 'seed_demo',
                'command': 'python scripts/bootstrap/seed_demo.py',
                'description': 'Create local demo trainer, student, products, payments, entitlements, payout and expired subscription data.',
                'scenarios': [
                    'trainer_with_products',
                    'student_with_active_course',
                    'failed_payment',
                    'refunded_order',
                    'payout_ready',
                    'subscription_expired',
                ],
            },
        ],
        'role_matrix': ROLE_MATRIX,
        'ci_gate': CI_GATE,
        'launch_candidate': {
            'project_version_file': 'VERSION',
            'release_notes': 'docs/launch/launch_candidate_v119.md',
            'api': '/api/v1/ops/admin/launch-candidate/',
            'next_step': 'v120 Production Launch Pack',
        },
        'production_launch_pack': {
            'project_version': 'v167.0',
            'docs': 'docs/launch/production/',
            'api': '/api/v1/ops/admin/production-launch-pack/',
            'ship_condition': 'Production gate green, production readiness ok, staging validation complete.',
        },
    }
    if include_commands:
        payload['smoke_commands'] = SMOKE_COMMANDS
        payload['management_commands'] = [{'key': 'check_production_readiness', 'name': 'check_production_readiness'}]
    if include_recommendations:
        payload['recommendations'] = _recommendations(summary)
    return payload
