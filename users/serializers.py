import phonenumbers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from orders.models import Order
from orders.serializers import OrderSerializer
from orders.utils import change_date_format
from users.models import CustomUser, Team


class RegistrationSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source="first_name", required=True)
    lastName = serializers.CharField(source="last_name", required=True)
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    isTeamMember = serializers.BooleanField(source="is_team_member", required=False, default=False)
    isAdmin = serializers.BooleanField(source="is_admin", required=False, default=False)
    phoneNumber = serializers.CharField(
        source="phone_number", required=False, validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )

    class Meta:
        model = CustomUser
        fields = [
            "username",
            "firstName",
            "lastName",
            "password",
            "password2",
            "email",
            "phoneNumber",
            "isTeamMember",
            "isAdmin",
        ]
        extra_kwargs = {
            "firstName": {"required": True},
            "lastName": {"required": True},
        }

    def validate(self, attrs: dict):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords fields didn't match."})

        if "phoneNumber" in attrs.keys():
            attrs["phone_number"] = self.validate_phone_number(attrs["phone_number"])

        return attrs

    def create(self, validated_data):
        user = CustomUser.objects.create(
            username=validated_data["username"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            email=validated_data["email"],
            phone_number=validated_data.get("phone_number", None),
            is_team_member=validated_data.get("is_team_member", False),
            is_admin=validated_data.get("is_admin", False),
        )
        user.set_password(validated_data["password"])
        user.save()

        return user

    @staticmethod
    def validate_phone_number(phone_number: str) -> str | None:
        try:
            parsed = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError({"phone_number": "Invalid phone number."})

            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

        except phonenumbers.NumberParseException:
            raise serializers.ValidationError({"phone_number": "Invalid phone number format."})


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    user_agent = serializers.CharField(required=True)

    def validate(self, data: dict) -> dict | None:
        username = data["username"]
        password = data["password"]

        if not username or not password:
            raise serializers.ValidationError("To login you must provide both username and password.")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        data["user"] = user
        return data


class DashboardSerializer(OrderSerializer):

    def to_representation(self, instance: Order) -> dict:
        created_at = change_date_format(instance.created_at)

        return {
            "id": instance.id,
            "name": instance.name,
            "owner": instance.owner.first_name,
            "createdAt": created_at,
            "accepted": instance.accepted,
            "status": instance.status,
        }


class TeamSerializer(serializers.ModelSerializer):
    leader = serializers.CharField(source="leader.username", read_only=True)
    status = serializers.CharField(source="status.name", read_only=True)
    list_of_members = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ['leader', 'status', 'list_of_members']

    def get_list_of_members(self, obj: Team):
        return [member.username for member in obj.list_of_members.all()]
