from __future__ import annotations

import inspect
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

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
LOCAL_SERVICE_HOSTS = {'localhost', '127.0.0.1', '0.0.0.0'}


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
    if not bool(getattr(settings, 'PAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP', False)):
        unsafe_flags.append('PAYMENTS_WEBHOOK_REQUIRE_TIMESTAMP')
    if unsafe_flags:
        return _check(
            'payment_production_guards',
            'payment_safety',
            'Payment production guards',
            'critical',
            detail='Disable unsafe payment flags and require webhook timestamps before accepting production traffic.',
            unsafe_flags=unsafe_flags,
        )
    return _check(
        'payment_production_guards',
        'payment_safety',
        'Payment production guards',
        detail='Mock checkout and unverified provider-return mutations are disabled; webhook timestamps are required.',
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


def _check_auth_logout_throttle() -> dict[str, Any]:
    return _check_auth_scoped_throttle(
        key='auth_logout_throttle',
        rate_key='auth_logout',
        title='Logout endpoint throttle',
        max_production_per_minute=120,
        traffic_label='logout traffic',
    )


def _check_public_ingest_throttles() -> dict[str, Any]:
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    contracts = [
        (
            'analytics_collect',
            import_module('apps.analytics.api.views').AnalyticsEventCollectView,
            'analytics_collect',
        ),
        (
            'affiliate_click',
            import_module('apps.affiliates.api.views').PublicAffiliateTrackingViewSet,
            'affiliate_click',
        ),
        (
            'referral_track',
            import_module('apps.referrals.api.views').TrackReferralView,
            'referral_track',
        ),
    ]
    offenders = []
    for key, view_class, scope in contracts:
        if key not in rates:
            offenders.append(f'{key}_rate_missing')
        if getattr(view_class, 'throttle_scope', '') != scope:
            offenders.append(f'{key}_scope_missing')
        throttle_classes = [getattr(item, '__name__', str(item)) for item in getattr(view_class, 'throttle_classes', [])]
        if 'ScopedRateThrottle' not in throttle_classes:
            offenders.append(f'{key}_scoped_throttle_missing')
    if offenders:
        return _check(
            'public_ingest_throttles',
            'http_safety',
            'Public ingest throttles',
            'critical',
            detail='Public analytics, affiliate and referral ingestion endpoints must use endpoint-specific scoped throttles.',
            offenders=offenders,
        )
    return _check(
        'public_ingest_throttles',
        'http_safety',
        'Public ingest throttles',
        detail='Public analytics, affiliate and referral ingestion endpoints use endpoint-specific scoped throttles.',
    )


def _check_admin_ops_throttle() -> dict[str, Any]:
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    rate = str(rates.get('admin_ops') or '')
    per_minute = _rate_per_minute(rate)
    views_module = import_module('apps.ops.api.views')
    contracts = [
        'AdminOperationsDashboardView',
        'AdminOperationsHubView',
        'AdminProductionReadinessView',
        'AdminObservabilityRuntimeView',
        'AdminGlobalSearchView',
        'SupportConsoleView',
        'SupportNotificationResendView',
        'SupportEntitlementFixView',
        'AdminReconciliationReportView',
        'AdminReconciliationRepairView',
        'AdminReconciliationSnapshotCaptureView',
        'AdminReconciliationSnapshotCompareView',
    ]
    offenders = []
    if per_minute is None:
        offenders.append('admin_ops_rate_missing')
    elif bool(getattr(settings, 'IS_PRODUCTION', False)) and per_minute > 120:
        offenders.append('admin_ops_rate_too_permissive')

    for view_name in contracts:
        view_class = getattr(views_module, view_name)
        if getattr(view_class, 'throttle_scope', '') != 'admin_ops':
            offenders.append(f'{view_name}_scope_missing')
        throttle_classes = [getattr(item, '__name__', str(item)) for item in getattr(view_class, 'throttle_classes', [])]
        if 'ScopedRateThrottle' not in throttle_classes:
            offenders.append(f'{view_name}_scoped_throttle_missing')

    if offenders:
        return _check(
            'admin_ops_throttle',
            'http_safety',
            'Admin operations throttle',
            'critical',
            detail='Admin operations, support and reconciliation endpoints must use an endpoint-specific scoped throttle.',
            offenders=offenders,
            configured_rate=rate,
        )

    return _check(
        'admin_ops_throttle',
        'http_safety',
        'Admin operations throttle',
        detail='Admin operations, support and reconciliation endpoints use scoped throttling.',
        configured_rate=rate,
        per_minute=per_minute,
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
    parsed_location = urlparse(location)
    if (parsed_location.hostname or '').lower() in LOCAL_SERVICE_HOSTS:
        return _check(
            'production_cache_backend',
            'auth_safety',
            'Shared cache backend',
            'critical',
            detail='Production cache backend must not point at localhost.',
            backend=backend,
            location=location,
        )

    return _check(
        'production_cache_backend',
        'auth_safety',
        'Shared cache backend',
        detail='Production cache backend is shared and configured.',
        backend=backend,
    )


def _check_celery_production_config() -> dict[str, Any]:
    broker_url = str(getattr(settings, 'CELERY_BROKER_URL', '') or '')
    result_backend = str(getattr(settings, 'CELERY_RESULT_BACKEND', '') or '')
    eager = bool(getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False))
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'celery_production_config',
            'task_safety',
            'Background task configuration',
            detail='Production background task configuration is evaluated when IS_PRODUCTION=True.',
            broker_url=broker_url,
        )

    unsafe = []
    for key, value in (
        ('CELERY_BROKER_URL', broker_url),
        ('CELERY_RESULT_BACKEND', result_backend),
    ):
        parsed = urlparse(value)
        if not parsed.scheme or (parsed.hostname or '').lower() in LOCAL_SERVICE_HOSTS:
            unsafe.append(key)
    if eager:
        unsafe.append('CELERY_TASK_ALWAYS_EAGER')
    if unsafe:
        return _check(
            'celery_production_config',
            'task_safety',
            'Background task configuration',
            'critical',
            detail='Production background jobs must use shared broker/result backend and run asynchronously.',
            unsafe_flags=unsafe,
        )
    return _check(
        'celery_production_config',
        'task_safety',
        'Background task configuration',
        detail='Production Celery broker/result backend are shared and eager mode is disabled.',
    )


def _check_error_tracking_production_config(*, repo_root: Path) -> dict[str, Any]:
    dsn = str(getattr(settings, 'SENTRY_DSN', '') or '')
    requirements_path = repo_root / 'backend' / 'requirements.txt'
    pyproject_path = repo_root / 'backend' / 'pyproject.toml'
    integration_path = repo_root / 'backend' / 'config' / 'error_tracking.py'
    settings_path = repo_root / 'backend' / 'config' / 'settings' / 'base.py'
    dependency_sources = []
    for path in (requirements_path, pyproject_path):
        if path.exists():
            dependency_sources.append(path.read_text().lower())
    dependency_configured = any('sentry-sdk' in source for source in dependency_sources)
    integration_source = integration_path.read_text() if integration_path.exists() else ''
    settings_source = settings_path.read_text() if settings_path.exists() else ''
    integration_configured = all(
        fragment in integration_source
        for fragment in (
            'sentry_sdk.init',
            'DjangoIntegration',
            'CeleryIntegration',
            'RedisIntegration',
        )
    ) and 'configure_error_tracking(' in settings_source
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'error_tracking_production_config',
            'observability_safety',
            'External error tracking',
            detail='Production external error tracking is evaluated when IS_PRODUCTION=True.',
            dependency_configured=dependency_configured,
            integration_configured=integration_configured,
        )

    parsed = urlparse(dsn)
    unsafe = []
    if parsed.scheme != 'https' or not parsed.netloc or (parsed.hostname or '').lower() in LOCAL_SERVICE_HOSTS:
        unsafe.append('SENTRY_DSN')
    if not dependency_configured:
        unsafe.append('sentry_sdk_dependency')
    if not integration_configured:
        unsafe.append('sentry_sdk_initialization')
    if unsafe:
        return _check(
            'error_tracking_production_config',
            'observability_safety',
            'External error tracking',
            'critical',
            detail='Production must configure external error tracking, include sentry-sdk and initialize it at startup.',
            unsafe_flags=unsafe,
        )
    return _check(
        'error_tracking_production_config',
        'observability_safety',
        'External error tracking',
        detail='Production Sentry DSN, sentry-sdk dependency and startup initialization are configured.',
    )


def _check_media_storage_production_config() -> dict[str, Any]:
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'media_storage_production_config',
            'storage_safety',
            'Media storage configuration',
            detail='Production media storage configuration is evaluated when IS_PRODUCTION=True.',
        )

    endpoint = str(getattr(settings, 'VK_S3_ENDPOINT_URL', '') or '')
    access_key = str(getattr(settings, 'VK_S3_ACCESS_KEY_ID', '') or '')
    secret_key = str(getattr(settings, 'VK_S3_SECRET_ACCESS_KEY', '') or '')
    private_bucket = str(getattr(settings, 'VK_PRIVATE_BUCKET', '') or '')
    public_bucket = str(getattr(settings, 'VK_PUBLIC_BUCKET', '') or '')
    unsafe = []
    if not endpoint.startswith('https://') or 'localhost' in endpoint or '127.0.0.1' in endpoint:
        unsafe.append('VK_S3_ENDPOINT_URL')
    if not access_key or access_key in {'change-me', 'replace-me'}:
        unsafe.append('VK_S3_ACCESS_KEY_ID')
    if not secret_key or secret_key in {'change-me', 'replace-me'}:
        unsafe.append('VK_S3_SECRET_ACCESS_KEY')
    if not private_bucket:
        unsafe.append('VK_PRIVATE_BUCKET')
    if not public_bucket:
        unsafe.append('VK_PUBLIC_BUCKET')
    if private_bucket and public_bucket and private_bucket == public_bucket:
        unsafe.append('VK_BUCKETS_NOT_SEPARATED')
    if unsafe:
        return _check(
            'media_storage_production_config',
            'storage_safety',
            'Media storage configuration',
            'critical',
            detail='Configure production S3 endpoint, credentials and separate public/private buckets.',
            unsafe_flags=unsafe,
        )
    return _check(
        'media_storage_production_config',
        'storage_safety',
        'Media storage configuration',
        detail='Production media storage uses HTTPS S3 endpoint, credentials and separated buckets.',
    )


def _check_media_upload_validation_contract() -> dict[str, Any]:
    serializer_module = import_module('apps.videos.api.serializers')
    module_source = inspect.getsource(serializer_module)
    max_upload_bytes = int(getattr(settings, 'MEDIA_MAX_UPLOAD_BYTES', 0) or 0)
    required_fragments = {
        'content_type_extension_map': 'UPLOAD_CONTENT_TYPE_EXTENSIONS',
        'filename_path_strip': 'PurePath',
        'max_upload_size': 'MEDIA_MAX_UPLOAD_BYTES',
        'sha256_regex': 'CHECKSUM_SHA256_RE',
    }
    offenders = [key for key, fragment in required_fragments.items() if fragment not in module_source]
    if max_upload_bytes <= 0:
        offenders.append('MEDIA_MAX_UPLOAD_BYTES_missing')

    if offenders:
        return _check(
            'media_upload_validation_contract',
            'storage_safety',
            'Media upload validation contract',
            'critical',
            detail='Upload intents must validate filename, MIME/extension consistency, maximum size and checksum format.',
            offenders=offenders,
            max_upload_bytes=max_upload_bytes,
        )

    return _check(
        'media_upload_validation_contract',
        'storage_safety',
        'Media upload validation contract',
        detail='Upload intents validate filename, MIME/extension consistency, maximum size and checksum format.',
        max_upload_bytes=max_upload_bytes,
    )


def _check_media_upload_permission_contract() -> dict[str, Any]:
    views_module = import_module('apps.videos.api.views')
    permissions_module = import_module('apps.access_control.permissions')
    upload_views = {
        'UploadIntentCreateApi': getattr(views_module, 'UploadIntentCreateApi'),
        'UploadIntentCompleteApi': getattr(views_module, 'UploadIntentCompleteApi'),
    }
    offenders = []
    permission_names_by_view = {}
    for view_name, view_class in upload_views.items():
        permission_classes = list(getattr(view_class, 'permission_classes', []) or [])
        permission_names = [getattr(item, '__name__', str(item)) for item in permission_classes]
        permission_names_by_view[view_name] = permission_names
        if getattr(permissions_module, 'CanUploadMedia') not in permission_classes:
            offenders.append(f'{view_name}_CanUploadMedia_missing')
        if 'AllowAny' in permission_names:
            offenders.append(f'{view_name}_AllowAny')
    complete_source = inspect.getsource(getattr(upload_views['UploadIntentCompleteApi'], 'post'))
    if 'asset.status != MediaAsset.Status.DRAFT' not in complete_source:
        offenders.append('UploadIntentCompleteApi_state_guard_missing')
    if offenders:
        return _check(
            'media_upload_permission_contract',
            'storage_safety',
            'Media upload permission contract',
            'critical',
            detail='Media upload intents must require the media.upload capability, not only a logged-in account.',
            offenders=offenders,
            permission_classes=permission_names_by_view,
        )
    return _check(
        'media_upload_permission_contract',
        'storage_safety',
        'Media upload permission contract',
        detail='Media upload intents require the media.upload capability and complete only from draft state.',
        permission_classes=permission_names_by_view,
    )


def _check_media_upload_verification_contract() -> dict[str, Any]:
    task_module = import_module('apps.videos.tasks')
    source = inspect.getsource(task_module)
    required_fragments = {
        'uploaded_state_guard': 'asset.status != MediaAsset.Status.UPLOADED',
        'storage_head': 'storage_service.head_object',
        'content_length_required': 'ContentLength',
        'size_match': 'expected_content_length',
        'content_type_match': 'expected_content_type',
        'failure_state': 'MediaAsset.Status.FAILED',
    }
    offenders = [key for key, fragment in required_fragments.items() if fragment not in source]
    if offenders:
        return _check(
            'media_upload_verification_contract',
            'storage_safety',
            'Media upload verification contract',
            'critical',
            detail='Uploaded media must be verified against storage metadata before it can become publishable.',
            offenders=offenders,
        )
    return _check(
        'media_upload_verification_contract',
        'storage_safety',
        'Media upload verification contract',
        detail='Uploaded media verification checks state, object size and content type before marking assets verified.',
    )


def _check_media_read_ttl_contract() -> dict[str, Any]:
    service_module = import_module('apps.videos.services.issue_access_url')
    service_source = inspect.getsource(service_module)
    ttl_seconds = int(getattr(settings, 'MEDIA_READ_TTL_SECONDS', 0) or 0)
    max_ttl_seconds = int(getattr(settings, 'MEDIA_READ_MAX_TTL_SECONDS', 0) or 0)
    offenders = []
    if '_media_read_ttl_seconds' not in service_source or 'min(ttl_seconds, max_ttl_seconds)' not in service_source:
        offenders.append('read_ttl_clamp_missing')
    if ttl_seconds <= 0:
        offenders.append('MEDIA_READ_TTL_SECONDS_invalid')
    if max_ttl_seconds <= 0:
        offenders.append('MEDIA_READ_MAX_TTL_SECONDS_invalid')
    if bool(getattr(settings, 'IS_PRODUCTION', False)) and max_ttl_seconds > 900:
        offenders.append('MEDIA_READ_MAX_TTL_SECONDS_too_high')

    if offenders:
        return _check(
            'media_read_ttl_contract',
            'storage_safety',
            'Media read URL TTL contract',
            'critical',
            detail='Presigned media read URLs must have a positive TTL and a production-safe upper bound.',
            offenders=offenders,
            ttl_seconds=ttl_seconds,
            max_ttl_seconds=max_ttl_seconds,
        )

    return _check(
        'media_read_ttl_contract',
        'storage_safety',
        'Media read URL TTL contract',
        detail='Presigned media read URLs are clamped to a production-safe maximum TTL.',
        ttl_seconds=ttl_seconds,
        max_ttl_seconds=max_ttl_seconds,
    )


def _check_csv_export_safety_contract(*, repo_root: Path) -> dict[str, Any]:
    files = {
        'common_csv_safe': repo_root / 'backend' / 'common' / 'csv_safe.py',
        'audit_export': repo_root / 'backend' / 'apps' / 'audit' / 'api' / 'views.py',
        'referrals_export': repo_root / 'backend' / 'apps' / 'referrals' / 'api' / 'admin_views.py',
        'payouts_export': repo_root / 'backend' / 'apps' / 'payouts' / 'api' / 'ops_views.py',
        'finance_documents_export': repo_root / 'backend' / 'apps' / 'finance_documents' / 'services' / 'commercial_documents.py',
        'finance_reporting_export': repo_root / 'backend' / 'apps' / 'finance_reporting' / 'services' / 'exporters.py',
    }
    offenders = []
    helper_source = files['common_csv_safe'].read_text() if files['common_csv_safe'].exists() else ''
    if 'CSV_FORMULA_PREFIXES' not in helper_source or 'csv_safe_value' not in helper_source:
        offenders.append('common_csv_safe_value_missing')
    if 'spreadsheet_safe_value' not in helper_source:
        offenders.append('common_spreadsheet_safe_value_missing')

    for key, path in files.items():
        if key == 'common_csv_safe':
            continue
        source = path.read_text() if path.exists() else ''
        if 'csv_safe_value' not in source:
            offenders.append(f'{key}_missing_csv_safe_value')
        if key in {'payouts_export', 'finance_reporting_export'} and 'spreadsheet_safe_value' not in source:
            offenders.append(f'{key}_missing_spreadsheet_safe_value')

    if offenders:
        return _check(
            'csv_export_safety_contract',
            'export_safety',
            'Spreadsheet export formula injection safety',
            'critical',
            detail='Admin CSV/XLSX exports must escape values that spreadsheet apps interpret as formulas.',
            offenders=offenders,
        )

    return _check(
        'csv_export_safety_contract',
        'export_safety',
        'Spreadsheet export formula injection safety',
        detail='Admin CSV/XLSX exports use shared formula-injection escaping.',
    )


def _check_backup_restore_contract(*, repo_root: Path) -> dict[str, Any]:
    backup_script = repo_root / 'scripts' / 'ops' / 'backup_postgres.sh'
    restore_script = repo_root / 'scripts' / 'ops' / 'verify_postgres_restore.sh'
    backup_doc = repo_root / 'docs' / 'launch' / 'production' / 'backup.md'
    restore_runbook = repo_root / 'ops' / 'runbooks' / 'database-restore.md'
    offenders = []

    backup_source = backup_script.read_text() if backup_script.exists() else ''
    restore_source = restore_script.read_text() if restore_script.exists() else ''
    backup_doc_source = backup_doc.read_text() if backup_doc.exists() else ''
    restore_runbook_source = restore_runbook.read_text() if restore_runbook.exists() else ''

    if not backup_script.exists():
        offenders.append('backup_script_missing')
    elif not backup_script.stat().st_mode & 0o111:
        offenders.append('backup_script_not_executable')
    if not restore_script.exists():
        offenders.append('restore_script_missing')
    elif not restore_script.stat().st_mode & 0o111:
        offenders.append('restore_script_not_executable')

    required_backup_fragments = (
        'set -euo pipefail',
        ': "${DATABASE_URL:?DATABASE_URL is required}"',
        'pg_dump --no-owner --no-privileges --format=plain "$DATABASE_URL"',
        'sha256sum "$BACKUP_FILE" > "$CHECKSUM_FILE"',
    )
    for fragment in required_backup_fragments:
        if fragment not in backup_source:
            offenders.append(f'backup_script_missing:{fragment}')

    required_restore_fragments = (
        'set -euo pipefail',
        ': "${RESTORE_DATABASE_URL:?RESTORE_DATABASE_URL is required}"',
        ': "${RESTORE_TARGET_ISOLATED:?Set RESTORE_TARGET_ISOLATED=1',
        'RESTORE_TARGET_ISOLATED" != "1"',
        'gzip -t "$BACKUP_FILE"',
        'gzip -cd "$BACKUP_FILE" | psql "$RESTORE_DATABASE_URL" --set ON_ERROR_STOP=1',
    )
    for fragment in required_restore_fragments:
        if fragment not in restore_source:
            offenders.append(f'restore_script_missing:{fragment}')

    if 'scripts/ops/backup_postgres.sh' not in backup_doc_source:
        offenders.append('backup_doc_missing_backup_script')
    if 'scripts/ops/verify_postgres_restore.sh' not in backup_doc_source:
        offenders.append('backup_doc_missing_restore_script')
    if 'Restore the approved backup into an isolated database first.' not in restore_runbook_source:
        offenders.append('restore_runbook_missing_isolated_restore')

    if offenders:
        return _check(
            'backup_restore_contract',
            'backup_safety',
            'Backup and restore contract',
            'critical',
            detail='Production launch must include executable PostgreSQL backup and isolated restore verification scripts.',
            offenders=offenders,
        )

    return _check(
        'backup_restore_contract',
        'backup_safety',
        'Backup and restore contract',
        detail='PostgreSQL backup and isolated restore verification scripts are documented and executable.',
    )


def _check_production_database_backend() -> dict[str, Any]:
    database_config = dict(getattr(settings, 'DATABASES', {}).get('default', {}) or {})
    engine = str(database_config.get('ENGINE') or '')
    name = str(database_config.get('NAME') or '')
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'production_database_backend',
            'database_safety',
            'Production database backend',
            detail='Production database backend is evaluated when IS_PRODUCTION=True.',
            engine=engine,
        )
    if 'sqlite' in engine.lower():
        return _check(
            'production_database_backend',
            'database_safety',
            'Production database backend',
            'critical',
            detail='Production must not use SQLite fallback.',
            engine=engine,
            name=name,
        )
    if 'postgresql' not in engine.lower():
        return _check(
            'production_database_backend',
            'database_safety',
            'Production database backend',
            'critical',
            detail='Production database must use PostgreSQL.',
            engine=engine,
            name=name,
        )
    return _check(
        'production_database_backend',
        'database_safety',
        'Production database backend',
        detail='Production database backend uses PostgreSQL.',
        engine=engine,
    )


def _check_production_origin_security() -> dict[str, Any]:
    csrf_origins = list(getattr(settings, 'CSRF_TRUSTED_ORIGINS', []) or [])
    cors_origins = list(getattr(settings, 'CORS_ALLOWED_ORIGINS', []) or [])
    if not bool(getattr(settings, 'IS_PRODUCTION', False)):
        return _check(
            'production_origin_security',
            'http_safety',
            'Production trusted origins',
            detail='Production trusted origins are evaluated when IS_PRODUCTION=True.',
            csrf_trusted_origins=csrf_origins,
            cors_allowed_origins=cors_origins,
        )
    unsafe = []
    if not csrf_origins:
        unsafe.append('CSRF_TRUSTED_ORIGINS')
    if not cors_origins:
        unsafe.append('CORS_ALLOWED_ORIGINS')
    if any(str(origin).lower().startswith('http://') for origin in csrf_origins):
        unsafe.append('CSRF_TRUSTED_ORIGINS_HTTP')
    if any(str(origin).lower().startswith('http://') for origin in cors_origins):
        unsafe.append('CORS_ALLOWED_ORIGINS_HTTP')
    if unsafe:
        return _check(
            'production_origin_security',
            'http_safety',
            'Production trusted origins',
            'critical',
            detail='Production trusted origins must be explicit https:// origins.',
            unsafe_flags=unsafe,
            csrf_trusted_origins=csrf_origins,
            cors_allowed_origins=cors_origins,
        )
    return _check(
        'production_origin_security',
        'http_safety',
        'Production trusted origins',
        detail='Production trusted origins use explicit HTTPS origins.',
        csrf_trusted_origins=csrf_origins,
        cors_allowed_origins=cors_origins,
    )


def _check_runtime_apps_namespace(*, repo_root: Path) -> dict[str, Any]:
    root_apps = repo_root / 'apps' / '__init__.py'
    backend_apps = repo_root / 'backend' / 'apps' / '__init__.py'
    if root_apps.exists():
        return _check(
            'runtime_apps_namespace',
            'python_contract',
            'Single runtime apps namespace',
            'critical',
            detail='Root /apps is importable and can shadow backend/apps.',
            root_apps=str(root_apps),
        )
    if not backend_apps.exists():
        return _check(
            'runtime_apps_namespace',
            'python_contract',
            'Single runtime apps namespace',
            'critical',
            detail='backend/apps package is missing.',
            backend_apps=str(backend_apps),
        )
    return _check(
        'runtime_apps_namespace',
        'python_contract',
        'Single runtime apps namespace',
        detail='Only backend/apps is available as the runtime apps package.',
    )


def _check_django_settings_layout(*, repo_root: Path) -> dict[str, Any]:
    config_dir = repo_root / 'backend' / 'config'
    required = [
        config_dir / 'settings' / 'base.py',
        config_dir / 'settings' / 'local.py',
        config_dir / 'settings' / 'production.py',
        config_dir / 'settings' / 'test.py',
    ]
    missing = [str(path.relative_to(repo_root)) for path in required if not path.exists()]
    if missing:
        return _check(
            'django_settings_layout',
            'settings_safety',
            'Canonical Django settings layout',
            'critical',
            detail='Canonical config/settings package modules are missing.',
            missing=missing,
        )

    legacy_settings = (config_dir / 'settings.py').read_text().strip()
    legacy_test_settings = (config_dir / 'settings_test.py').read_text().strip()
    expected = {
        'settings.py': 'from config.settings.base import *  # noqa: F401,F403',
        'settings_test.py': 'from config.settings.test import *  # noqa: F401,F403',
    }
    offenders = []
    if legacy_settings != expected['settings.py']:
        offenders.append('backend/config/settings.py')
    if legacy_test_settings != expected['settings_test.py']:
        offenders.append('backend/config/settings_test.py')
    if offenders:
        return _check(
            'django_settings_layout',
            'settings_safety',
            'Canonical Django settings layout',
            'critical',
            detail='Legacy settings modules must remain thin compatibility shims.',
            offenders=offenders,
        )
    return _check(
        'django_settings_layout',
        'settings_safety',
        'Canonical Django settings layout',
        detail='Runtime settings live in config/settings; legacy modules are compatibility shims.',
    )


def _check_backend_migration_release_job(*, repo_root: Path) -> dict[str, Any]:
    entrypoint_path = repo_root / 'deploy' / 'backend' / 'entrypoint.sh'
    release_path = repo_root / 'deploy' / 'backend' / 'release.sh'
    compose_path = repo_root / 'docker-compose.yml'
    missing = [
        str(path.relative_to(repo_root))
        for path in (entrypoint_path, release_path, compose_path)
        if not path.exists()
    ]
    if missing:
        return _check(
            'backend_migration_release_job',
            'deploy_safety',
            'Backend migration release job',
            'critical',
            detail='Deploy runtime or release job files are missing.',
            missing=missing,
        )

    entrypoint = entrypoint_path.read_text()
    release = release_path.read_text()
    compose = compose_path.read_text()
    offenders = []
    if 'manage.py migrate' in entrypoint:
        offenders.append('entrypoint_migrate')
    if 'collectstatic' in entrypoint:
        offenders.append('entrypoint_collectstatic')
    if 'manage.py migrate --noinput' not in release:
        offenders.append('release_missing_migrate')
    if 'collectstatic --noinput' not in release:
        offenders.append('release_missing_collectstatic')
    if '  release:' not in compose or '/app/deploy/backend/release.sh' not in compose:
        offenders.append('compose_missing_release_service')
    if offenders:
        return _check(
            'backend_migration_release_job',
            'deploy_safety',
            'Backend migration release job',
            'critical',
            detail='Migrations must run in a one-shot release job, not every backend app start.',
            offenders=offenders,
        )
    return _check(
        'backend_migration_release_job',
        'deploy_safety',
        'Backend migration release job',
        detail='Backend app start does not run migrations; release service owns migrate and collectstatic.',
    )


def _check_celery_worker_queue_coverage(*, repo_root: Path) -> dict[str, Any]:
    worker_path = repo_root / 'deploy' / 'backend' / 'celery-worker.sh'
    celery_path = repo_root / 'backend' / 'config' / 'celery.py'
    missing = [
        str(path.relative_to(repo_root))
        for path in (worker_path, celery_path)
        if not path.exists()
    ]
    if missing:
        return _check(
            'celery_worker_queue_coverage',
            'task_safety',
            'Celery worker queue coverage',
            'critical',
            detail='Celery worker deploy script or routing config is missing.',
            missing=missing,
        )

    worker = worker_path.read_text()
    celery_config = celery_path.read_text()
    offenders = []
    if 'CELERY_WORKER_QUEUES' not in worker:
        offenders.append('worker_queues_not_configurable')
    for route_symbol in ('OUTBOX_QUEUE', 'OPS_QUEUE', 'EMAIL_QUEUE', 'DEFAULT_QUEUE'):
        if route_symbol not in celery_config:
            offenders.append(f'{route_symbol.lower()}_missing')
    for queue_name in ('default', 'outbox', 'ops', 'email'):
        if queue_name not in worker:
            offenders.append(f'{queue_name}_queue_not_consumed_by_default_worker')
    if offenders:
        return _check(
            'celery_worker_queue_coverage',
            'task_safety',
            'Celery worker queue coverage',
            'critical',
            detail='Production Celery worker default queues must cover routed outbox, ops, email and default tasks.',
            offenders=offenders,
        )
    return _check(
        'celery_worker_queue_coverage',
        'task_safety',
        'Celery worker queue coverage',
        detail='Production Celery worker defaults consume routed outbox, ops, email and default queues.',
    )


def _check_outbox_compose_overlay_runtime(*, repo_root: Path) -> dict[str, Any]:
    overlay_path = repo_root / 'docker-compose.outbox.yml'
    if not overlay_path.exists():
        return _check(
            'outbox_compose_overlay_runtime',
            'deploy_safety',
            'Outbox compose overlay runtime',
            'critical',
            detail='Optional outbox compose overlay is missing.',
        )

    overlay = overlay_path.read_text()
    offenders = []
    if 'dockerfile: deploy/backend/Dockerfile' not in overlay:
        offenders.append('canonical_backend_dockerfile_missing')
    if 'docker/celery/Dockerfile' in overlay:
        offenders.append('legacy_poetry_celery_dockerfile')
    if '${TRAINERHUB_ENV_FILE:-.env}' not in overlay:
        offenders.append('trainerhub_env_file_missing')
    if 'cd /app/backend' not in overlay:
        offenders.append('backend_workdir_missing')
    if '--queues=outbox,default' not in overlay:
        offenders.append('outbox_queue_missing')
    if offenders:
        return _check(
            'outbox_compose_overlay_runtime',
            'deploy_safety',
            'Outbox compose overlay runtime',
            'critical',
            detail='Outbox compose overlay must use the canonical backend image and consume outbox/default queues.',
            offenders=offenders,
        )
    return _check(
        'outbox_compose_overlay_runtime',
        'deploy_safety',
        'Outbox compose overlay runtime',
        detail='Outbox compose overlay uses canonical backend image, env file and outbox/default queues.',
    )


def _check_deploy_scripts_preflight(*, repo_root: Path) -> dict[str, Any]:
    deploy_path = repo_root / 'scripts' / 'deploy' / 'deploy.sh'
    migrate_path = repo_root / 'scripts' / 'deploy' / 'migrate.sh'
    missing = [
        str(path.relative_to(repo_root))
        for path in (deploy_path, migrate_path)
        if not path.exists()
    ]
    if missing:
        return _check(
            'deploy_scripts_preflight',
            'deploy_safety',
            'Deploy scripts preflight',
            'critical',
            detail='Deploy or migrate script is missing.',
            missing=missing,
        )

    offenders = []
    for key, path in (('deploy', deploy_path), ('migrate', migrate_path)):
        script = path.read_text()
        deploy_check = 'python manage.py check --deploy --fail-level WARNING'
        readiness = 'python manage.py check_production_readiness --summary-only --fail-on-degraded'
        release = 'docker compose run --rm release'
        if deploy_check not in script:
            offenders.append(f'{key}_deploy_check_missing')
        if readiness not in script:
            offenders.append(f'{key}_readiness_check_missing')
        if release not in script:
            offenders.append(f'{key}_release_job_missing')
        if deploy_check in script and release in script and script.index(deploy_check) > script.index(release):
            offenders.append(f'{key}_deploy_check_after_release')
        if readiness in script and release in script and script.index(readiness) > script.index(release):
            offenders.append(f'{key}_readiness_check_after_release')
    if offenders:
        return _check(
            'deploy_scripts_preflight',
            'deploy_safety',
            'Deploy scripts preflight',
            'critical',
            detail='Deploy scripts must run Django deploy checks and production readiness before release migrations.',
            offenders=offenders,
        )
    return _check(
        'deploy_scripts_preflight',
        'deploy_safety',
        'Deploy scripts preflight',
        detail='Deploy scripts run Django deploy checks and production readiness before release migrations.',
    )


def _check_deploy_image_tag_contract(*, repo_root: Path) -> dict[str, Any]:
    compose_path = repo_root / 'docker-compose.yml'
    deploy_path = repo_root / 'scripts' / 'deploy' / 'deploy.sh'
    migrate_path = repo_root / 'scripts' / 'deploy' / 'migrate.sh'
    workflow_path = repo_root / '.github' / 'workflows' / 'deploy.yml'
    missing = [
        str(path.relative_to(repo_root))
        for path in (compose_path, deploy_path, migrate_path, workflow_path)
        if not path.exists()
    ]
    if missing:
        return _check(
            'deploy_image_tag_contract',
            'deploy_safety',
            'Deploy image tag contract',
            'critical',
            detail='Deploy compose, scripts or workflow files are missing.',
            missing=missing,
        )

    compose = compose_path.read_text()
    deploy = deploy_path.read_text()
    migrate = migrate_path.read_text()
    workflow = workflow_path.read_text()
    offenders = []
    if 'image: ${BACKEND_IMAGE:-trainerhub-backend:local}' not in compose:
        offenders.append('backend_image_ref_missing')
    if 'image: ${FRONTEND_IMAGE:-trainerhub-frontend:local}' not in compose:
        offenders.append('frontend_image_ref_missing')
    for key, script in (('deploy', deploy), ('migrate', migrate)):
        if ': "${REGISTRY:?REGISTRY is required}"' not in script:
            offenders.append(f'{key}_registry_required_missing')
        if ': "${IMAGE_TAG:?IMAGE_TAG is required}"' not in script:
            offenders.append(f'{key}_image_tag_required_missing')
        if 'BACKEND_IMAGE="${REGISTRY}/trainerhub-backend:${IMAGE_TAG}"' not in script:
            offenders.append(f'{key}_backend_image_export_missing')
    if 'FRONTEND_IMAGE="${REGISTRY}/trainerhub-frontend:${IMAGE_TAG}"' not in deploy:
        offenders.append('deploy_frontend_image_export_missing')
    if 'export REGISTRY=${{ vars.REGISTRY_URL }}' not in workflow:
        offenders.append('workflow_registry_export_missing')
    if offenders:
        return _check(
            'deploy_image_tag_contract',
            'deploy_safety',
            'Deploy image tag contract',
            'critical',
            detail='Deploy must use registry/image tag variables consistently across workflow, scripts and compose.',
            offenders=offenders,
        )
    return _check(
        'deploy_image_tag_contract',
        'deploy_safety',
        'Deploy image tag contract',
        detail='Deploy workflow, scripts and compose consistently use registry/image-tagged backend and frontend images.',
    )


def _check_docker_build_context_hygiene(*, repo_root: Path) -> dict[str, Any]:
    dockerignore_path = repo_root / '.dockerignore'
    if not dockerignore_path.exists():
        return _check(
            'docker_build_context_hygiene',
            'deploy_safety',
            'Docker build context hygiene',
            'critical',
            detail='Repository .dockerignore is missing.',
        )

    dockerignore = dockerignore_path.read_text()
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
    missing = [pattern for pattern in required_patterns if pattern not in dockerignore]
    if missing:
        return _check(
            'docker_build_context_hygiene',
            'deploy_safety',
            'Docker build context hygiene',
            'critical',
            detail='Docker build context must exclude local env files, databases, dependency caches and test reports.',
            missing_patterns=missing,
        )
    return _check(
        'docker_build_context_hygiene',
        'deploy_safety',
        'Docker build context hygiene',
        detail='Docker build context excludes local env files, databases, dependency caches and test reports.',
    )


def _check_frontend_standalone_runtime(*, repo_root: Path) -> dict[str, Any]:
    dockerfile_path = repo_root / 'deploy' / 'frontend' / 'Dockerfile'
    next_config_path = repo_root / 'frontend' / 'next.config.ts'
    missing = [
        str(path.relative_to(repo_root))
        for path in (dockerfile_path, next_config_path)
        if not path.exists()
    ]
    if missing:
        return _check(
            'frontend_standalone_runtime',
            'deploy_safety',
            'Frontend standalone runtime',
            'critical',
            detail='Frontend Dockerfile or Next config is missing.',
            missing=missing,
        )

    dockerfile = dockerfile_path.read_text()
    next_config = next_config_path.read_text()
    offenders = []
    if "output: 'standalone'" not in next_config:
        offenders.append('next_standalone_output_missing')
    if '/app/frontend/.next/standalone ./' not in dockerfile:
        offenders.append('dockerfile_standalone_copy_missing')
    if '/app/frontend/.next/static ./.next/static' not in dockerfile:
        offenders.append('dockerfile_static_copy_missing')
    if 'CMD ["node", "server.js"]' not in dockerfile:
        offenders.append('dockerfile_server_js_cmd_missing')
    if 'NEXT_TELEMETRY_DISABLED=1' not in dockerfile:
        offenders.append('telemetry_disabled_missing')
    if 'NEXT_PUBLIC_API_BASE_URL' not in dockerfile:
        offenders.append('api_base_build_arg_missing')
    if offenders:
        return _check(
            'frontend_standalone_runtime',
            'deploy_safety',
            'Frontend standalone runtime',
            'critical',
            detail='Frontend Docker runtime must match Next standalone output and production API base configuration.',
            offenders=offenders,
        )
    return _check(
        'frontend_standalone_runtime',
        'deploy_safety',
        'Frontend standalone runtime',
        detail='Frontend Docker runtime matches Next standalone output and production API base configuration.',
    )


def _check_nginx_edge_proxy_contract(*, repo_root: Path) -> dict[str, Any]:
    nginx_path = repo_root / 'deploy' / 'nginx' / 'nginx.conf'
    if not nginx_path.exists():
        return _check(
            'nginx_edge_proxy_contract',
            'http_safety',
            'Nginx edge proxy contract',
            'critical',
            detail='Nginx config is missing.',
        )

    nginx = nginx_path.read_text()
    required_fragments = [
        'map $http_upgrade $connection_upgrade',
        'proxy_set_header X-Forwarded-Host $host;',
        'proxy_set_header X-Forwarded-Port $server_port;',
        'proxy_set_header Upgrade $http_upgrade;',
        'proxy_set_header Connection $connection_upgrade;',
        'add_header X-Content-Type-Options "nosniff" always;',
        'add_header X-Frame-Options "DENY" always;',
        'add_header Referrer-Policy "strict-origin-when-cross-origin" always;',
        'location /flower/',
        'return 404;',
        'limit_req_zone $binary_remote_addr zone=api_per_ip',
        'limit_req_zone $binary_remote_addr zone=auth_per_ip',
    ]
    missing = [fragment for fragment in required_fragments if fragment not in nginx]
    if missing:
        return _check(
            'nginx_edge_proxy_contract',
            'http_safety',
            'Nginx edge proxy contract',
            'critical',
            detail='Nginx must preserve forwarded request metadata, support upgrade connections and block Flower from public access.',
            missing_fragments=missing,
        )
    return _check(
        'nginx_edge_proxy_contract',
        'http_safety',
        'Nginx edge proxy contract',
        detail='Nginx preserves forwarded metadata, supports upgrade connections, applies security headers and blocks Flower.',
    )


def _check_cookie_only_auth_contract() -> dict[str, Any]:
    auth_classes = tuple(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_AUTHENTICATION_CLASSES', ()))
    if not auth_classes or auth_classes[0] != 'apps.authn.authentication.CookieJWTAuthentication':
        return _check(
            'cookie_jwt_authentication',
            'auth_safety',
            'Cookie JWT authentication',
            'critical',
            detail='CookieJWTAuthentication must be the first DRF authentication class.',
            configured=list(auth_classes),
        )
    if not bool(getattr(settings, 'SIMPLE_JWT', {}).get('BLACKLIST_AFTER_ROTATION', False)):
        return _check(
            'cookie_jwt_authentication',
            'auth_safety',
            'Cookie JWT authentication',
            'critical',
            detail='Refresh token blacklist must be enabled after rotation.',
            configured=list(auth_classes),
        )

    auth_module = import_module('apps.authn.authentication')
    auth_source = inspect.getsource(getattr(auth_module, 'CookieJWTAuthentication'))
    enforce_csrf_source = inspect.getsource(getattr(auth_module, 'enforce_csrf'))
    views_module = import_module('apps.authn.api.views')
    refresh_source = inspect.getsource(getattr(views_module, 'RefreshView'))
    logout_source = inspect.getsource(getattr(views_module, 'LogoutView'))
    if (
        'enforce_csrf(request)' not in auth_source
        or 'CSRFCheck' not in enforce_csrf_source
        or 'from_cookie and refresh_token' not in refresh_source
        or 'from_cookie and refresh_token' not in logout_source
    ):
        return _check(
            'cookie_jwt_authentication',
            'auth_safety',
            'Cookie JWT authentication',
            'critical',
            detail='Cookie JWT auth and refresh-cookie auth must enforce CSRF on unsafe browser requests.',
        )

    public_payload_source = inspect.getsource(getattr(views_module, '_public_auth_payload'))
    if 'access_token' in public_payload_source or 'refresh_token' in public_payload_source:
        return _check(
            'cookie_only_auth_response',
            'auth_safety',
            'Cookie-only auth response',
            'critical',
            detail='Auth response payload must not expose JWT tokens in JSON.',
        )

    return _check(
        'cookie_jwt_authentication',
        'auth_safety',
        'Cookie JWT authentication',
        detail='Cookie auth is first, CSRF is enforced, refresh blacklist is enabled and public auth JSON omits JWT tokens.',
    )


def _check_default_api_permissions() -> dict[str, Any]:
    permission_classes = tuple(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_PERMISSION_CLASSES', ()))
    if permission_classes != ('rest_framework.permissions.IsAuthenticated',):
        return _check(
            'default_api_permissions',
            'permissions',
            'DRF default API permissions',
            'critical',
            detail='DRF default permission must require authentication; public endpoints must opt into AllowAny explicitly.',
            configured=list(permission_classes),
        )
    return _check(
        'default_api_permissions',
        'permissions',
        'DRF default API permissions',
        detail='DRF defaults require authentication and public APIs must opt into AllowAny explicitly.',
    )


def _check_audit_context_redaction() -> dict[str, Any]:
    audit_source = inspect.getsource(import_module('apps.audit.services'))
    required_fragments = (
        'SENSITIVE_CONTEXT_KEYS',
        'REDACTED_VALUE',
        '_redact_sensitive',
        'AuditService._redact_sensitive(value or {})',
        'password',
        'refresh_token',
        'authorization',
        'cookie',
    )
    offenders = [fragment for fragment in required_fragments if fragment not in audit_source]
    if offenders:
        return _check(
            'audit_context_redaction',
            'audit_safety',
            'Audit context redaction',
            'critical',
            detail='Audit context must redact password, token, authorization and cookie values before persistence.',
            offenders=offenders,
        )
    return _check(
        'audit_context_redaction',
        'audit_safety',
        'Audit context redaction',
        detail='Audit context recursively redacts password, token, authorization and cookie values before persistence.',
    )


def _check_public_review_disclosure_contract() -> dict[str, Any]:
    serializers_module = import_module('apps.reviews.api.serializers')
    public_source = inspect.getsource(getattr(serializers_module, 'PublicReviewSerializer'))
    target_payload_source = inspect.getsource(getattr(serializers_module, 'TargetReviewPayloadSerializer'))
    forbidden_fragments = (
        'moderation_note',
        'moderated_by_id',
        'moderated_at',
        'trainer_reply_by_id',
    )
    offenders = [fragment for fragment in forbidden_fragments if fragment in public_source]
    if 'PublicReviewSerializer' not in target_payload_source:
        offenders.append('target_payload_not_using_public_review_serializer')

    if offenders:
        return _check(
            'public_review_disclosure_contract',
            'privacy_safety',
            'Public review disclosure contract',
            'critical',
            detail='Public review payloads must not expose moderation notes or internal actor identifiers.',
            offenders=offenders,
        )

    return _check(
        'public_review_disclosure_contract',
        'privacy_safety',
        'Public review disclosure contract',
        detail='Public review payloads hide moderation notes and internal actor identifiers.',
    )


def _check_review_self_moderation_contract() -> dict[str, Any]:
    selectors_module = import_module('apps.reviews.selectors')
    source = inspect.getsource(getattr(selectors_module, 'get_review_eligibility'))
    offenders = []
    if 'self_review' not in source:
        offenders.append('self_review_guard_missing')
    if "target.get('trainer_id')" not in source or "getattr(user, 'id'" not in source:
        offenders.append('trainer_user_comparison_missing')
    self_review_pos = source.find('self_review')
    entitlement_pos = source.find('has_active_entitlement')
    if self_review_pos == -1 or entitlement_pos == -1 or self_review_pos > entitlement_pos:
        offenders.append('self_review_guard_after_entitlement')
    if offenders:
        return _check(
            'review_self_moderation_contract',
            'privacy_safety',
            'Review self-moderation contract',
            'critical',
            detail='Review eligibility must reject trainer self-reviews before entitlement checks.',
            offenders=offenders,
        )
    return _check(
        'review_self_moderation_contract',
        'privacy_safety',
        'Review self-moderation contract',
        detail='Review eligibility rejects trainer self-reviews before purchase entitlement checks.',
    )


def _check_review_write_throttle_contract() -> dict[str, Any]:
    views_module = import_module('apps.reviews.api.views')
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    target_view = getattr(views_module, 'TargetReviewsView')
    reply_view = getattr(views_module, 'TrainerReviewReplyView')
    get_throttles_source = inspect.getsource(getattr(target_view, 'get_throttles'))
    reply_throttle_classes = [getattr(item, '__name__', str(item)) for item in getattr(reply_view, 'throttle_classes', [])]
    offenders = []
    if 'review_write' not in rates:
        offenders.append('review_write_rate_missing')
    if 'review_reply' not in rates:
        offenders.append('review_reply_rate_missing')
    if getattr(target_view, 'throttle_scope', '') != 'review_write':
        offenders.append('target_reviews_write_scope_missing')
    if "self.request.method == 'POST'" not in get_throttles_source or 'ScopedRateThrottle()' not in get_throttles_source:
        offenders.append('target_reviews_post_only_throttle_missing')
    if getattr(reply_view, 'throttle_scope', '') != 'review_reply':
        offenders.append('trainer_reply_scope_missing')
    if 'ScopedRateThrottle' not in reply_throttle_classes:
        offenders.append('trainer_reply_scoped_throttle_missing')
    if offenders:
        return _check(
            'review_write_throttle_contract',
            'http_safety',
            'Review write throttle contract',
            'critical',
            detail='Review creation and trainer replies must use dedicated scoped throttles without throttling public review reads as writes.',
            offenders=offenders,
        )
    return _check(
        'review_write_throttle_contract',
        'http_safety',
        'Review write throttle contract',
        detail='Review creation and trainer replies use dedicated scoped throttles.',
        configured_rates={
            'review_write': rates.get('review_write'),
            'review_reply': rates.get('review_reply'),
        },
    )


def _check_review_reply_state_contract() -> dict[str, Any]:
    service_module = import_module('apps.reviews.services')
    source = inspect.getsource(getattr(service_module.ReviewService, 'reply_to_review'))
    offenders = []
    if 'review.status != Review.STATUS_PUBLISHED' not in source:
        offenders.append('published_state_guard_missing')
    if 'Only published reviews can receive trainer replies' not in source:
        offenders.append('published_state_error_missing')
    owner_pos = source.find('Only the owning trainer can reply')
    state_pos = source.find('review.status != Review.STATUS_PUBLISHED')
    save_pos = source.find("review.save(update_fields=['trainer_reply'")
    if state_pos == -1 or save_pos == -1 or state_pos > save_pos:
        offenders.append('published_state_guard_after_save')
    if offenders:
        return _check(
            'review_reply_state_contract',
            'privacy_safety',
            'Review reply state contract',
            'critical',
            detail='Trainer replies must be allowed only on published reviews.',
            offenders=offenders,
        )
    return _check(
        'review_reply_state_contract',
        'privacy_safety',
        'Review reply state contract',
        detail='Trainer replies are limited to published reviews.',
        owner_guard_before_state_guard=owner_pos != -1 and state_pos != -1 and owner_pos < state_pos,
    )


def _check_public_store_identity_contract() -> dict[str, Any]:
    source = inspect.getsource(import_module('apps.store.selectors'))
    if "'trainer_id'" in source or '"trainer_id"' in source:
        return _check(
            'public_store_identity_contract',
            'privacy_safety',
            'Public store identity contract',
            'critical',
            detail='Public legacy store payload must use trainer_slug/trainer_name instead of trainer_id.',
        )
    return _check(
        'public_store_identity_contract',
        'privacy_safety',
        'Public store identity contract',
        detail='Public legacy store payload uses trainer_slug/trainer_name and avoids trainer_id.',
    )


def _check_messaging_participant_privacy_contract() -> dict[str, Any]:
    views_module = import_module('apps.messaging.api.views')
    helper_source = inspect.getsource(getattr(views_module, '_require_participant'))
    messages_source = inspect.getsource(getattr(views_module.ConversationMessagesView, 'get_queryset'))
    mark_read_source = inspect.getsource(getattr(views_module.MarkReadView, 'post'))
    offenders = []
    if 'ConversationParticipant.DoesNotExist' not in helper_source or 'PermissionDenied' not in helper_source:
        offenders.append('require_participant_missing_permission_denied')
    if '_require_participant(conversation=conversation, user=self.request.user)' not in messages_source:
        offenders.append('messages_view_missing_participant_guard')
    if '_require_participant(conversation=conversation, user=request.user)' not in mark_read_source:
        offenders.append('mark_read_missing_participant_guard')
    if offenders:
        return _check(
            'messaging_participant_privacy_contract',
            'privacy_safety',
            'Messaging participant privacy contract',
            'critical',
            detail='Messaging read and mark-read endpoints must reject non-participants with a controlled permission error.',
            offenders=offenders,
        )
    return _check(
        'messaging_participant_privacy_contract',
        'privacy_safety',
        'Messaging participant privacy contract',
        detail='Messaging read and mark-read endpoints require conversation membership.',
    )


def _check_messaging_write_throttle_contract() -> dict[str, Any]:
    views_module = import_module('apps.messaging.api.views')
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    contracts = [
        ('messaging_start', getattr(views_module, 'StartConversationView')),
        ('messaging_send', getattr(views_module, 'SendMessageView')),
    ]
    offenders = []
    for scope, view_class in contracts:
        if scope not in rates:
            offenders.append(f'{scope}_rate_missing')
        if getattr(view_class, 'throttle_scope', '') != scope:
            offenders.append(f'{scope}_scope_missing')
        throttle_classes = [getattr(item, '__name__', str(item)) for item in getattr(view_class, 'throttle_classes', [])]
        if 'ScopedRateThrottle' not in throttle_classes:
            offenders.append(f'{scope}_scoped_throttle_missing')
    if offenders:
        return _check(
            'messaging_write_throttle_contract',
            'http_safety',
            'Messaging write throttle contract',
            'critical',
            detail='Messaging start/send endpoints must use dedicated scoped throttles to limit account spam.',
            offenders=offenders,
        )
    return _check(
        'messaging_write_throttle_contract',
        'http_safety',
        'Messaging write throttle contract',
        detail='Messaging start/send endpoints use dedicated scoped throttles.',
        configured_rates={scope: rates.get(scope) for scope, _view in contracts},
    )


def _check_provider_return_read_only() -> dict[str, Any]:
    views_module = import_module('apps.payments.api.views')
    source = inspect.getsource(getattr(views_module.PaymentViewSet, 'provider_return'))
    forbidden_calls = (
        'mark_succeeded',
        'mark_cancelled',
        'mark_failed',
        'mark_refunded',
        'mark_disputed',
        'mark_chargeback_lost',
        'mark_chargeback_won',
    )
    offenders = [name for name in forbidden_calls if name in source]
    if offenders:
        return _check(
            'provider_return_read_only',
            'payment_safety',
            'Provider return redirect is read-only',
            'critical',
            detail='Provider return must not mutate payment state from query parameters.',
            forbidden_calls=offenders,
        )
    return _check(
        'provider_return_read_only',
        'payment_safety',
        'Provider return redirect is read-only',
        detail='Provider return only reads payment status and returns a frontend redirect path.',
    )


def _check_public_webhook_signature_path() -> dict[str, Any]:
    views_module = import_module('apps.payments.api.views')
    source = inspect.getsource(getattr(views_module.PaymentWebhookViewSet, 'receive'))
    if 'PaymentWebhookService.handle(' in source:
        return _check(
            'public_webhook_signature_path',
            'payment_safety',
            'Public webhook signature path',
            'critical',
            detail='Public webhook receive must use handle_raw with verify_signature=True.',
        )
    if 'verify_signature=True' not in source or 'handle_raw' not in source:
        return _check(
            'public_webhook_signature_path',
            'payment_safety',
            'Public webhook signature path',
            'critical',
            detail='Public webhook receive is not explicitly verifying signatures.',
        )
    return _check(
        'public_webhook_signature_path',
        'payment_safety',
        'Public webhook signature path',
        detail='Public webhook receive uses raw body verification for every payload shape.',
    )


def _check_public_webhook_body_limit() -> dict[str, Any]:
    views_module = import_module('apps.payments.api.views')
    security_module = import_module('apps.payments.webhook_security')
    receive_source = inspect.getsource(getattr(views_module.PaymentWebhookViewSet, 'receive'))
    security_source = inspect.getsource(getattr(security_module.PaymentWebhookSecurity, 'validate_body_size'))
    max_body = getattr(settings, 'PAYMENTS_WEBHOOK_MAX_BODY_BYTES', None)
    offenders = []
    try:
        max_body_int = int(max_body)
    except (TypeError, ValueError):
        max_body_int = 0
    if max_body_int <= 0:
        offenders.append('PAYMENTS_WEBHOOK_MAX_BODY_BYTES')
    elif max_body_int > 1024 * 1024:
        offenders.append('PAYMENTS_WEBHOOK_MAX_BODY_BYTES_gt_1mb')
    if 'len(raw_body or b' not in security_source:
        offenders.append('security_missing_raw_body_length_check')
    if 'PaymentWebhookSecurity.validate_body_size(raw_body)' not in receive_source:
        offenders.append('receive_missing_preparse_body_limit')
    if 'payload=request.data' in receive_source:
        limit_pos = receive_source.find('PaymentWebhookSecurity.validate_body_size(raw_body)')
        data_pos = receive_source.find('payload=request.data')
        if data_pos != -1 and (limit_pos == -1 or data_pos < limit_pos):
            offenders.append('request_data_access_before_body_limit')
    if offenders:
        return _check(
            'public_webhook_body_limit',
            'payment_safety',
            'Public webhook body limit',
            'critical',
            detail='Public payment webhook ingestion must cap raw request size before parsing request.data.',
            offenders=offenders,
            max_body_bytes=max_body,
        )
    return _check(
        'public_webhook_body_limit',
        'payment_safety',
        'Public webhook body limit',
        detail='Public payment webhook ingestion caps raw request size before JSON parsing.',
        max_body_bytes=max_body_int,
    )


def _check_webhook_provider_event_id() -> dict[str, Any]:
    models_module = import_module('apps.payments.models')
    services_module = import_module('apps.payments.services')
    event_model = getattr(models_module, 'PaymentWebhookEvent')
    provider_event_field = event_model._meta.get_field('provider_event_id')
    external_event_field = event_model._meta.get_field('external_event_id')
    service_source = inspect.getsource(getattr(services_module, 'PaymentWebhookService'))
    offenders = []
    if not getattr(provider_event_field, 'unique', False):
        offenders.append('provider_event_id_not_unique')
    if getattr(external_event_field, 'unique', False):
        offenders.append('external_event_id_globally_unique')
    if 'provider_event_id=cls._provider_event_id(normalized)' not in service_source:
        offenders.append('service_not_scoped_by_provider_event_id')
    if offenders:
        return _check(
            'webhook_provider_event_id',
            'payment_safety',
            'Webhook provider event idempotency',
            'critical',
            detail='Webhook idempotency must be scoped by provider_event_id, not raw external_event_id alone.',
            offenders=offenders,
        )
    return _check(
        'webhook_provider_event_id',
        'payment_safety',
        'Webhook provider event idempotency',
        detail='Webhook ingestion stores a unique provider_event_id and preserves raw external_event_id per provider.',
    )


def _check_commission_policy_single_source() -> dict[str, Any]:
    policy_module = import_module('apps.payments.commission_policy')
    services_module = import_module('apps.payments.services')
    checkout_module = import_module('apps.orders.checkout_integrity')
    statements_module = import_module('apps.finance_documents.services.statements')
    policy_service = getattr(policy_module, 'CommissionPolicyService', None)
    payment_service_source = inspect.getsource(getattr(services_module, 'PaymentService'))
    checkout_source = inspect.getsource(getattr(checkout_module, '_commission_snapshot'))
    statement_source = inspect.getsource(getattr(statements_module.TrainerStatementService, '_gross_from_net'))
    offenders = []
    if policy_service is None:
        offenders.append('missing_commission_policy_service')
    if 'CommissionPolicyService.split' not in payment_service_source:
        offenders.append('payment_service_direct_commission_math')
    if 'PLATFORM_FEE_RATE' in payment_service_source:
        offenders.append('payment_service_platform_fee_constant')
    if 'CommissionPolicyService.split' not in checkout_source:
        offenders.append('checkout_integrity_direct_commission_math')
    if 'CommissionPolicyService.gross_from_net' not in statement_source:
        offenders.append('statement_direct_gross_from_net_math')
    if offenders:
        return _check(
            'commission_policy_single_source',
            'payment_safety',
            'Commission policy single source',
            'critical',
            detail='Payment, checkout and finance documents must use one commission policy service.',
            offenders=offenders,
        )
    return _check(
        'commission_policy_single_source',
        'payment_safety',
        'Commission policy single source',
        detail='Commission math is centralized in CommissionPolicyService.',
    )


def _check_payment_payout_ownership_source() -> dict[str, Any]:
    services_module = import_module('apps.payments.services')
    source = inspect.getsource(getattr(services_module.PaymentService, '_extract_trainer_id'))
    offenders = []
    if "metadata.get('trainer_id')" in source or 'metadata.get("trainer_id")' in source:
        offenders.append('order_item_metadata_trainer_id')
    if 'SubscriptionPlan' not in source:
        offenders.append('subscription_plan_owner_missing')
    if 'PublishedVideo' not in source or 'trainer_profile.user_id' not in source:
        offenders.append('published_content_owner_missing')
    if offenders:
        return _check(
            'payment_payout_ownership_source',
            'payment_safety',
            'Payment payout ownership source',
            'critical',
            detail='Payment payout recipient must come from subscription/content ownership, not mutable order metadata.',
            offenders=offenders,
        )
    return _check(
        'payment_payout_ownership_source',
        'payment_safety',
        'Payment payout ownership source',
        detail='Payment payout recipient is resolved from subscription/content owner models, not metadata.trainer_id.',
    )


def _check_tenant_scoping_ownership_source() -> dict[str, Any]:
    scoping_module = import_module('apps.tenancy.scoping')
    source = inspect.getsource(scoping_module)
    offenders = []
    for forbidden in (
        'items__metadata__trainer_id',
        'provider_payload__trainer_id',
        'source_order__items__metadata__trainer_id',
        'metadata__trainer_id',
    ):
        if forbidden in source:
            offenders.append(forbidden)
    if 'SubscriptionPlan' not in source or 'PublishedVideo' not in source or '_owned_order_item_filter' not in source:
        offenders.append('owner_model_scope_missing')
    if offenders:
        return _check(
            'tenant_scoping_ownership_source',
            'permissions',
            'Tenant scoping ownership source',
            'critical',
            detail='Tenant scoping must use owner models, not mutable JSON trainer_id fields.',
            offenders=offenders,
        )
    return _check(
        'tenant_scoping_ownership_source',
        'permissions',
        'Tenant scoping ownership source',
        detail='Tenant scoping resolves orders, payments, webhooks and entitlements through owner models.',
    )


def _check_entitlement_valid_source_selection_contract() -> dict[str, Any]:
    entitlements_module = import_module('apps.entitlements.access_audit')
    helper_source = inspect.getsource(getattr(entitlements_module, '_first_source_valid_entitlement'))
    check_source = inspect.getsource(getattr(entitlements_module.AccessControlAuditService, 'check'))
    offenders = []
    if '_validate_source(entitlement' not in helper_source:
        offenders.append('candidate_source_validation_missing')
    if 'return entitlement, source_rules, entitlement, None' not in helper_source:
        offenders.append('valid_candidate_return_missing')
    if '_first_source_valid_entitlement' not in check_source:
        offenders.append('access_check_candidate_selection_missing')
    if '.filter(_active_entitlement_filter(now)).first()' in check_source:
        offenders.append('first_active_entitlement_selection')
    if offenders:
        return _check(
            'entitlement_valid_source_selection_contract',
            'permissions',
            'Entitlement valid source selection contract',
            'critical',
            detail='Runtime access must select an active entitlement with a valid backing source instead of trusting the newest active row.',
            offenders=offenders,
        )
    return _check(
        'entitlement_valid_source_selection_contract',
        'permissions',
        'Entitlement valid source selection contract',
        detail='Runtime access evaluates active entitlement candidates and selects a source-valid grant.',
    )


def _check_support_entitlement_fix_target_contract() -> dict[str, Any]:
    serializers_module = import_module('apps.ops.api.operations_serializers')
    support_module = import_module('apps.ops.support_console')
    serializer_source = inspect.getsource(getattr(serializers_module, 'SupportEntitlementFixSerializer'))
    service_source = inspect.getsource(getattr(support_module, 'fix_entitlement'))
    helper_source = inspect.getsource(getattr(support_module, '_validate_entitlement_target'))
    offenders = []
    if 'EntitlementTargetType.choices' not in serializer_source:
        offenders.append('serializer_target_type_whitelist_missing')
    if 'target_id is required' not in serializer_source:
        offenders.append('serializer_target_id_validation_missing')
    if '_validate_entitlement_target' not in service_source:
        offenders.append('service_target_guard_missing')
    if 'EntitlementTargetType.choices' not in helper_source:
        offenders.append('service_target_type_whitelist_missing')
    if 'target_id is required' not in helper_source:
        offenders.append('service_target_id_required_missing')
    if offenders:
        return _check(
            'support_entitlement_fix_target_contract',
            'permissions',
            'Support entitlement fix target contract',
            'critical',
            detail='Support entitlement fixes must require an allowed target_type and a concrete target_id before granting or revoking by user.',
            offenders=offenders,
        )
    return _check(
        'support_entitlement_fix_target_contract',
        'permissions',
        'Support entitlement fix target contract',
        detail='Support entitlement fixes require whitelisted target types and concrete target ids.',
    )


def _check_support_notification_delivery_scope_contract() -> dict[str, Any]:
    scoping_module = import_module('apps.tenancy.scoping')
    support_module = import_module('apps.ops.support_console')
    scoping_source = inspect.getsource(getattr(scoping_module, 'scope_notification_deliveries_for_user'))
    snapshot_source = inspect.getsource(getattr(support_module, 'get_support_console_snapshot'))
    delivery_source = inspect.getsource(getattr(support_module, '_delivery_for_operator'))
    offenders = []
    for fragment in (
        'scope_orders_for_user',
        'scope_entitlements_for_user',
        'scope_payments_for_user',
        'user_id__in=visible_user_ids',
    ):
        if fragment not in scoping_source:
            offenders.append(f'scope_notification_delivery_missing:{fragment}')
    if 'scope_notification_deliveries_for_user' not in snapshot_source:
        offenders.append('support_snapshot_delivery_scope_missing')
    if 'scope_notification_deliveries_for_user' not in delivery_source:
        offenders.append('support_resend_delivery_scope_missing')
    if offenders:
        return _check(
            'support_notification_delivery_scope_contract',
            'permissions',
            'Support notification delivery scope contract',
            'critical',
            detail='Support notification delivery reads and resend actions must be tenant-scoped through visible commerce/access users.',
            offenders=offenders,
        )
    return _check(
        'support_notification_delivery_scope_contract',
        'permissions',
        'Support notification delivery scope contract',
        detail='Support notification delivery snapshot and resend actions use tenant-aware scoping.',
    )


def _check_side_effect_failure_audit() -> dict[str, Any]:
    entitlements_module = import_module('apps.entitlements.services')
    messaging_module = import_module('apps.messaging.services.conversations')
    payments_module = import_module('apps.payments.services')
    payouts_module = import_module('apps.payouts.services')
    entitlement_audit_granted = inspect.getsource(getattr(entitlements_module.EntitlementService, '_audit_granted'))
    messaging_notify = inspect.getsource(getattr(messaging_module, '_notify_recipient'))
    messaging_emit_event = inspect.getsource(getattr(messaging_module, '_emit_domain_event'))
    payment_safe_notify = inspect.getsource(getattr(payments_module.PaymentService, '_safe_notify'))
    payout_safe_notify = inspect.getsource(getattr(payouts_module.PayoutService, '_safe_notify'))
    offenders = []
    for key, source in (
        ('entitlement_audit_granted', entitlement_audit_granted),
        ('payment_safe_notify', payment_safe_notify),
        ('payout_safe_notify', payout_safe_notify),
    ):
        if 'AuditService.log' not in source or 'side_effect.failed' not in source:
            offenders.append(key)
        if 'except Exception' in source and ('pass' in source or 'return None' in source):
            offenders.append(f'{key}_silent_exception')
    for key, source in (
        ('messaging_notify_recipient', messaging_notify),
        ('messaging_emit_domain_event', messaging_emit_event),
    ):
        if 'logger.exception' not in source:
            offenders.append(f'{key}_missing_error_log')
        if 'except Exception' in source and ('pass' in source or 'return' in source):
            offenders.append(f'{key}_silent_exception')
    if offenders:
        return _check(
            'side_effect_failure_audit',
            'payment_safety',
            'Side effect failure audit',
            'critical',
            detail='Notification side-effect failures must be audited instead of silently swallowed.',
            offenders=offenders,
        )
    return _check(
        'side_effect_failure_audit',
        'payment_safety',
        'Side effect failure audit',
        detail='Payment and payout notification failures create audit events.',
    )


def _check_rbac_role_assignment_source() -> dict[str, Any]:
    permissions_module = import_module('apps.access_control.permissions')
    policies_module = import_module('apps.access_control.policies')
    selectors_module = import_module('apps.access_control.selectors')
    source = inspect.getsource(getattr(permissions_module, 'user_role_set'))
    policy_permission_source = inspect.getsource(getattr(permissions_module.PolicyPermission, 'has_permission'))
    check_feature_source = inspect.getsource(getattr(policies_module.PolicyService, 'check_feature'))
    role_capabilities = getattr(selectors_module, 'ROLE_CAPABILITIES', {})
    trainer_capabilities = set(role_capabilities.get('trainer', []))
    offenders = []
    if 'except Exception' in source:
        offenders.append('broad_exception_in_user_role_set')
    if 'except Exception' in check_feature_source:
        offenders.append('broad_exception_in_policy_check_feature')
    if 'filter(is_active=True)' not in source or 'values_list' not in source:
        offenders.append('missing_active_role_assignment_lookup')
    if "if not roles:" not in source:
        offenders.append('legacy_user_role_not_limited_to_fallback')
    if 'user=request.user' not in policy_permission_source:
        offenders.append('policy_permission_missing_request_user')
    for capability in ('trainer_cms.manage_content', 'media.upload'):
        if capability not in trainer_capabilities:
            offenders.append(f'trainer_missing_capability:{capability}')
    if offenders:
        return _check(
            'rbac_role_assignment_source',
            'permissions',
            'RBAC role assignment source',
            'critical',
            detail='RBAC must use active AccountRoleAssignment and policy capability names must match permission requirements.',
            offenders=offenders,
        )
    return _check(
        'rbac_role_assignment_source',
        'permissions',
        'RBAC role assignment source',
        detail='RBAC reads active role assignments first and uses legacy User.role only as fallback.',
    )


def _check_trainer_runtime_role_source() -> dict[str, Any]:
    common_permissions = inspect.getsource(import_module('common.permissions'))
    assignments_service = inspect.getsource(import_module('apps.assignments.services'))
    customers_views = inspect.getsource(import_module('apps.customers.api.views'))
    messaging_service = inspect.getsource(import_module('apps.messaging.services.conversations'))
    products_views = inspect.getsource(import_module('apps.products.api.views'))
    progress_views = inspect.getsource(import_module('apps.progress.api.views'))
    promotions_views = inspect.getsource(import_module('apps.promotions.api.views'))
    trainer_cms_views = inspect.getsource(import_module('apps.trainer_cms.api.views'))
    videos_views = inspect.getsource(import_module('apps.videos.api.views'))
    video_access = inspect.getsource(import_module('apps.videos.services.issue_access_url'))
    onboarding_flow = inspect.getsource(import_module('apps.trainers.onboarding_flow'))
    offenders = []
    for key, source in (
        ('common_permissions', common_permissions),
        ('assignments_service', assignments_service),
        ('customers_api_views', customers_views),
        ('messaging_service', messaging_service),
        ('products_api_views', products_views),
        ('progress_api_views', progress_views),
        ('promotions_api_views', promotions_views),
        ('trainer_cms_api_views', trainer_cms_views),
        ('videos_api_views', videos_views),
        ('video_access_url_service', video_access),
        ('trainer_onboarding_flow', onboarding_flow),
    ):
        for forbidden in (
            'user.role == "trainer"',
            "user.role == 'trainer'",
            'user.role != "trainer"',
            "user.role != 'trainer'",
            'getattr(user, "role"',
            "getattr(user, 'role'",
            'getattr(request.user, "role"',
            "getattr(request.user, 'role'",
        ):
            if forbidden in source:
                offenders.append(f'{key}_legacy_role_pattern:{forbidden}')
        if 'user_role_set' not in source:
            offenders.append(f'{key}_missing_user_role_set')
    if offenders:
        return _check(
            'trainer_runtime_role_source',
            'permissions',
            'Trainer runtime role source',
            'critical',
            detail='Trainer content runtime access must use active role assignments, not legacy User.role checks.',
            offenders=offenders,
        )
    return _check(
        'trainer_runtime_role_source',
        'permissions',
        'Trainer runtime role source',
        detail='Trainer content runtime access uses user_role_set and active role assignments.',
    )


def _check_assignment_content_ownership_contract() -> dict[str, Any]:
    service_module = import_module('apps.assignments.services')
    module_source = inspect.getsource(service_module)
    create_source = inspect.getsource(getattr(service_module.AssignmentService, 'create_assignment'))
    offenders = []
    if '_validate_assignment_target_ownership' not in module_source:
        offenders.append('ownership_helper_missing')
    if 'TrainerCourseDraft' not in module_source:
        offenders.append('course_lookup_missing')
    if 'TrainerProgramDraft' not in module_source:
        offenders.append('program_lookup_missing')
    if 'str(target.trainer_id) != str(getattr(trainer, "id"' not in module_source:
        offenders.append('generic_target_owner_comparison_missing')
    if '_validate_assignment_target_ownership(' not in create_source:
        offenders.append('create_assignment_missing_ownership_guard')
    if offenders:
        return _check(
            'assignment_content_ownership_contract',
            'privacy_safety',
            'Assignment content ownership contract',
            'critical',
            detail='Trainer assignment creation must verify that the target content belongs to the trainer.',
            offenders=offenders,
        )
    return _check(
        'assignment_content_ownership_contract',
        'privacy_safety',
        'Assignment content ownership contract',
        detail='Trainer assignment creation verifies course/program ownership before creating homework.',
    )


def _check_assignment_write_throttle_contract() -> dict[str, Any]:
    views_module = import_module('apps.assignments.api.views')
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    contracts = [
        ('assignment_submit', getattr(views_module, 'StudentAssignmentViewSet'), 'submit'),
        ('assignment_create', getattr(views_module, 'TrainerAssignmentViewSet'), 'create'),
        ('assignment_review', getattr(views_module, 'TrainerSubmissionViewSet'), 'review'),
    ]
    offenders = []
    for scope, view_class, action_name in contracts:
        if scope not in rates:
            offenders.append(f'{scope}_rate_missing')
        if getattr(view_class, 'throttle_scope', '') != scope:
            offenders.append(f'{scope}_scope_missing')
        source = inspect.getsource(getattr(view_class, 'get_throttles'))
        if f'self.action == "{action_name}"' not in source or 'ScopedRateThrottle()' not in source:
            offenders.append(f'{scope}_action_scoped_throttle_missing')
    if offenders:
        return _check(
            'assignment_write_throttle_contract',
            'http_safety',
            'Assignment write throttle contract',
            'critical',
            detail='Assignment submit/create/review actions must use dedicated scoped throttles without throttling list endpoints as writes.',
            offenders=offenders,
        )
    return _check(
        'assignment_write_throttle_contract',
        'http_safety',
        'Assignment write throttle contract',
        detail='Assignment submit/create/review actions use dedicated scoped throttles.',
        configured_rates={scope: rates.get(scope) for scope, _view, _action in contracts},
    )


def _check_assignment_attachment_validation_contract() -> dict[str, Any]:
    serializers_module = import_module('apps.assignments.api.serializers')
    source = inspect.getsource(serializers_module)
    submit_source = inspect.getsource(getattr(serializers_module.AssignmentSubmitSerializer, 'validate_attachments'))
    required_fragments = {
        'max_attachment_count': 'MAX_SUBMISSION_ATTACHMENTS',
        'allowed_fields': 'ALLOWED_ATTACHMENT_FIELDS',
        'https_url': 'parsed.scheme != "https"',
        'private_host_guard': '_is_private_host',
        'size_limit': 'MAX_ATTACHMENT_SIZE_BYTES',
    }
    offenders = [key for key, fragment in required_fragments.items() if fragment not in source]
    if 'validate_attachments' not in submit_source:
        offenders.append('validate_attachments_missing')
    if offenders:
        return _check(
            'assignment_attachment_validation_contract',
            'storage_safety',
            'Assignment attachment validation contract',
            'critical',
            detail='Assignment submission attachments must restrict fields, count, URL scheme/host and size metadata.',
            offenders=offenders,
        )
    return _check(
        'assignment_attachment_validation_contract',
        'storage_safety',
        'Assignment attachment validation contract',
        detail='Assignment submission attachments validate fields, count, public HTTPS URLs and size metadata.',
    )


def _check_progress_canonical_program_contract() -> dict[str, Any]:
    service_module = import_module('apps.progress.services')
    source = inspect.getsource(getattr(service_module, '_resolve_lesson_context'))
    offenders = []
    forbidden_fragments = (
        'str(program_id or course.id)',
        'str(program_id or program.source_draft_id)',
        "str(program_id or lesson['program_id'])",
    )
    for fragment in forbidden_fragments:
        if fragment in source:
            offenders.append(f'client_program_id_fallback:{fragment}')
    required_fragments = (
        'str(course.id)',
        'str(program.source_draft_id)',
        "str(lesson['program_id'])",
    )
    for fragment in required_fragments:
        if fragment not in source:
            offenders.append(f'canonical_program_id_missing:{fragment}')
    if offenders:
        return _check(
            'progress_canonical_program_contract',
            'privacy_safety',
            'Progress canonical program contract',
            'critical',
            detail='Lesson completion must persist progress under the resolved content program/course id, not a client supplied program_id.',
            offenders=offenders,
        )
    return _check(
        'progress_canonical_program_contract',
        'privacy_safety',
        'Progress canonical program contract',
        detail='Lesson completion persists progress under canonical resolved program/course ids.',
    )


def _check_progress_write_throttle_contract() -> dict[str, Any]:
    views_module = import_module('apps.progress.api.views')
    rates = dict(getattr(settings, 'REST_FRAMEWORK', {}).get('DEFAULT_THROTTLE_RATES', {}) or {})
    contracts = [
        ('progress_video_save', getattr(views_module, 'MyVideoProgressViewSet'), 'save'),
        ('progress_lesson_complete', getattr(views_module, 'MyLessonProgressViewSet'), 'complete'),
    ]
    offenders = []
    for scope, view_class, action_name in contracts:
        if scope not in rates:
            offenders.append(f'{scope}_rate_missing')
        if getattr(view_class, 'throttle_scope', '') != scope:
            offenders.append(f'{scope}_scope_missing')
        throttles_code = getattr(view_class, 'get_throttles').__code__
        if action_name not in throttles_code.co_consts or 'ScopedRateThrottle' not in throttles_code.co_names:
            offenders.append(f'{scope}_action_scoped_throttle_missing')
    if offenders:
        return _check(
            'progress_write_throttle_contract',
            'http_safety',
            'Progress write throttle contract',
            'critical',
            detail='Video progress save and lesson completion actions must use dedicated scoped throttles without throttling progress reads as writes.',
            offenders=offenders,
        )
    return _check(
        'progress_write_throttle_contract',
        'http_safety',
        'Progress write throttle contract',
        detail='Progress write actions use dedicated scoped throttles.',
        configured_rates={scope: rates.get(scope) for scope, _view, _action in contracts},
    )


def _check_progress_student_privacy_contract() -> dict[str, Any]:
    selectors_module = import_module('apps.progress.selectors')
    selector_source = inspect.getsource(getattr(selectors_module, 'get_trainer_student_progress'))
    module_source = inspect.getsource(selectors_module)
    offenders = []
    if '_mask_student_email' not in module_source:
        offenders.append('student_email_mask_missing')
    if '_can_view_student_email' not in module_source:
        offenders.append('student_email_privileged_view_guard_missing')
    if "'student_email_masked'" not in selector_source:
        offenders.append('student_email_masked_flag_missing')
    if "'student_email': getattr(row.user, 'email', '')" in selector_source:
        offenders.append('student_email_direct_exposure')
    if offenders:
        return _check(
            'progress_student_privacy_contract',
            'privacy_safety',
            'Progress student privacy contract',
            'critical',
            detail='Trainer progress reports must not expose full student emails to ordinary trainer accounts.',
            offenders=offenders,
        )
    return _check(
        'progress_student_privacy_contract',
        'privacy_safety',
        'Progress student privacy contract',
        detail='Trainer progress reports mask student emails unless the viewer has privileged staff/admin access.',
    )


def _check_payout_runtime_recipient_integrity() -> dict[str, Any]:
    service_module = import_module('apps.payouts.services')
    source = inspect.getsource(getattr(service_module.PayoutService, '_resolve_trainer_profile'))
    offenders = []
    if 'example.invalid' in source:
        offenders.append('example.invalid')
    if 'get_or_create' in source and 'User' in source:
        offenders.append('synthetic_user_get_or_create')
    if offenders:
        return _check(
            'payout_runtime_recipient_integrity',
            'payout_safety',
            'Payout recipient integrity',
            'critical',
            detail='Payout runtime must not create synthetic trainer users or recipients.',
            forbidden_patterns=offenders,
        )
    return _check(
        'payout_runtime_recipient_integrity',
        'payout_safety',
        'Payout recipient integrity',
        detail='Payout runtime requires an existing trainer profile and does not create synthetic recipients.',
    )


def _check_public_runtime_readiness_disclosure() -> dict[str, Any]:
    runtime_module = import_module('apps.runtime.services')
    source = inspect.getsource(getattr(runtime_module.RuntimeService, 'readiness'))
    offenders = []
    for forbidden in ('postgres', 'redis', 'celery', 'vk cloud', 's3', 'broker configured'):
        if forbidden in source.lower():
            offenders.append(forbidden)
    if offenders:
        return _check(
            'public_runtime_readiness_disclosure',
            'http_safety',
            'Public runtime readiness disclosure',
            'critical',
            detail='Public readiness endpoint must not disclose concrete infrastructure vendors or backend technologies.',
            offenders=offenders,
        )
    return _check(
        'public_runtime_readiness_disclosure',
        'http_safety',
        'Public runtime readiness disclosure',
        detail='Public runtime readiness returns generic component status only.',
    )


def _check_demo_seed_production_guard(*, repo_root: Path) -> dict[str, Any]:
    command_path = repo_root / 'backend' / 'apps' / 'users' / 'management' / 'commands' / 'create_demo_users.py'
    seed_path = repo_root / 'scripts' / 'bootstrap' / 'seed_demo.py'
    backend_seed_path = repo_root / 'backend' / 'scripts' / 'bootstrap' / 'seed_demo.py'
    command_source = command_path.read_text()
    seed_source = seed_path.read_text()
    backend_seed_source = backend_seed_path.read_text()
    offenders = []
    for key, source in (
        ('create_demo_users', command_source),
        ('seed_demo', seed_source),
        ('backend_seed_demo', backend_seed_source),
    ):
        if 'ALLOW_DEMO_SEED' not in source:
            offenders.append(f'{key}_missing_allow_gate')
        if 'IS_PRODUCTION' not in source:
            offenders.append(f'{key}_missing_production_guard')
    if offenders:
        return _check(
            'demo_seed_production_guard',
            'deploy_safety',
            'Demo seed production guard',
            'critical',
            detail='Demo users and seed data with fixed passwords must be blocked in production unless explicitly allowed.',
            offenders=offenders,
        )
    return _check(
        'demo_seed_production_guard',
        'deploy_safety',
        'Demo seed production guard',
        detail='Demo users and seed scripts require ALLOW_DEMO_SEED=1 in production.',
    )


def _check_payment_gateway_public_url_contract() -> dict[str, Any]:
    gateway_module = import_module('apps.payments.gateway')
    adapter = getattr(gateway_module, 'PaymentGatewayAdapter')
    api_source = inspect.getsource(getattr(adapter, '_api_base_url'))
    frontend_source = inspect.getsource(getattr(adapter, '_frontend_base_url'))
    normalize_source = inspect.getsource(getattr(adapter, '_normalize_public_base_url'))
    offenders = []
    if 'ALLOWED_HOSTS' in api_source:
        offenders.append('api_base_from_allowed_hosts')
    if "getattr(settings, 'API_BASE_URL'" not in api_source:
        offenders.append('api_base_setting_missing')
    if "getattr(settings, 'FRONTEND_BASE_URL'" not in frontend_source:
        offenders.append('frontend_base_setting_missing')
    if 'IS_PRODUCTION' not in normalize_source or 'public https:// URL in production' not in normalize_source:
        offenders.append('production_public_https_guard_missing')
    if offenders:
        return _check(
            'payment_gateway_public_urls',
            'payment_safety',
            'Payment gateway public URLs',
            'critical',
            detail='Payment gateway must build return and webhook URLs from explicit public HTTPS base URLs.',
            offenders=offenders,
        )
    return _check(
        'payment_gateway_public_urls',
        'payment_safety',
        'Payment gateway public URLs',
        detail='Payment gateway return and webhook URLs use explicit public base URL settings with production HTTPS guards.',
    )


def _check_production_gate_https_origin_defaults(*, repo_root: Path) -> dict[str, Any]:
    script_path = repo_root / 'scripts' / 'ci' / 'production_gate.sh'
    source = script_path.read_text()
    offenders = []
    for forbidden in ('http://localhost', 'http://127.0.0.1', 'http://trainerhub.local'):
        if forbidden in source:
            offenders.append(forbidden)
    if 'APP_ENV="${APP_ENV:-production}"' not in source:
        offenders.append('app_env_production_default_missing')
    if 'API_BASE_URL="${API_BASE_URL:-https://api.trainerhub.local}"' not in source:
        offenders.append('api_https_default_missing')
    if 'FRONTEND_BASE_URL="${FRONTEND_BASE_URL:-https://trainerhub.local}"' not in source:
        offenders.append('frontend_https_default_missing')
    if 'CSRF_TRUSTED_ORIGINS="${CSRF_TRUSTED_ORIGINS:-https://trainerhub.local}"' not in source:
        offenders.append('csrf_https_default_missing')
    if 'CORS_ALLOWED_ORIGINS="${CORS_ALLOWED_ORIGINS:-https://trainerhub.local}"' not in source:
        offenders.append('cors_https_default_missing')
    if offenders:
        return _check(
            'production_gate_https_origin_defaults',
            'deploy_safety',
            'Production gate HTTPS origin defaults',
            'critical',
            detail='Production gate must not default to local HTTP CORS/CSRF origins.',
            offenders=offenders,
        )
    return _check(
        'production_gate_https_origin_defaults',
        'deploy_safety',
        'Production gate HTTPS origin defaults',
        detail='Production gate defaults CORS/CSRF origins to HTTPS-only values.',
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
    checks.append(_check_auth_logout_throttle())
    checks.append(_check_public_ingest_throttles())
    checks.append(_check_admin_ops_throttle())
    checks.append(_check_production_cache_backend())
    checks.append(_check_celery_production_config())
    checks.append(_check_error_tracking_production_config(repo_root=repo_root))
    checks.append(_check_media_storage_production_config())
    checks.append(_check_media_upload_validation_contract())
    checks.append(_check_media_upload_permission_contract())
    checks.append(_check_media_upload_verification_contract())
    checks.append(_check_media_read_ttl_contract())
    checks.append(_check_csv_export_safety_contract(repo_root=repo_root))
    checks.append(_check_backup_restore_contract(repo_root=repo_root))
    checks.append(_check_production_database_backend())
    checks.append(_check_production_origin_security())
    checks.append(_check_runtime_apps_namespace(repo_root=repo_root))
    checks.append(_check_django_settings_layout(repo_root=repo_root))
    checks.append(_check_backend_migration_release_job(repo_root=repo_root))
    checks.append(_check_celery_worker_queue_coverage(repo_root=repo_root))
    checks.append(_check_outbox_compose_overlay_runtime(repo_root=repo_root))
    checks.append(_check_deploy_scripts_preflight(repo_root=repo_root))
    checks.append(_check_deploy_image_tag_contract(repo_root=repo_root))
    checks.append(_check_docker_build_context_hygiene(repo_root=repo_root))
    checks.append(_check_frontend_standalone_runtime(repo_root=repo_root))
    checks.append(_check_nginx_edge_proxy_contract(repo_root=repo_root))
    checks.append(_check_cookie_only_auth_contract())
    checks.append(_check_default_api_permissions())
    checks.append(_check_audit_context_redaction())
    checks.append(_check_public_review_disclosure_contract())
    checks.append(_check_review_self_moderation_contract())
    checks.append(_check_review_write_throttle_contract())
    checks.append(_check_review_reply_state_contract())
    checks.append(_check_public_store_identity_contract())
    checks.append(_check_messaging_participant_privacy_contract())
    checks.append(_check_messaging_write_throttle_contract())
    checks.append(_check_provider_return_read_only())
    checks.append(_check_public_webhook_signature_path())
    checks.append(_check_public_webhook_body_limit())
    checks.append(_check_webhook_provider_event_id())
    checks.append(_check_payment_gateway_public_url_contract())
    checks.append(_check_commission_policy_single_source())
    checks.append(_check_payment_payout_ownership_source())
    checks.append(_check_side_effect_failure_audit())
    checks.append(_check_rbac_role_assignment_source())
    checks.append(_check_trainer_runtime_role_source())
    checks.append(_check_assignment_content_ownership_contract())
    checks.append(_check_assignment_write_throttle_contract())
    checks.append(_check_assignment_attachment_validation_contract())
    checks.append(_check_progress_canonical_program_contract())
    checks.append(_check_progress_write_throttle_contract())
    checks.append(_check_progress_student_privacy_contract())
    checks.append(_check_tenant_scoping_ownership_source())
    checks.append(_check_entitlement_valid_source_selection_contract())
    checks.append(_check_support_entitlement_fix_target_contract())
    checks.append(_check_support_notification_delivery_scope_contract())
    checks.append(_check_payout_runtime_recipient_integrity())
    checks.append(_check_public_runtime_readiness_disclosure())
    checks.append(_check_demo_seed_production_guard(repo_root=repo_root))
    checks.append(_check_production_gate_https_origin_defaults(repo_root=repo_root))

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
            {
                'key': 'migrate',
                'command': 'bash scripts/deploy/migrate.sh',
                'description': 'Apply database schema through the release job before seed/smoke checks.',
            },
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
