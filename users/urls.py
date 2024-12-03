from django.urls import path
from rest_framework import routers

from users import views

router = routers.DefaultRouter()
router.register(r"registration", views.RegistrationView, basename="register"),

urlpatterns = router.urls
