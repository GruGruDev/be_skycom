import django_filters.rest_framework as django_filters

from locations.models import Address
from locations.models import AddressType
from locations.models import Districts
from locations.models import Wards


class DistrictFilter(django_filters.FilterSet):
    province_id = django_filters.CharFilter(field_name="province_id", lookup_expr="exact")

    class Meta:
        model = Districts
        fields = [
            "province_id",
        ]


class WardFilter(django_filters.FilterSet):
    province_id = django_filters.CharFilter(field_name="province_id", lookup_expr="exact")
    district_id = django_filters.CharFilter(field_name="district_id", lookup_expr="exact")

    class Meta:
        model = Wards
        fields = [
            "province_id",
            "district_id",
        ]


class AddressFilter(django_filters.FilterSet):
    type = django_filters.MultipleChoiceFilter(choices=AddressType.choices(), field_name="type")

    class Meta:
        model = Address
        fields = ["type", "customer_id", "warehouse_id"]
