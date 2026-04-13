from rest_framework import generics
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .serializers import RegisterSerializer, EmailTokenObtainPairSerializer


class RegisterApi(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class LoginApi(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class RefreshApi(TokenRefreshView):
    pass
