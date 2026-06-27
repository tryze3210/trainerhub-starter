#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."

python -m compileall backend

(
  cd backend
  python manage.py check
  python manage.py makemigrations --check --dry-run
  python manage.py check_production_readiness --json --fail-on-degraded
  pytest \
    tests/test_notifications_v91_domain_triggers.py \
    tests/test_customer_crm_v92.py \
    tests/test_booking_v93_schedule_waitlist.py \
    tests/test_booking_v94_attendance_checkin.py \
    tests/test_production_readiness_v95.py \
    tests/test_course_program_builder_v97.py \
    tests/test_content_access_runtime_v98.py \
    tests/test_video_delivery_hardening_v99.py \
    tests/test_student_learning_area_v100.py \
    tests/test_progress_tracking_v101.py \
    tests/test_assignments_homework_v102.py \
    tests/test_reviews_feedback_loop_v103.py \
    tests/test_messaging_core_v104.py \
    tests/test_role_matrix_permissions_v107.py \
    tests/test_tenant_isolation_v108.py \
    tests/test_admin_global_search_v109.py \
    tests/test_support_console_v110.py \
    tests/test_disputes_chargebacks_v111.py \
    tests/test_finance_documents_v112.py \
    tests/test_legal_compliance_v113.py \
    tests/test_observability_runtime_v114.py \
    tests/test_ops_runbooks_v115.py \
    tests/test_ci_cd_production_gate_v116.py \
    tests/test_demo_seed_scenarios_v117.py \
    tests/test_public_marketplace_hardening_v118.py \
    tests/test_launch_candidate_v119.py \
    tests/test_production_launch_pack_v120.py
)

(
  cd frontend
  npm run typecheck
  npm run build
)
