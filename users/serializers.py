import phonenumbers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django_celery_beat.utils import now
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from orders.models import Order
from orders.serializers import OrderSerializer
from orders.utils import change_date_format
from users.utils import PasswordValidator
from users.models import CustomUser, Team, Chat, Participant


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


class EditUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    firstName = serializers.CharField(
        source="first_name",
    )
    lastName = serializers.CharField(
        source="last_name",
    )
    phoneNumber = serializers.CharField(
        source="phone_number",
    )

    class Meta:
        model = CustomUser
        fields = ["username", "email", "firstName", "lastName", "phoneNumber"]

    def validate(self, data: dict) -> dict:
        username = data.get("username")
        email = data.get("email")
        phoneNumber = data.get("phone_number")
        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError("Username already exists.")

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("Email already exists.")

        if phoneNumber:
            data["phoneNumber"] = self.validate_phone_number(phoneNumber)

        return data

    @staticmethod
    def validate_phone_number(phone_number: str) -> str | None:
        try:
            parsed = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_valid_number(parsed):
                raise serializers.ValidationError("Invalid phone number.")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise serializers.ValidationError("Invalid phone number format.")

    def update(self, instance, validated_data):
        instance.username = validated_data.get("username", instance.username)
        instance.email = validated_data.get("email", instance.email)
        instance.first_name = validated_data.get("first_name", instance.first_name)
        instance.last_name = validated_data.get("last_name", instance.last_name)
        instance.phone_number = validated_data.get("phone_number", instance.phone_number)
        instance.save()
        return instance


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


class ChatSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    is_group = serializers.BooleanField(default=False)
    chat_id = serializers.IntegerField(required=False)
    participants = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["name", "chat_id", "is_group", "participants"]
        read_only_fields = ["created_at"]

    def get_participants(self, obj):
        participants = obj.participants.all()  # Access participants through the related Manager
        # Serialize the related objects into a list of dictionaries
        return [{"id": participant.user.id, "username": participant.user.username} for participant in participants]


class CreateChatSerializer(ChatSerializer):
    def validate(self, attrs: dict) -> dict:
        if attrs.get("is_group") == False and len(attrs.get("participants", [])) > 1:
            raise serializers.ValidationError("You can't add more than one participant to your chat.")
        return attrs

    def create(self, validated_data):
        participants = validated_data.pop("participants")
        participants.append(self.context["request"].user.id)  # Add the requesting user as a participant

        # Create the chat
        chat = Chat.objects.create(**validated_data)
        chat.save()

        # Create participants
        participant_objects = [Participant(chat=chat, user_id=participant_id) for participant_id in participants]
        Participant.objects.bulk_create(participant_objects)  # Efficiently create all participants

        owner = Participant.objects.get(chat=chat, user=self.context["request"].user)
        owner.role = "admin"
        owner.save()
        # Prepare response
        response = {
            "name": chat.name,
            "chat_id": chat.id,
            "is_group": chat.is_group,
            "participants": list(
                chat.participants.values("id", "user_id")  # Assuming `participants` is a related name
            ),
        }

        return response


class UpdateChatSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False)
    is_group = serializers.BooleanField(default=False)
    chat_id = serializers.IntegerField(required=False)
    participants = serializers.JSONField(required=False)

    class Meta:
        model = Chat
        fields = ["name", "is_group", "chat_id", "participants"]

    def update(self, instance, validated_data):
        request = self.context["request"]
        action = request.data.get("action")

        if action == "update":
            instance.name = validated_data.get("name", instance.name)
            if instance.is_group:
                new_participants = validated_data.get("participants", [])
                if new_participants:
                    current_participants = Participant.objects.filter(chat=instance)
                    current_participant_ids = {participant.user.id for participant in current_participants}

                    new_participant_ids = set(new_participants)
                    participants_to_add = new_participant_ids - current_participant_ids
                    participants_to_remove = current_participant_ids - new_participant_ids

                    if participants_to_add:
                        users_to_add = CustomUser.objects.filter(id__in=participants_to_add)
                        Participant.objects.bulk_create(
                            [Participant(chat=instance, user=user) for user in users_to_add]
                        )

                    if participants_to_remove:
                        Participant.objects.filter(chat=instance, user_id__in=participants_to_remove).delete()

            instance.save()

            return {
                "id": instance.id,
                "name": instance.name,
                "is_group": instance.is_group,
                "participants": list(Participant.objects.filter(chat=instance).values("user__id", "user__username")),
            }

        elif action == "delete":
            instance.delete()
            return {"detail": "Chat successfully deleted."}

        # If action is invalid
        raise serializers.ValidationError({"detail": "Invalid action provided."})


class InputSerializer(serializers.Serializer):
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
