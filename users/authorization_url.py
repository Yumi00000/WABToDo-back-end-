from django.views import View
from django.shortcuts import redirect

from core.service import (
    GoogleRawLoginFlowService,
)


class GoogleLoginRedirectApi(View):
    """Handle Google OAuth2 login redirection process.

    This class encapsulates the logic required to redirect users to Google's OAuth2
    authorization endpoint. It establishes a login flow using an external service,
    retrieves the authorization URL and state, and stores the state information into
    the user's session for later use. This process is part of the OAuth2 workflow
    to authenticate users via Google services.
    """
    def get(self, request, *args, **kwargs):
        google_login_flow = GoogleRawLoginFlowService()

        authorization_url, state = google_login_flow.get_authorization_url()

        print(f"Redirect to: {authorization_url}, State: {state}")  # Debugging Output

        request.session["google_oauth2_state"] = state

        return redirect(authorization_url)
