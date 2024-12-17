from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from rest_framework.viewsets import GenericViewSet

from core import permissions as custom_perm
from tasks import serializers
from tasks.models import Task
from tasks.paginations import TasksPagination


class GetTeamTasksView(generics.ListAPIView, GenericViewSet):
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = serializers.BaseTaskSerializer
    pagination_class = TasksPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "executor"]

    def get_queryset(self):
        user = self.request.user
        order_id = self.request.data.get("orderId", None)
        team_id = self.request.data.get("teamId", None)
        queryset = Task.objects.filter(
            Q(team__leader=user) | Q(team__list_of_members=user) | Q(order_id=order_id) | Q(team_id=team_id)
        ).distinct()

        return queryset


class CreateTaskView(generics.CreateAPIView, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = serializers.CreateTaskSerializer


class UpdateTaskView(generics.UpdateAPIView, GenericViewSet):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = serializers.EditTaskSerializer
