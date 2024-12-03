from rest_framework import generics, permissions
from rest_framework.viewsets import GenericViewSet

from users import serializers
from users.models import CustomUser


class RegistrationView(generics.CreateAPIView, GenericViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.RegistrationSerializer
