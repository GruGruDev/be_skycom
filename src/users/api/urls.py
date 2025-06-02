from django.urls import path
from rest_framework.routers import DefaultRouter

from users.api.views import ProfileAPIView
from users.api.views import UserActionLogViewSet
from users.api.views import UserDepartmentViewSet
from users.api.views import UserHistoryListAPIView
from users.api.views import UserRoleViewSet
from users.api.views import UserViewSet

router = DefaultRouter()
router.register("role", UserRoleViewSet, basename="user-role")
router.register("department", UserDepartmentViewSet, basename="user-department")
# router.register("group", UserGroupViewSet, basename="user-group")
router.register("action-log", UserActionLogViewSet, basename="user-action-log")
router.register("", UserViewSet, basename="user")

urlpatterns = [
    path("me/", ProfileAPIView.as_view(), name="user_profile"),
    path("<pk>/history/", UserHistoryListAPIView.as_view(), name="history-users"),
] + router.urls
