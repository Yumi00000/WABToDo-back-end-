import phonenumbers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django_celery_beat.utils import now
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from orders.models import Order
from orders.serializers import OrderSerializer
from orders.utils import change_date_format
from users.models import CustomUser, Team
from users.utils import PasswordValidator


class RegistrationSerializer(serializers.ModelSerializer, PasswordValidator):
    username = serializers.CharField(required=True, trim_whitespace=False)
    firstName = serializers.CharField(
        source="first_name",
        required=True,
    )
    lastName = serializers.CharField(source="last_name", required=True)
    email = serializers.EmailField(required=True, validators=[UniqueValidator(queryset=CustomUser.objects.all())])
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password], trim_whitespace=False
    )
    password2 = serializers.CharField(
        write_only=True, required=True, validators=[validate_password], trim_whitespace=False
    )
    isTeamMember = serializers.BooleanField(source="is_team_member", required=False, default=False)
    isAdmin = serializers.BooleanField(source="is_admin", required=False, default=False)
    isStaff = serializers.BooleanField(source="is_staff", required=False, default=False)
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
            "isStaff",
        ]

    def validate(self, attrs: dict):

        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password": "Passwords fields didn't match."})

        if not self.password_validator(attrs):
            raise serializers.ValidationError(
                {
                    "password": "Not a reliable password.",
                    "password scheme": {
                        "capital_letter": "At least once capital letter is required.",
                        "numeric": "At least once numeric is required.",
                        "cannot_be_used": "Username, first or last name, email.",
                        "spaces": "Password must not contain spaces.",
                    },
                }
            )

        if attrs.get("phone_number"):
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
            is_staff=validated_data.get("is_staff", False),
            is_active=False,
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
        user.last_login = now()
        user.save()

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
    leader = serializers.CharField(source="leader.username", read_only=False)
    status = serializers.CharField(read_only=False)
    list_of_members = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["leader", "status", "list_of_members"]

    def get_list_of_members(self, obj: Team):
        members = [member.username for member in obj.list_of_members.all()]
        return members


class CreateTeamSerializer(serializers.ModelSerializer):
    list_of_members = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Team
        fields = ["list_of_members", "status"]

    def create(self, validated_data):
        leader = self.context["request"].user
        list_of_members = validated_data.pop("list_of_members", [])

        # Create the team
        team = Team.objects.create(leader=leader, status=validated_data.get("status", "available"))

        # Set members
        members = CustomUser.objects.filter(id__in=list_of_members)
        team.list_of_members.set(members)
        team.list_of_members.add(leader)  # Add leader
        CustomUser.objects.filter(id__in=list_of_members).update(is_team_member=True)

        # Save and refresh team object
        team.save()
        team.refresh_from_db()  # Ensure related fields are loaded

        # Serialize team and return response
        return TeamSerializer(team).data


class UpdateTeamSerializer(TeamSerializer):
    leader_id = serializers.IntegerField()
    list_of_members = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=True)
    status = serializers.CharField()

    class Meta:
        model = Team
        fields = ["leader_id", "status", "list_of_members"]

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("leader_id"):
            raise serializers.ValidationError("Team leader id is required.")
        if not attrs.get("list_of_members"):
            raise serializers.ValidationError("Team members list is required.")

        if attrs["leader_id"] not in attrs["list_of_members"]:
            raise serializers.ValidationError({"leader_id": f"You cannot remove this member: {attrs['leader_id']}"})
        return attrs

    def update(self, instance, validated_data):
        current_members_ids = (
            set(member.id for member in instance.list_of_members.all())
            if instance.list_of_members.filter(id=self.context["request"].user.id).exists()
            else set()
        )

        instance.leader = CustomUser.objects.get(id=validated_data.get("leader_id", instance.leader.id))
        instance.status = validated_data.get("status", instance.status)
        new_members_ids = set(validated_data.pop("list_of_members", []))

        members_to_add = new_members_ids - current_members_ids
        members_to_remove = current_members_ids - new_members_ids

        if members_to_add or members_to_remove:
            updated_members = CustomUser.objects.filter(id__in=new_members_ids)
            instance.list_of_members.set(updated_members)
            CustomUser.objects.filter(id__in=members_to_add).update(is_team_member=True)
            CustomUser.objects.filter(id__in=members_to_remove).update(is_team_member=False)

        instance.save()

        # Serialize the updated instance before returning
        return TeamSerializer(instance).data
