from django.utils import timezone
from rest_framework import serializers

from orders.models import Order
from orders.utils import change_date_format
from tasks.models import Task
from tasks.serializers import BaseTaskSerializer
from users.models import Team


class OrderSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.id")
    accepted = serializers.ReadOnlyField()
    team = serializers.ReadOnlyField(source="team.id", default=None)
    tasks = serializers.SerializerMethodField()
    createdAt = serializers.ReadOnlyField(source="created_at")
    updatedAt = serializers.ReadOnlyField(source="updated_at")
    acceptedAt = serializers.ReadOnlyField(source="accepted_at")

    class Meta:
        model = Order
        fields = [
            "id",
            "owner",
            "name",
            "description",
            "deadline",
            "createdAt",
            "updatedAt",
            "acceptedAt",
            "accepted",
            "team",
            "tasks",
            "status",
        ]

    def get_tasks(self, obj):
        tasks = Task.objects.filter(order=obj)
        return BaseTaskSerializer(tasks, many=True).data

    def validate(self, attrs):
        self._validate_name(attrs.get("name"))
        self._validate_description(attrs.get("description"))
        return attrs

    def _validate_name(self, name):
        if name is not None and len(name) < 5:
            raise serializers.ValidationError({"name": "Name must be at least 5 characters long."})

    def _validate_description(self, description):
        if description is None:
            return
        if len(description) < 100:
            raise serializers.ValidationError({"description": "Description must be at least 100 characters long."})
        if len(description) > 3000:
            raise serializers.ValidationError({"description": "Description must not exceed 3000 characters."})


class CreateOrderSerializer(OrderSerializer):

    def create(self, validated_data):
        user = self.context["request"].user.id
        order = Order.objects.create(
            owner_id=user,
            name=validated_data["name"],
            description=validated_data["description"],
            deadline=validated_data["deadline"],
        )
        order.save()
        return order


class UpdateOrderSerializer(OrderSerializer):
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    deadline = serializers.DateField(required=False)

    def update(self, instance: Order, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.deadline = validated_data.get("deadline", instance.deadline)
        instance.updated_at = timezone.now()
        instance.save()

        return instance

    def to_representation(self, instance: Order):
        updated_at = change_date_format(instance.updated_at)

        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "deadline": instance.deadline,
            "updatedAt": updated_at,
            "status": instance.status,
        }


class UnacceptedOrderSerializer(OrderSerializer):
    def to_representation(self, instance: Order):
        created_at = change_date_format(instance.created_at)

        return {
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "deadline": instance.deadline,
            "createdAt": created_at,
            "status": instance.status,
        }


class AcceptOrderSerializer(serializers.ModelSerializer):
    accepted = serializers.BooleanField()
    team = serializers.IntegerField(source="team.id")
    status = serializers.CharField(required=True)

    class Meta:
        model = Order
        fields = ["accepted", "team", "status"]

    def validate(self, attrs):
        status = attrs["status"]
        if "team" in attrs:
            attrs["team_instance"] = self._get_team(attrs)

        if status == "active" and attrs["team_instance"].status == "unavailable":
            raise serializers.ValidationError({"message": "This team is currently unavailable."})

        return attrs

    def update(self, instance: Order, validated_data):
        order_status = validated_data.get("status", instance.status)
        is_accepted = validated_data.get("accepted", False)
        team_instance = validated_data.get("team_instance", instance.team)

        if is_accepted and order_status == "active":
            return self._accept_order(instance, team_instance, order_status)

        if order_status == "closed" and team_instance is not None:
            self._close_order(instance, team_instance, order_status)

        instance.status = order_status
        instance.save()
        return instance

    def to_representation(self, instance: Order):
        accepted_at = change_date_format(instance.accepted_at)

        return {
            "id": instance.id,
            "name": instance.name,
            "accepted": instance.accepted,
            "acceptedAt": accepted_at,
            "team": instance.team_id,
            "status": instance.status,
        }

    def _get_team(self, attrs: dict):
        try:
            team = attrs["team"]
            team_instance = Team.objects.get(id=team["id"])
            return team_instance
        except Team.DoesNotExist:
            raise serializers.ValidationError({"error": "Team with this Id does not exist."})

    def _accept_order(self, instance: Order, team_instance, order_status):
        instance.accepted = True
        instance.accepted_at = timezone.now()
        instance.team = team_instance
        instance.status = order_status
        team_instance.status = "unavailable"

        instance.save()
        team_instance.save()

        return instance

    def _close_order(self, instance: Order, team_instance, order_status):
        instance.status = order_status
        team_instance.status = "available"

        instance.save()
        team_instance.save()

        return instance
