from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import UserSerializer, RegisterSerializer

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register/
    Public endpoint — no JWT required.
    """
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class ProfileView(generics.RetrieveUpdateAPIView):
    """
    GET  /api/auth/profile/   → return logged-in user's profile
    PUT  /api/auth/profile/   → update logged-in user's profile
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        # Always returns the currently logged-in user
        # The client never passes a user ID — it's taken from the JWT
        return self.request.user