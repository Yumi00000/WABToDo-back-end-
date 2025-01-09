from django.db.models import Q
from django.http import response as dj_res
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters, status
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from core import permissions as custom_perm
from tasks import serializers as task_serializers
from tasks.mixins import TaskLoggerMixin
from tasks.models import Task
from tasks.paginations import TasksPagination


class GetTeamTasksView(generics.ListAPIView, GenericViewSet, TaskLoggerMixin):
    """
    Handles the retrieval of team tasks with filtering and custom logging mechanisms.

    This class-based view enables team members or administrators to fetch a list of tasks
    associated with a specified team or order. It extends Django's `ListAPIView` and integrates
    with a custom logging mixin for logging task retrieval events. Filtering options and
    search capabilities are provided for a tailored task view.

    Attributes
    ----------
    permission_classes : list
        Specifies the permissions necessary to access this view. Only team members or
        administrators are allowed.
    serializer_class : type
        The serializer class used for serializing task data.
    pagination_class : type
        The pagination class applied to responses for paginated task lists.
    filter_backends : list
        Backend filters used for advanced task filtering and searching functionality.
    filterset_fields : list
        Specific fields available for task filtering by clients.

    Methods
    -------
    get_queryset()
        Retrieves the task queryset for the requesting user with applied filters based
        on request data and query parameters.
    list(request, *args, **kwargs)
        Handles the GET request to retrieve and return a list of tasks, incorporating
        logging for task retrieval attempts, successes, and errors.
    """
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
    """
    CreateTaskView handles the creation of new task objects.

    This class extends `generics.CreateAPIView` for handling HTTP POST requests to create
    a new task. It integrates with `GenericViewSet` for viewset functionalities in Django
    REST Framework and utilizes the `TaskLoggerMixin` to log task creation events for
    monitoring and debugging. The class ensures permissions are checked, validated data
    is serialized, and tasks are created securely.

    Attributes
    ----------
    queryset : QuerySet
        A queryset representing all tasks in the system.
    permission_classes : list
        A list of permission classes that restrict access to team members or administrators.
    serializer_class : Type[Serializer]
        A serializer class used for validating and serializing task data.

    Methods
    -------
    create(request, *args, **kwargs)
        Handles task creation while logging events and exceptions along the process.
    """
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
    """
    Handles the update functionality for a task.

    This class extends the `generics.UpdateAPIView` and `GenericViewSet` to manage the updating
    of tasks in the system. It also incorporates logging functionality provided by `TaskLoggerMixin`
    to track update attempts, successful updates, and errors during the update process. The class
    uses a custom serializer to validate the task data and custom permissions to ensure that only
    authorized users can update tasks.

    Attributes:
    queryset: Contains the set of Task instances available for updating.
    permission_classes: Specifies the permission rules that restrict access to authorized users.
    serializer_class: Defines the serializer used to validate and serialize data for editing tasks.

    Methods:
    update(self, request, *args, **kwargs): Handles the update logic for a task. Implements logging
                                             and error handling functionality alongside parent
                                             class's update logic.

    """
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]
    serializer_class = task_serializers.EditTaskSerializer

    def update(self, request, *args, **kwargs):
        self.log_attempt_update(request.user)

        try:
            response = super().update(request, *args, **kwargs)
            self.log_successfully_updated(request.user, response.data)
            return response

        except serializers.ValidationError as e:
            self.log_validation_error(e.detail)
            raise

        except dj_res.Http404:
            self.log_validation_error("Task not found")
            raise

        except Exception as e:
            self.log_updating_error(request.user, str(e))
            response_error_message = {"error": "An error occurred while updating the task"}
            return Response(response_error_message, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteTaskView(generics.DestroyAPIView, GenericViewSet, TaskLoggerMixin):
    """
    Provides functionality for deleting a task.

    This class allows deletion of a task while logging the attempt, success,
    or any errors encountered during the deletion process. It uses permissions
    to restrict access and ensures proper error handling and logging behavior.

    Attributes:
        queryset: The queryset that defines which tasks are eligible for
                  deletion.
        permission_classes: List of permission classes applied to restrict
                            access for task deletion.
    """
    queryset = Task.objects.all()
    permission_classes = [custom_perm.IsTeamMemberOrAdmin]

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
