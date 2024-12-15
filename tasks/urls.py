from rest_framework import routers

from tasks import views

router = routers.DefaultRouter()
# router.register(r"", views.GetTeamTasksView, basename="tasks")
router.register(r"create", views.CreateTaskView, basename="create-task")
router.register(r"edit", views.UpdateTaskView, basename="edit-task")

urlpatterns = router.urls
