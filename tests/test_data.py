registration_credentials = {
    "username": "TheFirstUser",
    "firstName": "User",
    "lastName": "NotUser",
    "email": "theuseremail@gmail.com",
    "phoneNumber": "+48512345678",
    "password": "Weneedmorebananasthan1!",
    "password2": "Weneedmorebananasthan1!",
}

user_credentials = [
    {
        "id": 1,
        "username": "testuser1",
        "first_name": "John",
        "last_name": "Doe",
        "password": "testpassword",
        "is_active": True,
        "is_team_member": True,
        "is_admin": True,
        "is_staff": True,
    },
    {
        "id": 2,
        "username": "testuser2",
        "first_name": "Bob",
        "last_name": "Doe",
        "password": "testpassword",
        "is_active": True,
        "is_team_member": True,
    },
    {
        "id": 3,
        "username": "testuser3",
        "first_name": "Mark",
        "last_name": "Doe",
        "password": "testpassword",
        "is_active": True,
        "is_team_member": True,
    },
    {
        "id": 4,
        "username": "testuser4",
        "first_name": "Bob2",
        "last_name": "Doe",
        "password": "testpassword",
        "is_active": True,
    },
    {
        "id": 5,
        "username": "testuser5",
        "first_name": "Bob3",
        "last_name": "Doe",
        "password": "testpassword",
        "is_active": False,
    },
]

order_fake_creating_data = {
    "id": 1,
    "name": "TestOrderName",
    "description": (
        "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. "
        "Aenean commodo ligula eget dolor. Aenean massa.\n"
        "Cum sociis natoque penatibus et magnis dis parturient montes, nascetur ridiculus mus.\n"
        "Donec quam felis, ultricies nec, pellentesque eu, pretium quis, sem.\n"
        "Nulla consequat massa quis enim. Donec pede justo, fringilla vel, aliquet nec, vulputate."
    ),
    "deadline": "2025-12-31",
}
