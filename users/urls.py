from django.urls import path
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
    path("login/", views.LoginView.as_view(), name="login"),
]
