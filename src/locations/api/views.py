import django_filters.rest_framework as django_filters
from rest_framework import filters
from rest_framework.permissions import IsAuthenticated

from core.views import CustomModelViewSet
from locations.api.filters import AddressFilter
from locations.api.filters import DistrictFilter
from locations.api.filters import WardFilter
from locations.api.serializers import AddressCreateSerializer
from locations.api.serializers import AddressSerializer
from locations.api.serializers import AddressUpdateSerializer
from locations.api.serializers import DistrictSerializer
from locations.api.serializers import ProvinceSerializer
from locations.api.serializers import WardSerializer
from locations.models import Address
from locations.models import Districts
from locations.models import Provinces
from locations.models import Wards


class ProvinceViewSet(CustomModelViewSet):
    serializer_class = ProvinceSerializer
    permission_classes = [IsAuthenticated]
    queryset = Provinces.objects.all()

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    search_fields = ["code", "slug", "name", "type"]
    ordering_fields = "code"


class DistrictViewSet(CustomModelViewSet):
    serializer_class = DistrictSerializer
    permission_classes = [IsAuthenticated]
    queryset = Districts.objects.prefetch_related("province").all()

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    filterset_class = DistrictFilter
    search_fields = ["code", "slug", "name", "type"]
    ordering_fields = "code"


class WardViewSet(CustomModelViewSet):
    serializer_class = WardSerializer
    permission_classes = [IsAuthenticated]
    queryset = Wards.objects.prefetch_related("province", "district").all()

    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    ]
    filterset_class = WardFilter
    search_fields = ["code", "slug", "name", "type"]
    ordering_fields = "code"


class AddressViewSet(CustomModelViewSet):
    http_method_names = ("get", "post", "patch", "delete")
    permission_classes = (IsAuthenticated,)
    serializer_classes = {"create": AddressCreateSerializer, "partial_update": AddressUpdateSerializer}
    serializer_class = AddressSerializer
    queryset = Address.objects.all()
    filter_backends = (
        filters.SearchFilter,
        filters.OrderingFilter,
        django_filters.DjangoFilterBackend,
    )
    search_fields = ("address",)
    filterset_class = AddressFilter
    ordering_fields = "__all__"

    def get_serializer_class(self):
        return self.serializer_classes.get(self.action, self.serializer_class)
