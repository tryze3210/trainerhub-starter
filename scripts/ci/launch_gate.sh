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
    tests/test_messaging_core_v104.py
)

(
  cd frontend
  npm run typecheck
  npm run build
)
