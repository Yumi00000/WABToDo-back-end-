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
    id = serializers.IntegerField(required=True, write_only=True)
    name = serializers.CharField()
    description = serializers.CharField()
    deadline = serializers.DateField()
