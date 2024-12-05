from django.urls import path
from rest_framework import routers

from orders import views

router = routers.DefaultRouter()
router.register(r"create", views.CreateOrderView, basename="create-order"),
router.register(r"edit", views.EditOrderView, basename="edit-order"),

urlpatterns = router.urls
