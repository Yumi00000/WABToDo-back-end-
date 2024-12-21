from datetime import datetime

from django.utils import timezone
from rest_framework import serializers

from orders.models import Order
from users.models import Team


def change_date_format(date: datetime) -> str | None:
    try:
        old_format = date
        valid_format = old_format.strftime("%Y-%m-%d")
        return valid_format

    except (ValueError, TypeError, AttributeError):
        return None


class OrderManager:
    @staticmethod
    def get_team(attrs: dict):
        try:
            team = attrs["team"]
            team_instance = Team.objects.get(id=team["id"])
            return team_instance
        except Team.DoesNotExist:
            raise serializers.ValidationError({"error": "Team with this Id does not exist."})

    @staticmethod
    def accept_order(order_instance, team_instance, order_status):
        order_instance.accepted = True
        order_instance.accepted_at = timezone.now()
        order_instance.team = team_instance
        order_instance.status = order_status
        team_instance.status = "unavailable"

        order_instance.save()
        team_instance.save()

        return order_instance

    @staticmethod
    def close_order(order_instance, team_instance, order_status):
        order_instance.status = order_status
        team_instance.status = "available"

        order_instance.save()
        team_instance.save()

        return order_instance

    @staticmethod
    def change_team(order_instance: Order, team_instance):
        old_team = Team.objects.get(id=order_instance.team_id)
        old_team.status = "available"
        order_instance.team = team_instance
        team_instance.status = "unavailable"

        old_team.save()
        order_instance.save()
        team_instance.save()

        return order_instance
