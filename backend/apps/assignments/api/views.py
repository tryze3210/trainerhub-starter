from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.assignments.api.serializers import (
    AssignmentCreateSerializer,
    AssignmentReviewSerializer,
    AssignmentSubmitSerializer,
)
from apps.assignments.models import Assignment, AssignmentSubmission
from apps.assignments.selectors import (
    assignment_payload,
    list_student_assignments,
    list_trainer_assignments,
    list_trainer_submissions,
)
from apps.assignments.services import AssignmentService


def _error_response(exc: Exception):
    status_code = status.HTTP_400_BAD_REQUEST
    if isinstance(exc, PermissionDenied):
        status_code = status.HTTP_403_FORBIDDEN
    detail = getattr(exc, "message", None) or getattr(exc, "messages", None) or str(exc)
    return Response({"detail": detail}, status=status_code)


class StudentAssignmentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(list_student_assignments(user=request.user))

    @action(detail=True, methods=["post"], url_path="submit")
    def submit(self, request, pk=None):
        assignment = get_object_or_404(Assignment.objects.select_related("trainer"), pk=pk)
        serializer = AssignmentSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submission = AssignmentService.submit_assignment(
                student=request.user,
                assignment=assignment,
                data=serializer.validated_data,
            )
        except (PermissionDenied, ValidationError) as exc:
            return _error_response(exc)
        return Response(
            assignment_payload(assignment=assignment, submission=submission),
            status=status.HTTP_200_OK,
        )


class TrainerAssignmentViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(list_trainer_assignments(trainer=request.user))

    def create(self, request):
        serializer = AssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            assignment = AssignmentService.create_assignment(trainer=request.user, data=serializer.validated_data)
        except (PermissionDenied, ValidationError) as exc:
            return _error_response(exc)
        return Response(assignment_payload(assignment=assignment), status=status.HTTP_201_CREATED)


class TrainerSubmissionViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request):
        return Response(list_trainer_submissions(trainer=request.user))

    @action(detail=True, methods=["post"], url_path="review")
    def review(self, request, pk=None):
        submission = get_object_or_404(
            AssignmentSubmission.objects.select_related("assignment", "student", "reviewed_by"),
            pk=pk,
        )
        serializer = AssignmentReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            reviewed = AssignmentService.review_submission(
                trainer=request.user,
                submission=submission,
                data=serializer.validated_data,
            )
        except (PermissionDenied, ValidationError) as exc:
            return _error_response(exc)
        return Response(assignment_payload(assignment=reviewed.assignment, submission=reviewed))
