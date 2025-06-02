from rest_framework.routers import DefaultRouter

from locations.api.views import AddressViewSet
from locations.api.views import DistrictViewSet
from locations.api.views import ProvinceViewSet
from locations.api.views import WardViewSet

router = DefaultRouter()
router.register("provinces", ProvinceViewSet, basename="provinces")
router.register("districts", DistrictViewSet, basename="districts")
router.register("wards", WardViewSet, basename="wards")
router.register("addresses", AddressViewSet, basename="addresses")

urlpatterns = [*router.urls]
