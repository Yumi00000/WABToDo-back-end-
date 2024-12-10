from django.urls import path
from rest_framework import routers

from users import views

router = routers.DefaultRouter()
router.register(r"registration", views.RegistrationView, basename="register"),
router.register("dashboard", views.DashboardView, basename="dashboard")
router.register("teams", views.TeamsView, basename="teams")
router.register("create_team", views.TeamsCreateView, basename="create_team")

urlpatterns = router.urls
urlpatterns += [
    path("login/", views.LoginView.as_view(), name="login"),
]
