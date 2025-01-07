from django.db.models import Q
from django.http import response as dj_res
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, status, permissions
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core import permissions as custom_perm
from tasks import serializers as task_serializers
from tasks.mixins import TaskLoggerMixin
from tasks.models import Task
from tasks.paginations import TasksPagination


class GetTeamTasksView(generics.ListAPIView, GenericViewSet, TaskLoggerMixin):
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = task_serializers.BaseTaskSerializer
    pagination_class = TasksPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "executor"]

    def get_queryset(self):
        user = self.request.user
        order_id = self.request.data.get("orderId", None)
        team_id = self.request.data.get("teamId", None)
        status_filter = self.request.query_params.get("status", None)

        queryset = Task.objects.filter(
            Q(team__leader=user) | Q(team__list_of_members=user) | Q(order_id=order_id) | Q(team_id=team_id)
        ).distinct()

        if not status_filter:
            queryset = queryset.filter(status="active").order_by("-deadline")

        return queryset

    def list(self, request, *args, **kwargs):
        self.log_attempt_retrieve_tasks(request.user)

        try:
            response = super().list(request, *args, **kwargs)
            self.log_successfully_retrieve(request.user, response.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_retrieve_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while retrieving tasks."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CreateTaskView(generics.CreateAPIView, GenericViewSet, TaskLoggerMixin):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = task_serializers.CreateTaskSerializer

    def create(self, request, *args, **kwargs):
        self.log_attempt_create(request.user)

        try:
            response = super().create(request, *args, **kwargs)
            self.log_successfully_created(request.user, request.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except Exception as e:
            self.log_creation_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while creating the task."}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UpdateTaskView(generics.UpdateAPIView, GenericViewSet, TaskLoggerMixin):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = task_serializers.EditTaskSerializer

    def update(self, request, *args, **kwargs):
        self.log_attempt_update(request.user)

        try:
            response = super().update(request, *args, **kwargs)
            self.log_successfully_updated(request.user, response.data)
            return response

        except (serializers.ValidationError, dj_res.Http404) as e:
            self.log_validation_error(e)
            raise

        except Exception as e:
            self.log_updating_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while updating the task"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteTaskView(generics.DestroyAPIView, GenericViewSet, TaskLoggerMixin):
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin, permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        self.log_attempt_delete(request.user)

        try:
            response = super().delete(request, *args, **kwargs)
            self.log_successfully_deleted(request.user)
            return response

        except Exception as e:
            self.log_deleting_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while deleting the task"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
