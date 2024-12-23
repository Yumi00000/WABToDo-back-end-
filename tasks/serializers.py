from datetime import date

from django.db.models import Q
from rest_framework import serializers

from orders.models import Order
from tasks.models import Task, TaskStatus
from users.models import Team, CustomUser


class BaseTaskSerializer(serializers.ModelSerializer):
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
