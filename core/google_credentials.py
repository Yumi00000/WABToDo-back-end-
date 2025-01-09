from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from attrs import define


@define
class GoogleRawLoginCredentials:
    """
    Represents the raw login credentials required for Google services.

    This class encapsulates the essential credentials such as client ID,
    client secret, and project ID which are necessary for authenticating
    and interacting with Google's APIs. It serves as a container for
    these values, making it easier to manage and access the credentials
    in a structured manner.

    Attributes:
        client_id: A unique identifier for the client application
                   provided by Google.
        client_secret: A secret string used to authenticate the client
                       application.
        project_id: The identifier of the Google Cloud project
                    associated with the credentials.
    """
    client_id: str
    client_secret: str
    project_id: str


def google_raw_login_get_credentials() -> GoogleRawLoginCredentials:
    """
        Retrieves the Google OAuth2 credentials required for the raw login functionality.

        This function fetches the client ID, client secret, and project ID from the application
        settings and validates their presence. If any of these are missing, it raises an
        ImproperlyConfigured error. The validated credentials are then encapsulated in a
        GoogleRawLoginCredentials object and returned.

        Raises:
            ImproperlyConfigured: If `GOOGLE_OAUTH2_CLIENT_ID`, `GOOGLE_OAUTH2_CLIENT_SECRET`,
            or `GOOGLE_OAUTH2_PROJECT_ID` is missing in the application environment.

        Returns:
            GoogleRawLoginCredentials: An object that contains the Google OAuth2 credentials
            including the client ID, client secret, and project ID.
    """
    client_id = settings.GOOGLE_OAUTH2_CLIENT_ID
    client_secret = settings.GOOGLE_OAUTH2_CLIENT_SECRET
    project_id = settings.GOOGLE_OAUTH2_PROJECT_ID

    if not client_id:
        raise ImproperlyConfigured("GOOGLE_OAUTH2_CLIENT_ID missing in env.")

    if not client_secret:
        raise ImproperlyConfigured("GOOGLE_OAUTH2_CLIENT_SECRET missing in env.")

    if not project_id:
        raise ImproperlyConfigured("GOOGLE_OAUTH2_PROJECT_ID missing in env.")

    credentials = GoogleRawLoginCredentials(client_id=client_id, client_secret=client_secret, project_id=project_id)

    return credentials
