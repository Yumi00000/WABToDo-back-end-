from django.views import View
from django.shortcuts import redirect

from core.service import (
    GoogleRawLoginFlowService,
)


class GoogleLoginRedirectApi(View):
    def get(self, request, *args, **kwargs):
        google_login_flow = GoogleRawLoginFlowService()

        authorization_url, state = google_login_flow.get_authorization_url()

        print(f"Redirect to: {authorization_url}, State: {state}")  # Debugging Output

        request.session["google_oauth2_state"] = state

        return redirect(authorization_url)
