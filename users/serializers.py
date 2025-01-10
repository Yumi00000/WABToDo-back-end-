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
    """
    Represents a serializer for user registration handling.

    This serializer defines the fields and validation logic required for a
    user registration process. It ensures that the provided user information
    complies with the necessary requirements, including unique constraints
    and password validation criteria. Additionally, the serializer handles
    password confirmation to avoid mismatched inputs. The creation of a new
    user instance is managed through the `create` method.

    Attributes:
        username: A required CharField for the user's username.
        firstName: A required CharField sourced from the user's first_name.
        lastName: A required CharField sourced from the user's last_name.
        email: A required EmailField ensuring a unique email for the user in the database.
        password: A required CharField, write-only, for setting the user's password.
        password2: A required CharField, write-only, for confirming the user's password.
        isTeamMember: A BooleanField sourced from is_team_member, optional, defaults to False.
        isAdmin: A BooleanField sourced from is_admin, optional, defaults to False.
        isStaff: A BooleanField sourced from is_staff, optional, defaults to False.
        phoneNumber: An optional CharField sourced from phone_number with unique constraints.

    Methods:
        validate(attrs: dict):
            Validates the provided attributes. Ensures passwords match, checks
            password security using the password validator, and validates the phone number
            if provided. Returns the validated attributes.

        create(validated_data):
            Creates and returns a `CustomUser` object with the validated data.
            Password is hashed before saving the user.

        validate_phone_number(phone_number: str) -> str | None:
            Validates and formats the provided phone number using the phonenumbers library.
            Raises a validation error if the phone number is invalid.
    """
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
    """
    Serializes and validates login data for user authentication.

    This class is used to validate and serialize login credentials, ensuring that
    the required fields (username, password, and user_agent) are provided. It also
    authenticates the user using the provided credentials and attaches the user
    object to the validated data if authentication is successful.

    Attributes:
        username: CharField that captures the username provided by the user.
        password: CharField that captures the password provided, write-only.
        user_agent: CharField that captures the user agent string.

    Methods:
        validate: Validates login credentials and authenticates the user.

    """
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
    """
    Serializer class for editing user information.

    This class is a serializer that facilitates handling user update operations by
    validating and serializing the fields required for updating an existing user in
    the system. The serializer is designed to include validation logic to ensure that
    usernames, emails, and phone numbers are appropriately formatted and unique, while
    providing the capability to map fields for customizing their representation.

    Attributes:
        username (serializers.CharField): The username of the user.
        email (serializers.EmailField): The email address of the user.
        firstName (serializers.CharField): The first name of the user, mapped from the
            "first_name" field in the model.
        lastName (serializers.CharField): The last name of the user, mapped from the
            "last_name" field in the model.
        phoneNumber (serializers.CharField): The phone number of the user, mapped from
            the "phone_number" field in the model.

    Methods:
        validate:
            Validates the serialized user data to ensure that all fields meet the
            required conditions including uniqueness of username and email as well as
            validity of the phone number format.

        validate_phone_number:
            Static method for validating and formatting the provided phone number as per
            the international E.164 format.

        update:
            Updates the user instance with validated data, safely handling optional
            fields and persisting changes to the database.
    """
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
    """
    Represents a serializer for Dashboard-specific order data.

    This class is an extension of the OrderSerializer and provides custom
    representation for orders for Dashboard purposes. It modifies the
    serialization by formatting date fields and extracting specific data
    points to better suit the needs of the Dashboard display.

    Attributes
    ----------
    None

    Methods
    -------
    to_representation(instance: Order) -> dict
        Customizes the serialization of an Order instance for Dashboard representation.
    """
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
    """
    This serializer is responsible for handling serialization and deserialization
    of Team model instances into JSON and vice versa. It defines mappings for
    attributes related to a team, including the team leader, team status, and
    a generated list of team members.

    The serializer is designed to expose specific fields of the Team model while
    allowing customization for certain attributes like leader and list_of_members.
    It enables controlled access and mutation of these values during the API
    interaction.

    Attributes:
        leader: A character field that maps to the username of the team's leader.
        status: A character field that represents the current status of the team.
        list_of_members: A field created through a serializer method that generates
            a list of usernames of all the members in the team.

    Methods:
        get_list_of_members: A method to generate a list of team members' usernames
            dynamically for the given Team instance.

    Meta:
        Specifies the associated model as Team and declares the serializer fields
        to include id, leader, list_of_members, and status.

    """
    leader = serializers.CharField(source="leader.username", read_only=False)
    status = serializers.CharField(read_only=False)
    list_of_members = serializers.SerializerMethodField()

    class Meta:
        model = Team
        fields = ["id", "leader", "list_of_members", "status"]

    def get_list_of_members(self, obj: Team):
        members = [member.username for member in obj.list_of_members.all()]
        return members


class CreateTeamSerializer(serializers.ModelSerializer):
    """
    A serializer for creating and managing a Team object.

    The serializer is responsible for handling the validation and creation of a team,
    along with its members. It ensures a leader is assigned to the team and manages
    the association of members, including updating their status as team members.

    Attributes
    ----------
    leader : int, optional
        The ID of the team leader. This is not a required field because the leader is
        automatically set to the current logged-in user.
    list_of_members : list of int
        A list of user IDs to be added as members to the team. This is a write-only field
        and will not be returned in serialized responses.

    Meta
    ----
    model : Team
        Specifies that this serializer is associated with the Team model.
    fields : list of str
        Specifies the fields to be serialized: `id`, `leader`, `list_of_members`, and `status`.

    Methods
    -------
    create(validated_data)
        Creates and returns a new Team object using the validated data. Assigns the currently
        logged-in user as the team leader, associates the provided members' IDs, updates
        member statuses, and ensures the team object is refreshed before returning serialized data.
    """
    leader = serializers.IntegerField(required=False)
    list_of_members = serializers.ListField(child=serializers.IntegerField(), write_only=True)

    class Meta:
        model = Team
        fields = ["id", "leader", "list_of_members", "status"]

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
    """
    Handles the serialization and validation of data for updating a team.

    This class extends the `TeamSerializer` to provide additional fields and logic
    specific to updating team information, such as updating the team leader, team
    members, and status. It ensures data integrity by validating the presence of
    a leader and members, and verifies that the leader remains a member of the team.
    It also manages updates to the membership status of users when team members
    are added or removed.

    Attributes
    ----------
    leader_id : serializers.IntegerField
        The ID of the team leader.
    list_of_members : serializers.ListField
        List of member IDs belonging to the team. Write-only and required for updating.
    status : serializers.CharField
        Status of the team as a string. Allows updates to the team's status.

    Meta
    ----
    model : Team
        Links the serializer to the `Team` model.
    fields : list[str]
        Specifies the fields included in the serializer: `leader_id`, `status`, and
        `list_of_members`.

    Methods
    -------
    validate(attrs: dict) -> dict
        Validates the provided attributes for updating a team. Ensures mandatory
        fields are present and that the leader remains in the member list.
    update(instance, validated_data)
        Updates an existing team instance with validated data. Handles changes to
        the leader, status, and member list. Updates user membership statuses
        accordingly.
    """
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
    """
    Serializer for the Chat model.

    This serializer is responsible for serializing and deserializing the Chat model
    instances into JSON format, as well as performing validation and providing
    custom fields. It defines the structure for interacting with Chat instances via
    API endpoints.

    Attributes:
        name (serializers.CharField): The name of the chat. This field is required.
        is_group (serializers.BooleanField): Indicates whether the chat is a group
            chat. Defaults to False.
        chat_id (serializers.IntegerField): The ID of the chat. This field is
            optional.
        participants (serializers.SerializerMethodField): A custom field that
            serializes the participants of the chat into a list of dictionaries,
            including user IDs and usernames.

    Methods:
        get_participants(obj):
            Retrieves and serializes the participants related to the given Chat
            instance. Accesses participant objects and converts them into a list
            of dictionaries with user details for API consumption.

    Meta:
        model: Refers to the Chat model being serialized.
        fields: Specifies the set of fields to include in the serialization. This
            includes "name", "chat_id", "is_group", and "participants".
        read_only_fields: Identifies fields that are read-only during
            serialization. The "created_at" field is marked as read-only to
            safeguard its integrity and avoid modification during updates.
    """
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
    """
    Serializer for creating a chat.

    This serializer provides validation and creation logic for chat objects. It ensures
    that the constraints for group and non-group chats are respected. Non-group chats
    cannot have more than one participant apart from the creator. The serializer also
    handles the creation of participants for the chat and designates the creator as the
    admin of the chat. Finally, it prepares a structured response with the created chat's
    details.

    Methods:
        validate: Ensures valid data for creating a chat, particularly ensuring that
        non-group chats cannot have more than one participant.
        create: Handles the creation of the Chat object, its related Participants, and
        prepares the response for the created chat.
    """
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
    """
    Serializer class for updating chat instances.

    This serializer provides functionality to update the name and participant list of
    a chat instance. It supports handling group chats by managing participants to be added
    or removed. Additionally, it allows the chat instance to be deleted via a specific action.

    Attributes:
        name: The name of the chat. It's optional to provide.
        is_group: Boolean flag indicating whether the chat is a group chat.
        chat_id: The unique identifier of the chat instance. It's optional to provide.
        participants: A list of participants in JSON format. It's optional to provide.

    Methods:
        update: Handles updating chat instance attributes based on input data.
    """
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
    """
    Serializer for handling input data validation and transformation.

    This class is used for serializing and deserializing input data, often
    received in a request. It ensures that the required fields are properly
    formatted and validated as defined. Typically utilized in Django REST
    Framework-based APIs to manage user input.

    Attributes:
    code (str): A field that represents some input code, not mandatory.
    error (str): A field that represents error messages, not mandatory.
    state (str): A field that represents the state of an object, not
                 mandatory.
    """
    code = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
