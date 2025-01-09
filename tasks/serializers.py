from datetime import date

from django.db.models import Q
from rest_framework import serializers

from orders.models import Order
from tasks.models import Task, TaskStatus
from users.models import Team, CustomUser


class BaseTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for Task model.

    This class is responsible for serializing and validating Task model
    objects for API operations. It includes methods for validating various
    fields, retrieving related objects, and customizing serialized
    representations. The purpose of this serializer is to ensure that all
    data operations on the Task model are consistent with the business
    logic and data integrity requirements.

    Attributes:
        id (serializers.IntegerField): Read-only field representing the
        Task ID.
        team (serializers.IntegerField): Read-only field representing the
        Team ID associated with the task.
        order (serializers.IntegerField): Read-only field representing the
        Order ID associated with the task.
        status (serializers.CharField): Read-only field representing the
        status of the task.

    Methods:
        validate(attrs: dict) -> dict:
            Validates the given attributes dictionary against business
            requirements. Performs various validations on title,
            description, deadline, and status. Also retrieves and validates
            `team` and `order` values based on the input data.
        _validate_len_title(attrs: dict) -> None:
            Validates the length of the input title field. Ensures it is
            between 5 and 255 characters.
        _validate_len_description(attrs: dict) -> None:
            Validates the length of the input description field. Ensures it
            is between 10 and 5000 characters.
        _get_team_and_order(attrs: dict) -> list | None:
            Retrieves `team` and `order` based on the executor's details.
            Returns a list containing the team ID and order ID.
        _validate_deadline(attrs: dict) -> None:
            Ensures the deadline date, if present, is not earlier than
            today.
        _validate_status(attrs: dict) -> None:
            Validates that the provided status is one of the allowed
            statuses (PENDING, ACTIVE, or CLOSED).
        _get_user_team(user):
            Retrieves the user's team based on membership or leadership.
            Raises validation errors if no team is found.
        _get_team_order(team) -> int | None:
            Retrieves the active order associated with the team. Raises
            validation errors if no order exists or if the team's order is
            invalid.
        to_representation(instance: Task) -> dict:
            Converts a Task instance into a dictionary format for API
            response.
    """
    id = serializers.IntegerField(read_only=True)
    team = serializers.IntegerField(read_only=True)
    order = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "description", "executor", "team", "order", "status", "deadline"]

    def validate(self, attrs: dict) -> dict:
        self._validate_len_title(attrs)
        self._validate_len_description(attrs)
        attrs["team"], attrs["order"] = self._get_team_and_order(attrs)
        self._validate_deadline(attrs)
        if "status" in attrs:
            self._validate_status(attrs)

        return attrs

    def _validate_len_title(self, attrs: dict) -> None:
        if len(attrs["title"]) < 5:
            raise serializers.ValidationError({"title": "Title must be at least 5 characters"})
        if len(attrs["title"]) > 255:
            raise serializers.ValidationError({"title": "Title cannot be more than 255 characters"})

    def _validate_len_description(self, attrs: dict) -> None:
        if len(attrs["description"]) < 10:
            raise serializers.ValidationError({"description": "Description must be at least 10 characters"})
        if len(attrs["description"]) > 5000:
            raise serializers.ValidationError({"description": "Description cannot be more than 500 characters"})

    def _get_team_and_order(self, attrs: dict) -> list | None:
        executor = attrs["executor"]
        team_id = self._get_user_team(executor)
        order_id = self._get_team_order(team_id)
        validate = [team_id, order_id]
        return validate

    def _validate_deadline(self, attrs: dict) -> None:
        deadline = attrs["deadline"]
        if deadline and deadline < date.today():
            raise serializers.ValidationError()

    def _validate_status(self, attrs: dict) -> None:
        status = attrs["status"]
        statuses = [TaskStatus.PENDING.value, TaskStatus.ACTIVE.value, TaskStatus.CLOSED.value]
        if status not in statuses:
            raise serializers.ValidationError({"status": f"Available statuses: {statuses}"})

    def _get_user_team(self, user):
        user_team = Team.objects.filter(Q(list_of_members=user) | Q(leader=user)).distinct()

        if not user_team.exists():
            raise serializers.ValidationError({"executor": "User is not a member or leader of any team."})

        return user_team.first()

    def _get_team_order(self, team) -> int | None:
        try:
            order = Order.objects.get(team=team, status="active")
        except Order.DoesNotExist:
            raise serializers.ValidationError({"order": f"The order is not a project for a team with ID {team}"})

        return order

    def to_representation(self, instance: Task) -> dict:
        return {
            "id": instance.id,
            "title": instance.title,
            "description": instance.description,
            "executor": instance.executor.id,
            "team": instance.team.id,
            "order": instance.order.id,
            "status": instance.status,
            "deadline": instance.deadline,
        }


class CreateTaskSerializer(BaseTaskSerializer):
    """
    Serializer class for creating a new task.

    This class is responsible for handling the creation of new Task objects. It extends
    the functionality of BaseTaskSerializer and uses validated input data to construct
    and save a Task instance.

    Attributes
    ----------
    None

    Methods
    -------
    create(validated_data: BaseTaskSerializer) -> Task
        Creates and returns a new Task instance based on the validated input data.

    """
    def create(self, validated_data: BaseTaskSerializer) -> Task:
        task = Task.objects.create(
            title=validated_data["title"],
            description=validated_data["description"],
            executor=validated_data["executor"],
            team=validated_data["team"],
            order=validated_data["order"],
            deadline=validated_data["deadline"],
        )

        return task


class EditTaskSerializer(BaseTaskSerializer):
    """
    Serializer class that modifies existing task instances.

    This class is responsible for serializing and deserializing data related to
    tasks. It allows partial updates to task instances by validating and applying
    changes to provided fields such as title, description, executor, deadline, and
    status. The class includes custom validation logic and handles updates to the
    task model's attributes while ensuring data integrity.

    Attributes
    ----------
    title: str
        The title of the task (optional).
    description: str
        The detailed description of the task (optional).
    executor: str
        The identifier for the executor of the task (optional).
    deadline: date
        The deadline for completing the task (optional).
    status: str
        The current status of the task (optional).

    Methods
    -------
    validate(attrs: dict) -> dict
        Validates the provided attributes for the task. Ensures fields such as
        title, description, executor, deadline, and status meet specific
        requirements.

    update(instance: Task, validated_data: dict) -> Task
        Updates a given task instance with validated data. Modifies the relevant
        fields based on provided input, applies changes to the database, and returns
        the updated task instance.

    Raises
    ------
    ValidationError
        Raised by internal methods during validation if a field does not meet the
        required criteria.
    """
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    executor = serializers.CharField(required=False)
    deadline = serializers.DateField(required=False)
    status = serializers.CharField(required=False)

    def validate(self, attrs: dict) -> dict:
        if "title" in attrs:
            self._validate_len_title(attrs)
        if "description" in attrs:
            self._validate_len_description(attrs)
        if "executor" in attrs:
            attrs["team"], attrs["order"] = self._get_team_and_order(attrs)
        if "deadline" in attrs:
            self._validate_deadline(attrs)
        if "status" in attrs:
            self._validate_status(attrs)

        return attrs

    def update(self, instance: Task, validated_data: dict) -> Task:
        if "executor" in validated_data:
            user = CustomUser.objects.get(id=validated_data["executor"])
            instance.executor = user

        instance.title = validated_data.get("title", instance.title)
        instance.description = validated_data.get("description", instance.description)
        instance.deadline = validated_data.get("deadline", instance.deadline)
        instance.status = validated_data.get("status", instance.status)

        instance.save()
        return instance
