from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.onboarding import services
from apps.onboarding.api.serializers import CompleteStepSerializer, OnboardingStatusSerializer, OnboardingStepSerializer


class OnboardingStepsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(OnboardingStepSerializer(services.list_steps(user=request.user), many=True).data)


class OnboardingCompleteStepView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CompleteStepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = services.complete_step(
            user=request.user,
            code=serializer.validated_data['step_code'],
            payload=serializer.validated_data.get('payload'),
        )
        return Response(payload)


class OnboardingStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(OnboardingStatusSerializer(services.get_status(user=request.user)).data)
