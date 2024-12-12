from rest_framework import generics, permissions
from rest_framework.viewsets import GenericViewSet

from tasks import serializers
from tasks.models import Task


class CreateTaskView(generics.CreateAPIView, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.CreateTaskSerializer
