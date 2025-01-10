import logging
from datetime import timedelta

from django.utils import timezone
from django.utils.timezone import now
from rest_framework import serializers

from core.tasks import on_delete_time_item
from orders.models import Order, OrderStatus
from orders.utils import change_date_format, OrderManager
from tasks.models import Task
from tasks.serializers import BaseTaskSerializer


class OrderSerializer(serializers.ModelSerializer):
    """
    Serializer for the Order model.

    This serializer is responsible for validating and transforming the Order model
    data into a format suitable for rendering in a view or saving in the database.
    It includes various fields derived from the model and some computed or linked
    fields. Validation for specific attributes is also included to enforce specific
    data requirements during the object lifecycle.

    Attributes:
        owner: Read-only field representing the owner's ID, sourced from the related user.
        accepted: Read-only field indicating whether the order is accepted.
        team: Read-only field representing the team's ID, sourced from the related team model.
        tasks: Field computed through a method to fetch serialized task data associated with the order.
        createdAt: Read-only field sourced from the model's creation timestamp.
        updatedAt: Read-only field sourced from the model's last updated timestamp.
        acceptedAt: Read-only field sourced from the model's acceptance timestamp.
        on_delete_time: Read-only field sourced from the model's deletion timestamp.
        action: Optional char field for additional action-related input from API clients.

    Meta:
        model: Specifies that the serializer's data corresponds to the Order model.
        fields: Lists all fields included in the serialized representation.
        read_only_fields: Denotes fields that are not modifiable by API clients.

    Methods:
        get_tasks: Retrieves and serializes tasks associated with an Order instance,
        returning them as a list of serialized data.

        validate: Ensures that all provided data meets the necessary validation
        criteria before saving or processing it further.

        _validate_name: Validates the name field to ensure it has a minimum length
        requirement of 5 characters.

        _validate_description: Validates the description field to ensure it meets
        minimum and maximum length requirements (100 and 3000 characters respectively).
        Skips validation if the field is not set.
    """
    owner = serializers.ReadOnlyField(source="owner.id")
    accepted = serializers.ReadOnlyField()
    team = serializers.ReadOnlyField(source="team.id", default=None)
    tasks = serializers.SerializerMethodField()
    createdAt = serializers.ReadOnlyField(source="created_at")
    updatedAt = serializers.ReadOnlyField(source="updated_at")
    acceptedAt = serializers.ReadOnlyField(source="accepted_at")
    on_delete_time = serializers.ReadOnlyField(source="on_delete_date")
    action = serializers.CharField(required=False)

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
            "on_delete_date",
            "action"
        ]
        read_only_fields = ["on_delete_date"]

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
    """
    Handles the serialization and creation of Order objects.

    This class extends the OrderSerializer and provides a customized create
    method to handle the creation of Order objects with additional context from
    the request, such as dynamically assigning the owner of the order based on
    the authenticated user.

    Methods:
        create(validated_data):
            Overrides the base serializer's create method to handle the creation
            of an Order instance using validated data and additional context.

    Attributes:
        Inherited attributes from OrderSerializer.
    """
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
    """
    Serializer for updating order details.

    This serializer is designed for updating fields in an order object while
    validating the input data. It allows partial updates for specific fields (name,
    description, deadline) and provides functionality to handle a delete action by
    scheduling the order for deletion. It is a specialized extension of the
    OrderSerializer class.
    Attributes:
        name (serializers.CharField): Optional field for updating the name of the
            order.
        description (serializers.CharField): Optional field for updating the
            description of the order.
        deadline (serializers.DateField): Optional field for updating the deadline
            of the order.
        action (serializers.CharField): Optional field specifying an action to be
            taken (e.g., "delete").
        ALLOWED_FIELDS (list[str]): List of fields allowed for updating.
    """
    name = serializers.CharField(required=False)
    description = serializers.CharField(required=False)
    deadline = serializers.DateField(required=False)
    action = serializers.CharField(required=False)

    ALLOWED_FIELDS = ["name", "description", "deadline"]

    def validate(self, attrs: dict) -> dict:
        invalid_fields = all(False if attrs.get(field) else True for field in self.ALLOWED_FIELDS)
        if invalid_fields:
            raise serializers.ValidationError(
                {"details": f"The method allows only the following fields: {', '.join(self.ALLOWED_FIELDS)}."}
            )
        super().validate(attrs)

        return attrs

    def update(self, instance: Order, validated_data):
        instance.name = validated_data.get("name", instance.name)
        instance.description = validated_data.get("description", instance.description)
        instance.deadline = validated_data.get("deadline", instance.deadline)
        instance.updated_at = timezone.now()
        if validated_data.get("action") == "delete":
            instance.on_delete_date = timezone.now() + timedelta(days=7)
            self.schedule_delete(instance)
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

    def schedule_delete(self, instance):

        logger = logging.getLogger(__name__)
        logger.info(f"Scheduling delete for Order ID {instance.id} at {instance.on_delete_date}")
        delete_time = instance.on_delete_date
        if delete_time < now():
            on_delete_time_item.apply_async(
                args=[instance.__class__.__name__, instance.pk, "orders"],
                eta=delete_time,
            )


class OrdersListSerializer(OrderSerializer):
    """
    Responsible for serializing a collection of order instances into a specific
    format for external representation.

    This serializer extends the OrderSerializer class and overrides its
    representation method to transform database models into a format suitable
    for API responses or other external uses. The serialization includes
    attributes such as ID, name, description, deadline, status, and a
    formatted creation date.
    """
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


class OrderManagementSerializer(serializers.ModelSerializer):
    """
    Serializer for managing Order objects.

    This serializer is designed to handle the validation, update, and
    representation of `Order` objects. It includes various fields and
    functions for integrating and performing operations on `Order` instances,
    such as updating order status, assigning teams, and returning
    representations in a specified format.

    Attributes:
        accepted: BooleanField indicating whether the order has been accepted.
        team: IntegerField representing the team's ID, mapped to the source `team.id`.
        status: CharField indicating the current status of the order.

    """
    accepted = serializers.BooleanField()
    team = serializers.IntegerField(source="team.id")
    status = serializers.CharField(required=True)

    class Meta:
        model = Order
        fields = ["accepted", "team", "status"]

    def validate(self, attrs):
        self._validate_status(attrs)

        if "team" in attrs:
            attrs["team_instance"] = OrderManager.get_team(attrs)

        status = attrs["status"]
        if status == "active" and attrs["team_instance"].status == "unavailable":
            raise serializers.ValidationError({"message": "This team is currently unavailable."})

        return attrs

    def update(self, instance: Order, validated_data):
        order_status = validated_data.get("status", instance.status)
        is_accepted = validated_data.get("accepted", False)
        team_instance = validated_data.get("team_instance", instance.team)

        if is_accepted and order_status == "active":
            accepted_order = OrderManager.accept_order(instance, team_instance, order_status)
            return accepted_order

        if order_status == "closed" and team_instance is not None:
            closed_order = OrderManager.close_order(instance, team_instance, order_status)
            return closed_order

        if instance.team != validated_data.get("team_instance", None):
            new_team = OrderManager.change_team(instance, team_instance)
            return new_team

        instance.team = team_instance
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

    def _validate_status(self, attrs: dict) -> None:
        status = attrs["status"]
        statuses = [OrderStatus.PENDING.value, OrderStatus.ACTIVE.value, OrderStatus.CLOSED.value]
        if status not in statuses:
            raise serializers.ValidationError({"status": f"Available statuses: {statuses}"})
