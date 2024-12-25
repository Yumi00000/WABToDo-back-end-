from allauth.account.views import ConfirmEmailView
from django.urls import path, re_path, include
from rest_framework import routers

from users import views
from users.authorization_url import GoogleLoginRedirectApi

router = routers.DefaultRouter()
# router.register(r"registration", views.RegistrationView, basename="register"),
router.register("dashboard", views.DashboardView, basename="dashboard")
router.register("teams", views.TeamsListView, basename="teams")
router.register("team/create", views.TeamsCreateView, basename="create_team")
router.register("team/edit", views.UpdateTeamView, basename="update_team")
router.register("team/info", views.TeamView, basename="team_info")
router.register("chat/create", views.CreateChatView, basename="create_chat")
router.register("chat/edit", views.EditChatView, basename="edit_chat")
router.register("chat/info", views.ChatView, basename="chat_info")
router.register("chat/list", views.ChatListView, basename="chat_list")
router.register("edit", views.EditUserView, basename="edit_user")
urlpatterns = router.urls
urlpatterns += [
    # path("login/", views.LoginView.as_view(), name="account_login"),
    path("google-oauth2/login-raw/", GoogleLoginRedirectApi.as_view(), name="login-raw"),
    path("google-oauth2/callback-raw/", views.GoogleLoginApi.as_view(), name="callback-raw"),
    re_path(
        "registration/account-confirm-email/(?P<key>[-:\w]+)/$",
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    path("registration/", include("dj_rest_auth.registration.urls")),
    path("", include("dj_rest_auth.urls")),
]
