from rest_framework import generics
from rest_framework.viewsets import GenericViewSet

from tasks import serializers
from tasks.models import Task
from core import permissions as custom_perm


class GetTeamTasksView(generics.ListAPIView, GenericViewSet): ...


class CreateTaskView(generics.CreateAPIView, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrLeader]
    serializer_class = serializers.CreateTaskSerializer


class UpdateTaskView(generics.UpdateAPIView, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrLeader]
    serializer_class = serializers.EditTaskSerializer
