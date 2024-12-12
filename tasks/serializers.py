from datetime import date

from django.db.models import Q
from rest_framework import serializers

from orders.models import Order
from tasks.models import Task
from users.models import Team


class BaseTaskSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    team = serializers.IntegerField(read_only=True)
    order = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Task
        fields = ["id", "title", "description", "executor", "team", "order", "status", "deadline"]

    def validate(self, attrs: dict) -> dict:
        self._validate_len_title_and_description(attrs)
        attrs["team"], attrs["order"] = self._get_team_and_order(attrs)
        self._validate_deadline(attrs)

        return attrs

    def _validate_len_title_and_description(self, attrs: dict) -> None:
        if len(attrs["title"]) < 5:
            raise serializers.ValidationError({"title": "Title must be at least 5 characters"})
        if len(attrs["title"]) > 255:
            raise serializers.ValidationError({"title": "Title cannot be more than 255 characters"})
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
