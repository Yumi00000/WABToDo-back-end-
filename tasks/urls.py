from rest_framework import routers

from tasks import views

router = routers.DefaultRouter()
router.register(r"create", views.CreateTaskView, basename="create-task")

urlpatterns = router.urls
