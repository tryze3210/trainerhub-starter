from rest_framework import generics, permissions
from django.contrib.auth import get_user_model
from .serializers import UserMeSerializer

User = get_user_model()

class MeApi(generics.RetrieveUpdateAPIView):
    serializer_class = UserMeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
