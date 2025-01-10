from typing import Dict

import jwt
from attrs import define


@define
class GoogleAccessTokens:
    """
    Represents a container for Google access tokens.

    The class is used to hold and manage Google authorization tokens including
    an ID token and an access token. It also provides functionality to decode
    the ID token to extract its payload.

    Attributes:
        id_token: Represents the ID token as a string.
        access_token: Represents the access token as a string.
    """
    id_token: str
    access_token: str

    def decode_id_token(self) -> Dict[str, str]:
        id_token = self.id_token
        decoded_token = jwt.decode(jwt=id_token, options={"verify_signature": False})
        return decoded_token
