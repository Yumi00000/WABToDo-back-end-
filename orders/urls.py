from django.urls import path
from rest_framework import routers

from orders import views

router = routers.DefaultRouter()
router.register(r"create", views.CreateOrderView, basename="create-order"),

urlpatterns = router.urls
