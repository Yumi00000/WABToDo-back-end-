from allauth.account.views import ConfirmEmailView
from django.urls import path, re_path, include
from rest_framework import routers

from users import views

router = routers.DefaultRouter()
router.register(r"registration", views.RegistrationView, basename="register"),
router.register("dashboard", views.DashboardView, basename="dashboard")
router.register("teams", views.TeamsListView, basename="teams")
router.register("team/create", views.TeamsCreateView, basename="create_team")
router.register("team/edit", views.UpdateTeamView, basename="update_team")
router.register("team/info", views.TeamView, basename="team_info")
urlpatterns = router.urls
urlpatterns += [
    path("activate/<user_signed>", views.ActivateView.as_view(), name="activate"),
    path("login/", views.LoginView.as_view(), name="account_login"),
    re_path(
        "registration/account-confirm-email/(?P<key>[-:\w]+)/$",
        ConfirmEmailView.as_view(),
        name="account_confirm_email",
    ),
    path("", include("dj_rest_auth.urls")),
]
