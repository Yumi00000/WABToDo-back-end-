from rest_framework import serializers

from orders.models import Order
from tasks.models import Task
from tasks.serializers import TaskSerializer


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
        ]

    def get_tasks(self, obj):
        tasks = Task.objects.filter(order=obj)
        return TaskSerializer(tasks, many=True).data

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
