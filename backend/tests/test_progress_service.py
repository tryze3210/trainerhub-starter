from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.entitlements.models import Entitlement
from apps.entitlements.services import EntitlementService
from apps.progress.services import ProgressService


class ProgressServiceTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username='progress-user')
        EntitlementService.grant(
            user=self.user,
            kind=Entitlement.Kind.VIDEO,
            object_id='vid-101',
            source=Entitlement.Source.ADMIN_GRANT,
            source_reference='test-video',
            starts_at=timezone.now(),
        )
        EntitlementService.grant(
            user=self.user,
            kind=Entitlement.Kind.PROGRAM,
            object_id='prog-201',
            source=Entitlement.Source.ADMIN_GRANT,
            source_reference='test-program',
            starts_at=timezone.now(),
        )

    def test_save_video_progress_marks_completion(self):
        record = ProgressService.save_video_progress(user=self.user, video_id='vid-101', watched_seconds=1700, last_position_seconds=1700)
        self.assertTrue(record.is_completed)

    def test_mark_lesson_completed_updates_program_progress(self):
        ProgressService.mark_lesson_completed(user=self.user, lesson_id='lesson-301')
        program_progress = self.user.program_progress_records.get(program_id='prog-201')
        self.assertEqual(program_progress.completed_lessons, 1)
