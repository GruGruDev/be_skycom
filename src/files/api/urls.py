from rest_framework.routers import DefaultRouter

from files.api import views

router = DefaultRouter()
router.register("images", views.ImagesViewset, basename="images")

urlpatterns = [*router.urls]
